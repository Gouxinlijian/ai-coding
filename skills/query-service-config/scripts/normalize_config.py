"""Normalize ordered YAML, JSON, and Properties sources into two semantic formats."""

import argparse
import json
import re
from pathlib import Path


def load_yaml_module():
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("缺少 PyYAML，请先安装 PyYAML 后再处理 YAML") from exc
    return yaml


def parse_properties(text):
    values = {}
    continuation = ""
    for raw_line in text.splitlines():
        line = continuation + raw_line
        if line.endswith("\\") and not line.endswith("\\\\"):
            continuation = line[:-1]
            continue
        continuation = ""
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", "!")):
            continue
        separator = next((index for index, char in enumerate(line) if char in "=:"), None)
        if separator is None:
            parts = line.split(None, 1)
            key, value = parts[0], parts[1] if len(parts) > 1 else ""
        else:
            key, value = line[:separator], line[separator + 1:]
        values[parse_config_path(key.strip())] = value.strip()
    return values


def parse_config_path(key):
    tokens = []
    position = 0
    while position < len(key):
        if key[position] == ".":
            position += 1
            continue
        if key[position] == "[":
            match = re.match(r"\[(\d+)]", key[position:])
            if not match:
                raise ValueError(f"配置键包含无效列表索引: {key}")
            tokens.append(int(match.group(1)))
            position += len(match.group(0))
            continue
        match = re.match(r"[^.\[]+", key[position:])
        if not match:
            raise ValueError(f"配置键格式无效: {key}")
        tokens.append(match.group(0))
        position += len(match.group(0))
    if not tokens or isinstance(tokens[0], int):
        raise ValueError(f"配置键必须从对象字段开始: {key}")
    return tuple(tokens)


def format_config_path(path):
    parts = []
    for token in path:
        if isinstance(token, int):
            parts.append(f"[{token}]")
        else:
            parts.append(("." if parts else "") + token)
    return "".join(parts)


def flatten(value, prefix=(), output=None):
    output = output if output is not None else {}
    if isinstance(value, dict):
        if not value and prefix:
            output[prefix] = {}
        for key, nested in value.items():
            flatten(nested, prefix + (str(key),), output)
    elif isinstance(value, list):
        if not value and prefix:
            output[prefix] = []
        for index, nested in enumerate(value):
            flatten(nested, prefix + (index,), output)
    elif prefix:
        output[prefix] = value
    return output


def looks_like_yaml(text):
    lines = text.splitlines()
    for index, raw_line in enumerate(lines):
        stripped = raw_line.strip()
        if not stripped or stripped.startswith(("#", "!")):
            continue
        indent = len(raw_line) - len(raw_line.lstrip())
        if indent > 0 and re.match(r"-\s+[^:]+:\s*", stripped):
            return True
        if not re.match(r"[^:=]+:\s*(?:#.*)?$", stripped):
            continue
        for nested_line in lines[index + 1:]:
            nested = nested_line.strip()
            if not nested or nested.startswith(("#", "!")):
                continue
            nested_indent = len(nested_line) - len(nested_line.lstrip())
            if nested_indent <= indent:
                break
            if nested.startswith("- ") or re.match(r"[^:=]+:\s*", nested):
                return True
    return False


def detect_source_format(path, text):
    suffix = path.suffix.lower()
    if suffix in {".yml", ".yaml"}:
        return "yaml"
    if suffix == ".json":
        return "json"
    stripped = text.lstrip()
    if stripped.startswith("{") and stripped.rstrip().endswith("}"):
        return "json"
    return "yaml" if looks_like_yaml(text) else "properties"


def yaml_loader_with_duplicate_check(yaml):
    class UniqueKeyLoader(yaml.SafeLoader):
        pass

    def construct_mapping(loader, node, deep=False):
        mapping = {}
        for key_node, value_node in node.value:
            key = loader.construct_object(key_node, deep=deep)
            if key in mapping:
                raise ValueError(f"YAML 存在重复键: {key}")
            mapping[key] = loader.construct_object(value_node, deep=deep)
        return mapping

    UniqueKeyLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, construct_mapping)
    return UniqueKeyLoader


def load_source(path):
    text = path.read_text(encoding="utf-8-sig")
    source_format = detect_source_format(path, text)
    if source_format == "yaml":
        yaml = load_yaml_module()
        documents = list(yaml.load_all(text, Loader=yaml_loader_with_duplicate_check(yaml)))
        merged = {}
        for document in documents:
            if document is not None:
                if not isinstance(document, dict):
                    raise ValueError(f"YAML 根节点必须是对象: {path}")
                merged.update(flatten(document))
        return merged
    if source_format == "json":
        value = json.loads(text)
        if not isinstance(value, dict):
            raise ValueError(f"JSON 根节点必须是对象: {path}")
        return flatten(value)
    return parse_properties(text)


