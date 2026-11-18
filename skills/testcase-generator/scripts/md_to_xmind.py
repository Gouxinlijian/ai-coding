#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把测试用例 Markdown 转换为 XMind 文件。

用法：
    python md_to_xmind.py <input.md> <output.xmind> [标题] [--tables expand|skip]

约定：标题与列表项转换为导图节点，层级由标题级别和列表缩进决定；
表格默认展开为节点（首列作用例标题，其余列作为子节点），表头行与分隔行不生成节点；
代码块内容不进入导图。
"""

import argparse
import json
import re
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from uuid import uuid4

HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
LIST_PATTERN = re.compile(r"^([ \t]*)[-*+]\s+(.*)$")
CHECKBOX_PATTERN = re.compile(r"^\[([ xX])\]\s*")
INLINE_PATTERN = re.compile(r"`([^`]*)`|\*\*(.+?)\*\*|__(.+?)__")
LINK_PATTERN = re.compile(r"\[([^\]]+)\]\([^)]*\)")
DIVIDER_PATTERN = re.compile(r"^[-=*_|:\s]+$")
TABLE_DIVIDER_CELL = re.compile(r"^:?-{3,}:?$")

LIST_BASE_LEVEL = 7


def clean_text(text):
    """去掉行内链接、反引号、粗体标记和 HTML 换行。"""
    text = text.replace("<br>", "；").replace("<br/>", "；").replace("<br />", "；")
    text = LINK_PATTERN.sub(r"\1", text)
    text = INLINE_PATTERN.sub(lambda match: match.group(1) or match.group(2) or match.group(3), text)
    return text.strip()


def make_node(title, level):
    return {"title": title, "level": level, "children": []}


def split_table_row(line):
    text = line.strip()
    if text.startswith("|"):
        text = text[1:]
    if text.endswith("|"):
        text = text[:-1]
    return [cell.strip() for cell in text.split("|")]


def is_table_row(line):
    return line.strip().startswith("|")


def is_table_divider(line):
    if not is_table_row(line):
        return False
    cells = [cell for cell in split_table_row(line) if cell]
    return bool(cells) and all(TABLE_DIVIDER_CELL.match(cell) for cell in cells)


def table_headers(lines, index):
    """返回 (表头列表, 数据起始下标)；非表头表格返回 (None, index)。"""
    if not is_table_row(lines[index]):
        return None, index
    if index + 1 < len(lines) and is_table_divider(lines[index + 1]):
        headers = [clean_text(cell) for cell in split_table_row(lines[index])]
        return headers, index + 2
    return None, index


def add_table_row(root, stack, headers, line):
    cells = [clean_text(cell) for cell in split_table_row(line)]
    if not any(cells):
        return

    title_index = 0
    if not cells[0]:
        title_index = next((i for i, cell in enumerate(cells) if cell), 0)
    title = cells[title_index]
    if not title:
        return

    level = (stack[-1][0] if stack else 0) + 1
    node = make_node(title, level)
    for index, value in enumerate(cells):
        if index == title_index or not value:
            continue
        column = headers[index] if headers and index < len(headers) else ""
        if column and not value.startswith(column):
            child_title = "{}：{}".format(column, value)
        else:
            child_title = value
        node["children"].append(make_node(child_title, level + 1))

    parent = stack[-1][1] if stack else root
    parent["children"].append(node)


def parse_markdown(content, title=None, tables="expand"):
    """按标题级别、列表缩进与表格行构建节点树。"""
    root = make_node(title or "", 0)
    stack = []
    in_fence = False
    lines = [line.rstrip() for line in content.splitlines()]
    index = 0

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()

        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            index += 1
            continue
        if in_fence or not stripped:
            index += 1
            continue

        if is_table_row(line):
            if tables == "skip" or is_table_divider(line):
                index += 1
                continue
            headers, data_start = table_headers(lines, index)
            if headers is not None:
                index = data_start
                while index < len(lines) and is_table_row(lines[index]) and not is_table_divider(lines[index]):
                    add_table_row(root, stack, headers, lines[index])
                    index += 1
                continue
            add_table_row(root, stack, None, line)
            index += 1
            continue

        if DIVIDER_PATTERN.fullmatch(stripped):
            index += 1
            continue

        heading = HEADING_PATTERN.match(stripped)
        if heading:
            level = len(heading.group(1))
            node_title = clean_text(heading.group(2))
            if not node_title:
                index += 1
                continue
            node = make_node(node_title, level)
        else:
            item = LIST_PATTERN.match(line)
            if not item:
                index += 1
                continue
            indent = item.group(1).replace("\t", "    ")
            text = item.group(2).strip()
            checked = CHECKBOX_PATTERN.match(text)
            if checked:
                mark = "☑" if checked.group(1).lower() == "x" else "☐"
                text = CHECKBOX_PATTERN.sub("", text).strip()
                text = "{} {}".format(mark, text)
            node_title = clean_text(text)
            if not node_title:
                index += 1
                continue
            node = make_node(node_title, LIST_BASE_LEVEL + len(indent) // 2)

        while stack and stack[-1][0] >= node["level"]:
            stack.pop()
        parent = stack[-1][1] if stack else root
        parent["children"].append(node)
        stack.append((node["level"], node))
        index += 1

    return promote_single_top(root, title)


def promote_single_top(root, title=None):
    """只有一个一级标题时，用它作为根节点标题。"""
    children = root["children"]
    if len(children) == 1 and children[0]["level"] == 1:
        root_title = title or children[0]["title"]
        promoted = make_node(root_title, 0)
        promoted["children"] = children[0]["children"]
        return promoted
    if not root["title"]:
        root["title"] = "测试用例"
    return root


def build_topic(node):
    topic = {"id": uuid4().hex, "class": "topic", "title": node["title"]}
    if node["children"]:
        topic["children"] = {"attached": [build_topic(child) for child in node["children"]]}
    return topic


def build_content(root, sheet_title):
    return [
        {
            "id": uuid4().hex,
            "class": "sheet",
            "title": sheet_title,
            "rootTopic": build_topic(root),
        }
    ]


def write_xmind(target, root, sheet_title):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    manifest = {"file-entries": {"content.json": {}, "metadata.json": {}}}
    metadata = {
        "creator": {"name": "testcase-generator", "version": "1.0"},
        "created": now,
        "modified": now,
    }

    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(str(target), "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        archive.writestr("content.json", json.dumps(build_content(root, sheet_title), ensure_ascii=False, indent=2))
        archive.writestr("metadata.json", json.dumps(metadata, ensure_ascii=False, indent=2))


def count_nodes(node):
    total = 1
    for child in node["children"]:
        total += count_nodes(child)
    return total


def main(argv=None):
    parser = argparse.ArgumentParser(description="将测试用例 Markdown 转换为 XMind 文件")
    parser.add_argument("input", help="输入 Markdown 文件路径")
    parser.add_argument("output", help="输出 .xmind 文件路径")
    parser.add_argument("title", nargs="?", default=None, help="导图根标题，默认取 Markdown 首个一级标题")
    parser.add_argument(
        "--tables",
        choices=["expand", "skip"],
        default="expand",
        help="表格处理方式：expand 展开为节点（默认），skip 跳过表格",
    )
    args = parser.parse_args(argv)

    source = Path(args.input)
    if not source.is_file():
        print("错误：找不到输入文件 {}".format(source), file=sys.stderr)
        return 2

    content = source.read_text(encoding="utf-8")
    root = parse_markdown(content, args.title, args.tables)
    if not root["children"]:
        print("错误：Markdown 中没有可转换为节点的标题、列表项或表格行", file=sys.stderr)
        return 3

    target = Path(args.output)
    if target.suffix.lower() != ".xmind":
        print("警告：输出文件扩展名不是 .xmind，仍按 XMind 格式写入", file=sys.stderr)

    write_xmind(target, root, args.title or root["title"])
    print("已生成：{}".format(target.resolve()))
    print("节点总数：{}".format(count_nodes(root)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
