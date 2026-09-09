"""Annotate Properties keys with confirmed business-purpose descriptions."""

import argparse
import json
import re
from pathlib import Path

SKIP_DIRS = {".git", "node_modules", "target", "build", "dist", ".venv", "venv"}
SOURCE_SUFFIXES = {".java", ".kt", ".go", ".js", ".ts", ".py"}
DIRECT_PATTERNS = [
    re.compile(r'@Value\s*\(\s*["\']\$\{([^}:]+)'),
    re.compile(r'process\.env\.([A-Z][A-Z0-9_]*)'),
    re.compile(r'os\.(?:getenv|environ\.get)\(\s*["\']([^"\']+)'),
    re.compile(r'viper\.Get(?:String|Bool|Int|Duration)?\(\s*["\']([^"\']+)'),
]
PREFIX_PATTERN = re.compile(r'@ConfigurationProperties\s*\(\s*(?:prefix\s*=\s*)?["\']([^"\']+)')
JAVA_FIELD_PATTERN = re.compile(
    r"\b(?:private|protected|public)\s+[\w<>?,.\[\]]+\s+([A-Za-z][A-Za-z0-9_]*)\s*[;=]"
)
SOURCE_REFERENCE_PATTERN = re.compile(
    r"(?:直接引用|配置字段)[：:]|\.(?:java|kt|go|js|ts|py):\d+"
)


def camel_to_kebab(value):
    return re.sub(r"(?<!^)(?=[A-Z])", "-", value).lower()


def iter_source_files(project):
    for path in project.rglob("*"):
        if path.is_file() and path.suffix.lower() in SOURCE_SUFFIXES:
            if not any(part in SKIP_DIRS for part in path.parts):
                yield path


def collect_evidence(project):
    evidence = {}
    for path in iter_source_files(project):
        relative = path.relative_to(project).as_posix()
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        for line_number, line in enumerate(text.splitlines(), start=1):
            for pattern in DIRECT_PATTERNS:
                for match in pattern.finditer(line):
                    evidence.setdefault(match.group(1), f"直接引用：{relative}:{line_number}")
        for prefix_match in PREFIX_PATTERN.finditer(text):
            prefix = prefix_match.group(1)
            class_block = text[prefix_match.end():prefix_match.end() + 12000]
            next_class = class_block.find("\nclass ", 1)
            if next_class >= 0:
                class_block = class_block[:next_class]
            start_line = text.count("\n", 0, prefix_match.start()) + 1
            for field_match in JAVA_FIELD_PATTERN.finditer(class_block):
                field = field_match.group(1)
                line_number = start_line + class_block.count("\n", 0, field_match.start())
                for field_key in {field, camel_to_kebab(field)}:
                    evidence.setdefault(f"{prefix}.{field_key}",
                                        f"配置字段：{relative}:{line_number}")
    return evidence


def load_descriptions(path):
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError("业务作用说明必须是 JSON 对象")

    descriptions = {}
    for key, value in data.items():
        description = value.get("description") if isinstance(value, dict) else value
        if not isinstance(description, str) or not description.strip():
            raise ValueError(f"配置 {key} 缺少非空的 description")
        description = description.strip()
        if SOURCE_REFERENCE_PATTERN.search(description):
            raise ValueError(f"配置 {key} 的 description 不能使用源码位置代替业务作用")
        descriptions[key] = description
    return descriptions


def split_property(line):
    stripped = line.strip()
    if not stripped or stripped.startswith(("#", "!")):
        return None
    match = re.match(r"([^\s=:]+)\s*[:=]", line)
    return match.group(1) if match else None


def annotate(input_path, output_path, descriptions):
    output = []
    for line in input_path.read_text(encoding="utf-8-sig").splitlines():
        key = split_property(line)
        if key:
            previous = next((item.strip() for item in reversed(output) if item.strip()), "")
            if not previous.startswith(("#", "!")):
                description = descriptions.get(
                    key,
                    "未确认具体作用（需继续分析配置绑定后的业务调用链）",
                )
                output.append(f"# {description}")
        output.append(line)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(output) + "\n", encoding="utf-8-sig")


def main():
    parser = argparse.ArgumentParser(description="依据项目代码为 Properties 配置补充注释")
    parser.add_argument("--properties", type=Path, required=True)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--descriptions", type=Path, required=True,
                        help="配置键到中文业务作用说明的 JSON 文件")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    properties, project = args.properties.resolve(), args.project.resolve()
    if not properties.is_file():
        parser.error(f"Properties 文件不存在: {properties}")
    if not project.is_dir():
        parser.error(f"项目目录不存在: {project}")
    if not args.descriptions.is_file():
        parser.error(f"业务作用说明文件不存在: {args.descriptions}")
    evidence = collect_evidence(project)
    try:
        descriptions = load_descriptions(args.descriptions.resolve())
    except (OSError, json.JSONDecodeError, ValueError) as error:
        parser.error(str(error))
    annotate(properties, args.output.resolve(), descriptions)
    print(
        f"OK: 已写入 {args.output.resolve()}，业务作用 {len(descriptions)} 项，"
        f"内部代码证据 {len(evidence)} 项"
    )


if __name__ == "__main__":
    main()