def format_property_value(value):
    if isinstance(value, bool):
        return str(value).lower()
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return str(value)


MISSING = object()


def build_structure(values):
    root = {}
    for path in sorted(values, key=lambda item: tuple(
            (1, token) if isinstance(token, int) else (0, token) for token in item)):
        cursor = root
        for index, token in enumerate(path):
            last = index == len(path) - 1
            next_token = None if last else path[index + 1]
            if isinstance(token, int):
                if not isinstance(cursor, list):
                    raise ValueError(f"列表路径与对象冲突: {format_config_path(path)}")
                while len(cursor) <= token:
                    cursor.append(MISSING)
                if last:
                    if cursor[token] is not MISSING:
                        raise ValueError(f"配置路径重复: {format_config_path(path)}")
                    cursor[token] = values[path]
                    continue
                expected_type = list if isinstance(next_token, int) else dict
                if cursor[token] is MISSING:
                    cursor[token] = expected_type()
                elif not isinstance(cursor[token], expected_type):
                    raise ValueError(f"配置路径类型冲突: {format_config_path(path)}")
                cursor = cursor[token]
                continue

            if not isinstance(cursor, dict):
                raise ValueError(f"对象路径与列表冲突: {format_config_path(path)}")
            if last:
                if token in cursor:
                    raise ValueError(f"配置路径重复或层级冲突: {format_config_path(path)}")
                cursor[token] = values[path]
                continue
            expected_type = list if isinstance(next_token, int) else dict
            if token not in cursor:
                cursor[token] = expected_type()
            elif not isinstance(cursor[token], expected_type):
                raise ValueError(f"配置路径类型冲突: {format_config_path(path)}")
            cursor = cursor[token]

    def reject_sparse_lists(value, path=()):
        if isinstance(value, list):
            if any(item is MISSING for item in value):
                raise ValueError(f"列表索引不连续: {format_config_path(path)}")
            for index, item in enumerate(value):
                reject_sparse_lists(item, path + (index,))
        elif isinstance(value, dict):
            for key, item in value.items():
                reject_sparse_lists(item, path + (key,))

    reject_sparse_lists(root)
    return root


def indented_yaml_dumper(yaml):
    class IndentedSafeDumper(yaml.SafeDumper):
        def increase_indent(self, flow=False, indentless=False):
            return super().increase_indent(flow, False)

    return IndentedSafeDumper


def write_outputs(merged, out_properties, out_yaml):
    out_properties.parent.mkdir(parents=True, exist_ok=True)
    out_yaml.parent.mkdir(parents=True, exist_ok=True)
    with out_properties.open("w", encoding="utf-8-sig", newline="\n") as handle:
        for path in sorted(merged, key=format_config_path):
            handle.write(
                f"{format_config_path(path)}={format_property_value(merged[path])}\n"
            )
    yaml = load_yaml_module()
    structure = build_structure(merged)
    with out_yaml.open("w", encoding="utf-8-sig", newline="\n") as handle:
        yaml.dump(
            structure,
            handle,
            Dumper=indented_yaml_dumper(yaml),
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
        )


def parse_source(value):
    label, separator, raw_path = value.partition("=")
    if not separator or not label.strip() or not raw_path.strip():
        raise argparse.ArgumentTypeError("--source 必须使用 名称=文件路径")
    path = Path(raw_path).expanduser().resolve()
    if not path.is_file():
        raise argparse.ArgumentTypeError(f"来源文件不存在: {path}")
    return label.strip(), path


def main():
    parser = argparse.ArgumentParser(description="按给定优先级标准化并合并配置")
    parser.add_argument("--source", action="append", type=parse_source, required=True,
                        help="名称=文件路径；参数顺序从低优先级到高优先级")
    parser.add_argument("--out-properties", type=Path, required=True)
    parser.add_argument("--out-yaml", type=Path, required=True)
    args = parser.parse_args()
    merged, owners, overrides = {}, {}, []
    for label, path in args.source:
        try:
            values = load_source(path)
        except Exception as exc:
            raise SystemExit(f"解析失败 [{label}] {path}: {exc}") from exc
        for config_path, value in values.items():
            if config_path in merged:
                overrides.append({
                    "key": format_config_path(config_path),
                    "from": owners[config_path],
                    "to": label,
                })
            merged[config_path], owners[config_path] = value, label
    try:
        write_outputs(merged, args.out_properties.resolve(), args.out_yaml.resolve())
    except Exception as exc:
        raise SystemExit(f"输出失败: {exc}") from exc
    print(json.dumps({"keys": len(merged), "overrides": len(overrides),
                      "override_details": overrides,
                      "precedence": [label for label, _ in args.source]},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()


