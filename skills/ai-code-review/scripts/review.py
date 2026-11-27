#!/usr/bin/env python3
"""仅依赖 Python 标准库的本地代码评审引擎。"""
from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import stat
import subprocess
import sys
from collections import Counter
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

SEVERITIES = ("critical", "high", "medium", "low", "info")
SEVERITY_PENALTY = {"critical": 40, "high": 25, "medium": 12, "low": 4, "info": 1}
CATEGORIES = {"bug", "security", "performance", "maintainability", "style", "documentation", "resource", "other"}
SEVERITY_LABELS = {"critical": "严重", "high": "高", "medium": "中", "low": "低", "info": "提示"}
STATUS_LABELS = {"complete": "完成", "incomplete": "不完整", "preview": "预览"}
GATE_LABELS = {"passed": "通过", "failed": "未通过", "not_evaluated": "未评估"}
SOURCE_LABELS = {"working-tree": "工作区变更", "commit": "单个提交", "range": "提交区间", "scan": "整文件扫描"}
TEXT_EXTENSIONS = {
    ".c", ".cc", ".cpp", ".cxx", ".h", ".hpp", ".cs", ".css", ".dart", ".fs", ".go", ".graphql",
    ".hcl", ".hh", ".java", ".jl", ".js", ".json", ".jsx", ".kt", ".kts", ".lua", ".m", ".mm",
    ".php", ".pl", ".properties", ".proto", ".py", ".rb", ".rs", ".scala", ".sh", ".sql", ".swift",
    ".tf", ".thrift", ".ts", ".tsx", ".v", ".vh", ".vhd", ".yaml", ".yml", ".xml", ".zig",
}
PROTECTED = [".env", ".env.*", "**/.ssh/**", "**/id_rsa", "**/id_dsa", "**/id_ecdsa", "**/id_ed25519", "**/.netrc", "**/_netrc", "**/.npmrc", "**/.pypirc", "**/.dockercfg"]
IGNORED_DIRS = {".git", ".idea", ".venv", "__pycache__", "node_modules", "vendor", "target", "dist", "build", ".gradle", ".terraform", "coverage", "bin"}
GENERATED = ["**/*.generated.*", "**/*.gen.go", "**/*.pb.go", "**/*.pb.h", "**/*.designer.cs", "**/migrations/*"]


def eprint(message: str) -> None:
    print(message, file=sys.stderr)


def git_bytes(args: Sequence[str], repo: Path) -> bytes:
    result = subprocess.run(["git", "-C", str(repo), "--literal-pathspecs", *args], capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.decode("utf-8", errors="replace").strip() or "git command failed")
    return result.stdout


def run_git(args: Sequence[str], repo: Path) -> str:
    return git_bytes(args, repo).decode("utf-8", errors="replace")


def git_paths(args: Sequence[str], repo: Path) -> List[str]:
    return [os.fsdecode(path) for path in git_bytes(args, repo).split(b"\0") if path]


def repo_root(start: Path) -> Path:
    return Path(os.fsdecode(git_bytes(["rev-parse", "--show-toplevel"], start)).rstrip("\r\n")).resolve()


def rel_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def is_match(path: str, pattern: str) -> bool:
    normalized = path.replace("\\", "/").removeprefix("./").lstrip("/")
    pattern = pattern.replace("\\", "/").removeprefix("./").lstrip("/")
    name = normalized.rsplit("/", 1)[-1]
    return fnmatch.fnmatchcase(normalized, pattern) or fnmatch.fnmatchcase(name, pattern) or (
        pattern.startswith("**/") and fnmatch.fnmatchcase(normalized, pattern[3:])
    )


def protected(path: str) -> bool:
    normalized = path.replace("\\", "/").lower()
    return ".ssh" in normalized.split("/") or any(is_match(normalized, pattern) for pattern in PROTECTED)


def ignored(path: str) -> bool:
    parts = set(Path(path).parts)
    return bool(parts & IGNORED_DIRS) or any(is_match(path, pattern) for pattern in GENERATED)


def load_config(repo: Optional[Path], explicit: Optional[str]) -> Tuple[Dict[str, Any], str]:
    candidates = []
    if explicit:
        candidates.append((Path(explicit).expanduser(), "explicit"))
    if repo:
        candidates.append((repo / ".ai-code-review" / "rules.json", "repository"))
    candidates.append((Path.home() / ".ai-code-review" / "rules.json", "user"))
    for file_path, source in candidates:
        if source == "explicit" or file_path.is_file():
            try:
                data = json.loads(file_path.read_text(encoding="utf-8"))
                if not isinstance(data, dict):
                    raise ValueError("configuration root must be an object")
                data.setdefault("version", 1)
                validate_config(data)
                return data, source
            except (OSError, json.JSONDecodeError, ValueError) as exc:
                raise RuntimeError(f"invalid rules file {file_path}: {exc}") from exc
    return {"version": 1, "fail_on": "high", "rules": []}, "builtin"


def validate_config(config: Dict[str, Any]) -> None:
    if config.get("version") != 1:
        raise ValueError("only configuration version 1 is supported")
    if config.get("fail_on", "high") not in SEVERITIES:
        raise ValueError("fail_on must be critical, high, medium, low, or info")
    size = config.get("max_file_bytes", 500000)
    if type(size) is not int or not 0 < size < sys.maxsize:
        raise ValueError("max_file_bytes must be a positive byte limit below sys.maxsize")
    for key in ("include", "exclude", "rules"):
        if key in config and not isinstance(config[key], list):
            raise ValueError(f"{key} must be an array")
    for key in ("include", "exclude"):
        if any(not isinstance(pattern, str) for pattern in config.get(key, [])):
            raise ValueError(f"{key} must contain only string patterns")
    for index, rule in enumerate(config.get("rules", [])):
        required = {"id", "path", "category", "severity", "pattern", "message", "suggestion"}
        if not isinstance(rule, dict) or not required.issubset(rule):
            raise ValueError(f"custom rule {index} is missing required fields")
        if rule["category"] not in CATEGORIES or rule["severity"] not in SEVERITIES:
            raise ValueError(f"custom rule {rule.get('id', index)} has invalid category/severity")
        try:
            re.compile(str(rule["pattern"]), regex_flags(rule.get("flags", "")))
        except re.error as exc:
            raise ValueError(f"custom rule {rule.get('id', index)} has invalid regex: {exc}") from exc


def regex_flags(value: Any) -> int:
    flags = 0
    for item in str(value).replace("|", ",").split(","):
        item = item.strip().upper()
        flags |= {"IGNORECASE": re.IGNORECASE, "MULTILINE": re.MULTILINE, "DOTALL": re.DOTALL}.get(item, 0)
    return flags


def effective_rules(config: Dict[str, Any], path: str) -> List[Dict[str, Any]]:
    return [rule for rule in config.get("rules", []) if is_match(path, str(rule.get("path", "**/*")))]


def resolve_commit(repo: Path, ref: str) -> str:
    return run_git(["rev-parse", "--verify", "--end-of-options", f"{ref}^{{commit}}"], repo).strip()


def diff_scope(repo: Path, commit: Optional[str], base: Optional[str], target: Optional[str]) -> Tuple[List[str], List[str], Optional[str]]:
    if commit:
        snapshot = resolve_commit(repo, commit)
        header = git_bytes(["cat-file", "commit", snapshot], repo).partition(b"\n\n")[0]
        first_parent = next((line[7:].decode("ascii") for line in header.split(b"\n") if line.startswith(b"parent ")), None)
        if first_parent is None:
            return ["diff-tree", "--root", "--no-commit-id", "-r"], [snapshot], snapshot
        return ["diff"], [first_parent, snapshot], snapshot
    if base:
        snapshot = resolve_commit(repo, target or "HEAD")
        return ["diff"], [f"{resolve_commit(repo, base)}...{snapshot}"], snapshot
    return ["diff"], ["HEAD"], None


def diff_options(command: List[str]) -> List[str]:
    return [*command, "--no-ext-diff", "--no-textconv", "--no-renames"]


def changed_ranges(repo: Path, command: List[str], refs: List[str], path: str) -> List[range]:
    patch = git_bytes([*diff_options(command), "--unified=0", "--inter-hunk-context=0", *refs, "--", path], repo)
    ranges = []
    for line in patch.split(b"\n"):
        match = re.match(rb"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", line)
        if match:
            start, count = int(match.group(1)), int(match.group(2) or b"1")
            if count:
                ranges.append(range(start, start + count))
    return ranges


def split_paths(value: Optional[str]) -> List[str]:
    return [item.strip() for item in (value or "").split(",") if item.strip()]


def scan_root(cwd: Path) -> Path:
    return next((parent for parent in (cwd, *cwd.parents) if (parent / ".git").exists()), cwd)


def scan_candidates(root: Path, cwd: Path, raw_paths: List[str], selected: List[str]) -> List[str]:
    specs = [cwd / item for item in raw_paths] + [root / item for item in selected]
    found = set()
    for spec in specs or [root]:
        spec = Path(os.path.abspath(spec))
        if spec.exists() or spec.is_symlink():
            matches = [spec]
        elif any(char in str(spec) for char in "*?["):
            anchor = Path(spec.anchor)
            matches = list(anchor.glob(spec.relative_to(anchor).as_posix()))
        else:
            matches = []
        if not matches:
            raise ValueError(f"scan path matched nothing: {spec}")
        for match in matches:
            if match.is_symlink() or not match.is_dir():
                found.add(match)
            else:
                def walk_error(error: OSError) -> None:
                    raise error
                for folder, directories, names in os.walk(match, onerror=walk_error):
                    directories[:] = [name for name in directories if name != ".git"]
                    found.update(Path(folder) / name for name in names)
    return sorted(path.relative_to(root).as_posix() if path.is_relative_to(root) else path.as_posix() for path in found)


def path_decision(path: str, config: Dict[str, Any]) -> Tuple[str, str]:
    if protected(path):
        return "sensitive_path", "protected path excluded before user rules"
    if any(is_match(path, pattern) for pattern in config.get("exclude", [])):
        return "excluded", "matched configured exclude"
    includes = config.get("include", [])
    if includes and not any(is_match(path, pattern) for pattern in includes):
        return "excluded", "outside configured include"
    if ignored(path):
        return "generated", "dependency, build, generated, or ignored path"
    return "reviewed", "eligible"


def read_candidate(repo: Path, path: str, snapshot: Optional[str], limit: int) -> Tuple[str, str, bytes]:
    if snapshot:
        entry = git_bytes(["ls-tree", "-z", snapshot, "--", path], repo)
        if not entry:
            raise RuntimeError("path missing from target snapshot")
        mode, kind, object_id = entry.split(b"\t", 1)[0].split()
        if kind != b"blob" or mode == b"120000":
            return "unsupported", "not a regular file in the target snapshot", b""
        blob = object_id.decode("ascii")
        if int(run_git(["cat-file", "-s", blob], repo)) > limit:
            return "too_large", "file exceeds max_file_bytes", b""
        content = git_bytes(["cat-file", "blob", blob], repo)
    else:
        file_path = repo / path
        info = file_path.lstat()
        if not stat.S_ISREG(info.st_mode):
            return "unsupported", "not a regular file", b""
        if protected(file_path.resolve().as_posix()):
            return "sensitive_path", "resolved path is protected", b""
        if info.st_size > limit:
            return "too_large", "file exceeds max_file_bytes", b""
        with file_path.open("rb") as stream:
            content = stream.read(limit + 1)
    if len(content) > limit:
        return "too_large", "file exceeds max_file_bytes", b""
    if b"\x00" in content[:8192]:
        return "binary", "file contains NUL bytes in the initial sample", b""
    name = Path(path)
    if name.suffix.lower() not in TEXT_EXTENSIONS and name.name not in {"Dockerfile", "Makefile", "WORKSPACE", "BUILD"}:
        return "unsupported", "extension is not in the text-language allowlist", b""
    return "reviewed", "eligible", content


def finding(rule_id: str, category: str, severity: str, path: str, line: int, message: str, suggestion: str, source: str = "builtin", confidence: str = "medium", end_line: Optional[int] = None) -> Dict[str, Any]:
    return {"rule_id": rule_id, "category": category, "severity": severity, "path": path, "start_line": max(1, line), "end_line": max(1, end_line or line), "message": message, "suggestion": suggestion, "confidence": confidence, "source": source}


def builtins(path: str, lines: List[str]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    text = "\n".join(lines)
    def each(pattern: str, callback):
        for number, line in enumerate(lines, 1):
            if re.search(pattern, line):
                out.append(callback(number, line))
    secret = re.compile(r"(?i)(?:api[_-]?key|access[_-]?token|secret|password|passwd|private[_-]?key)\s*[:=]\s*[\"'][^\"']{8,}[\"']|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")
    each(secret.pattern, lambda n, _: finding("security.secret-generic", "security", "critical", path, n, "Credential-like material is present in source; the value is intentionally omitted from this report.", "Remove it, rotate the credential, and load it from a secret manager or protected environment.", confidence="high"))
    each(r"(?i)(?:execute|query|raw|cursor)\s*\([^\n]*(?:\+|%s|\.format\(|f[\"'])", lambda n, _: finding("security.sql-concat", "security", "high", path, n, "SQL appears to be assembled from a dynamic value, which can enable injection.", "Use parameterized queries or a trusted query builder; validate inputs at the boundary.", confidence="medium"))
    each(r"(?i)\b(?:eval|exec)\s*\(|new\s+Function\s*\(", lambda n, _: finding("security.dynamic-eval", "security", "high", path, n, "Dynamic code evaluation makes input-to-code execution possible.", "Remove dynamic evaluation or replace it with a closed allowlist of operations.", confidence="high"))
    each(r"(?i)\b(?:child_process\.(?:exec|execSync)|os\.system|subprocess\.(?:run|Popen|call))\s*\([^\n]*(?:\+|format\(|f[\"']|shell\s*=\s*True)", lambda n, _: finding("security.command-injection", "security", "high", path, n, "A process command is built from dynamic input or enables shell interpretation.", "Use an argument array, disable shell interpretation, and validate against an allowlist.", confidence="medium"))
    each(r"(?i)(?:innerHTML|outerHTML|insertAdjacentHTML)\s*=|dangerouslySetInnerHTML", lambda n, _: finding("security.xss-sink", "security", "high", path, n, "Unescaped HTML is written to a browser sink.", "Escape untrusted content or use a safe DOM/template API with an explicit sanitizer.", confidence="high"))
    each(r"(?i)\b(?:md5|sha1)\s*\(|(?:random\.random|Math\.random)\s*\(", lambda n, _: finding("security.weak-crypto", "security", "medium", path, n, "A weak hash or non-cryptographic random source is used.", "Use a modern approved hash and a cryptographically secure random source for security-sensitive values.", confidence="medium"))
    each(r"(?i)\b(?:except\s+Exception|catch\s*\([^)]*Exception|catch\s*\([^)]*Throwable)\s*[:{]", lambda n, _: finding("bug.broad-exception", "bug", "medium", path, n, "A broad exception handler can hide unrelated failures.", "Catch the narrow expected exception, preserve context, and handle or rethrow it explicitly.", confidence="medium"))
    each(r"(?i)\b(?:TODO|FIXME|HACK)\b", lambda n, _: finding("maintainability.todo-risk", "maintainability", "low", path, n, "An unresolved TODO/FIXME/HACK marker remains in the reviewed code.", "Resolve the work, link a tracked issue, or remove the marker when it is no longer actionable.", confidence="high"))
    each(r"(?i)\b(?:print|println|console\.log|System\.out\.print)\s*\(", lambda n, _: finding("style.debug-output", "style", "low", path, n, "Direct console output can bypass structured logging and leak noisy diagnostics.", "Use the project logging abstraction and include appropriate context and log level.", confidence="medium"))
    each(r"(?i)\b(?:const|let|var|int|string|boolean|bool|auto)\s+[a-zA-Z_]\s*(?:=|;|,)", lambda n, _: finding("style.naming", "style", "low", path, n, "A one-letter local name reduces readability and makes maintenance harder.", "Use a descriptive name that communicates the value's role and scope.", confidence="medium"))
    each(r"(?i)\b(?:open|FileInputStream|FileOutputStream|Socket|createConnection|connect)\s*\(", lambda n, _: finding("resource.unclosed-resource", "resource", "medium", path, n, "A manually opened resource is visible; no close boundary is proven locally.", "Use a context manager, try-with-resources, or an explicit finally/close path.", confidence="low"))
    each(r"(?i)\b(?:for|while)\b[^\n]*\{?\s*$", lambda n, _: finding("performance.loop-work", "performance", "low", path, n, "Loop work may be repeated for each item; inspect complexity and avoid repeated I/O or lookup.", "Move invariant work outside the loop and use indexed or batched operations where appropriate.", confidence="low"))
    for n, line in enumerate(lines, 1):
        if len(line.rstrip("\n")) > 140:
            out.append(finding("style.long-line", "style", "info", path, n, "Line exceeds 140 characters and may reduce readability or hide logic.", "Wrap the expression or extract a named value without changing behavior.", confidence="high"))
    if len(lines) > 300:
        out.append(finding("maintainability.long-file", "maintainability", "low", path, 1, "The file is large enough to increase review and change risk.", "Split cohesive responsibilities into smaller modules while preserving a stable public interface.", confidence="high", end_line=min(len(lines), 3)))
    if re.search(r"(?m)^\s*(?:def|function|func|public\s+\w+\s+\w+|private\s+\w+\s+\w+)\b", text) and len(lines) > 150:
        out.append(finding("maintainability.long-function", "maintainability", "low", path, 1, "A large source file contains functions that may be difficult to reason about locally.", "Measure individual function size and extract cohesive responsibilities where needed.", confidence="low"))
    return out


def custom_findings(path: str, lines: List[str], rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    text = "\n".join(lines)
    for rule in rules:
        regex = re.compile(str(rule["pattern"]), regex_flags(rule.get("flags", "")))
        for match in regex.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            out.append(finding(str(rule["id"]), str(rule["category"]), str(rule["severity"]), path, line, str(rule["message"]), str(rule["suggestion"]), source="custom", confidence="high"))
    return out


def dedupe(findings: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    result = []
    seen = set()
    for item in findings:
        key = (item["rule_id"], item["path"], item["start_line"], item["message"])
        if key not in seen:
            seen.add(key); result.append(item)
    return sorted(result, key=lambda item: (item["path"], item["start_line"], -SEVERITY_PENALTY[item["severity"]], item["rule_id"]))


def make_sarif(report: Dict[str, Any]) -> Dict[str, Any]:
    rules = {}
    results = []
    for item in report["findings"]:
        rules.setdefault(item["rule_id"], {"id": item["rule_id"], "shortDescription": {"text": item["rule_id"]}})
        results.append({"ruleId": item["rule_id"], "level": "error" if item["severity"] in {"critical", "high"} else "warning", "message": {"text": item["message"] + " Fix: " + item["suggestion"]}, "locations": [{"physicalLocation": {"artifactLocation": {"uri": item["path"]}, "region": {"startLine": item["start_line"], "endLine": item["end_line"]}}}]})
    return {"version": "2.1.0", "$schema": "https://json.schemastore.org/sarif-2.1.0.json", "runs": [{"tool": {"driver": {"name": "ai-code-review", "informationUri": "local", "rules": list(rules.values())}}, "results": results}]}


def execute(args: argparse.Namespace) -> Tuple[Dict[str, Any], int, Path]:
    mode = "scan" if args.command == "scan" else "diff"
    selected = split_paths(args.paths)
    command: List[str] = []
    refs: List[str] = []
    snapshot: Optional[str] = None
    untracked = set()
    if mode == "scan":
        cwd = Path.cwd().resolve()
        repo = scan_root(cwd)
        paths = scan_candidates(repo, cwd, split_paths(args.path), selected)
        if not paths:
            raise ValueError("scan scope contains no candidate files")
    else:
        repo = repo_root(Path(args.path or ".").resolve())
        command, refs, snapshot = diff_scope(repo, args.commit, args.from_ref, args.to_ref)
        tracked = git_paths([*diff_options(command), "--name-only", "-z", "--diff-filter=ACMRTUXB", *refs, "--"], repo)
        if snapshot is None:
            untracked = set(git_paths(["ls-files", "-z", "--others", "--exclude-standard"], repo))
        paths = sorted(path for path in set(tracked) | untracked if not selected or any(
            is_match(path, item) or path.startswith(item.replace("\\", "/").removeprefix("./").rstrip("/") + "/")
            for item in selected
        ))
    config, config_source = load_config(repo, args.config)
    limit = config.get("max_file_bytes", 500000)
    files = []
    findings = []
    warnings = []
    for path in paths:
        decision, reason = path_decision(path, config)
        rules_source = None
        if decision == "reviewed":
            try:
                decision, reason, content = read_candidate(repo, path, snapshot, limit)
                if decision == "reviewed":
                    rules = effective_rules(config, path)
                    rules_source = "custom" if rules else config_source
                    if not args.preview:
                        lines = [line.removesuffix("\r") for line in content.decode("utf-8", errors="replace").removesuffix("\n").split("\n")] if content else []
                        current = builtins(path, lines) + custom_findings(path, lines, rules)
                        if mode == "diff" and path not in untracked:
                            ranges = changed_ranges(repo, command, refs, path)
                            current = [item for item in current if any(item["start_line"] in span for span in ranges)]
                        findings.extend(current)
            except (OSError, RuntimeError) as exc:
                decision, reason = "failed", str(exc)
                warnings.append(f"{path}: {exc}")
        entry = {"path": path, "decision": decision, "reason": reason}
        if decision == "reviewed" and rules_source is not None:
            entry["ruleset"] = rules_source
        files.append(entry)
    findings = dedupe(findings)
    counts = Counter(item["severity"] for item in findings)
    categories = Counter(item["category"] for item in findings)
    threshold = args.fail_on or config.get("fail_on", "high")
    decisions = Counter(entry["decision"] for entry in files)
    incomplete = decisions["failed"] > 0
    blocked = any(SEVERITY_PENALTY[item["severity"]] >= SEVERITY_PENALTY[threshold] for item in findings)
    scope = {"mode": mode, "source": "scan" if mode == "scan" else ("commit" if args.commit else "range" if args.from_ref else "working-tree")}
    if snapshot is not None:
        scope["target_commit"] = snapshot
    report = {
        "status": "incomplete" if incomplete else "preview" if args.preview else "complete",
        "scope": scope,
        "files": files,
        "findings": findings,
        "summary": {
            "files_considered": len(paths), "files_reviewed": decisions["reviewed"],
            "files_failed": decisions["failed"], "by_decision": dict(sorted(decisions.items())),
            "findings": len(findings), "by_severity": {name: counts.get(name, 0) for name in SEVERITIES},
            "by_category": dict(sorted(categories.items())),
        },
        "score": None if incomplete or args.preview else max(0, 100 - sum(SEVERITY_PENALTY[item["severity"]] for item in findings)),
        "quality_gate": {"fail_on": threshold, "status": "failed" if incomplete or blocked else "not_evaluated" if args.preview else "passed"},
        "ruleset": {"source": config_source, "version": config.get("version", 1)},
        "warnings": warnings,
    }
    code = 1 if incomplete or blocked else 0
    return report, code, repo


def text_report(report: Dict[str, Any]) -> str:
    scope = report["scope"]
    summary = report["summary"]
    gate = report["quality_gate"]
    score = "不适用" if report["score"] is None else f"{report['score']}/100"
    status = STATUS_LABELS.get(report["status"], report["status"])
    gate_status = GATE_LABELS.get(gate["status"], gate["status"])
    source = SOURCE_LABELS.get(scope["source"], scope["source"])
    lines = [
        f"代码评审：{status}",
        f"范围：{source}（{scope['mode']}）",
        f"文件：已评审 {summary['files_reviewed']}/{summary['files_considered']}，失败 {summary['files_failed']}",
        f"评分：{score}｜门禁：{gate_status}（阈值 {gate['fail_on']}）",
    ]
    if "target_commit" in scope:
        lines.append(f"评审版本：{scope['target_commit']}")
    if summary["by_decision"]:
        decisions = "，".join(f"{name} {count} 个" for name, count in summary["by_decision"].items())
        lines.append(f"文件处置：{decisions}")
    lines.extend(f"告警：{warning}" for warning in report["warnings"])
    lines.append("")
    if not report["findings"]:
        if report["status"] == "preview":
            lines.append("本次仅为预览，未运行检测器。")
        elif report["status"] == "incomplete":
            lines.append("已完成部分未发现问题，但本次评审不完整。")
        else:
            lines.append("已评审文件中未发现问题。")
    else:
        for severity in SEVERITIES:
            items = [item for item in report["findings"] if item["severity"] == severity]
            if items:
                lines.append(f"[{SEVERITY_LABELS[severity]}]")
                for item in items:
                    lines.append(f"- {item['path']}:{item['start_line']}-{item['end_line']} [{item['category']}] {item['message']}")
                    lines.append(f"  建议：{item['suggestion']}")
    return "\n".join(lines)


def markdown_text(value: str) -> str:
    plain = escape(" ".join(value.splitlines()), quote=False)
    return re.sub(r"([\\`*_\[\]])", r"\\\1", plain)


def markdown_report(report: Dict[str, Any], code: int) -> str:
    scope = report["scope"]
    summary = report["summary"]
    gate = report["quality_gate"]
    score = "不适用" if report["score"] is None else f"{report['score']}/100"
    status = STATUS_LABELS.get(report["status"], report["status"])
    gate_status = GATE_LABELS.get(gate["status"], gate["status"])
    source = SOURCE_LABELS.get(scope["source"], scope["source"])
    lines = [
        "# 代码评审报告（引擎结果）",
        "",
        f"- 状态：{status}",
        f"- 范围：{source}（{scope['mode']}）",
        f"- 评分：{score}",
        f"- 质量门禁：{gate_status}（阈值 {gate['fail_on']}）",
        f"- 引擎退出码：{code}",
        f"- 文件：已评审 {summary['files_reviewed']}/{summary['files_considered']}，失败 {summary['files_failed']}",
    ]
    if "target_commit" in scope:
        lines.append(f"- 评审版本：`{scope['target_commit']}`")
    if summary["by_decision"]:
        decisions = "，".join(f"{name} {count} 个" for name, count in summary["by_decision"].items())
        lines.append(f"- 文件处置：{decisions}")

    lines.extend(["", "## 引擎确定性问题", ""])
    if not report["findings"]:
        if report["status"] == "preview":
            lines.append("本次仅为预览，未运行检测器。")
        elif report["status"] == "incomplete":
            lines.append("已完成部分未发现问题，但本次评审不完整。")
        else:
            lines.append("已评审文件中未发现问题。")
    else:
        for severity in SEVERITIES:
            items = [item for item in report["findings"] if item["severity"] == severity]
            if not items:
                continue
            lines.extend([f"### {SEVERITY_LABELS[severity]}", ""])
            for item in items:
                location = f"{markdown_text(item['path'])}:{item['start_line']}-{item['end_line']}"
                rule = markdown_text(item["rule_id"])
                lines.append(f"- **{location}** — {markdown_text(item['message'])}")
                lines.append(f"  - 规则：{rule}；来源：engine（{item['source']}）；置信度：{item['confidence']}")
                lines.append(f"  - 建议：{markdown_text(item['suggestion'])}")
            lines.append("")

    if report["warnings"]:
        lines.extend(["", "## 告警", ""])
        lines.extend(f"- {markdown_text(warning)}" for warning in report["warnings"])
    return "\n".join(lines).rstrip() + "\n"


def write_markdown_report(root: Path, report: Dict[str, Any], code: int) -> Path:
    directory = root / "docs" / "local" / "代码评审"
    resolved = directory.resolve()
    if os.path.normcase(str(resolved)) != os.path.normcase(str(directory)):
        raise ValueError(f"评审报告目录不能指向其他位置：{directory}")
    content = markdown_report(report, code)
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    path = resolved / f"review-{stamp}.md"
    suffix = 1
    while True:
        try:
            with path.open("x", encoding="utf-8", errors="backslashreplace") as output:
                output.write(content)
            return path
        except FileExistsError:
            suffix += 1
            path = resolved / f"review-{stamp}-{suffix}.md"


def rules_check(args: argparse.Namespace) -> int:
    target = Path(args.path).resolve()
    start = next((parent for parent in (target, *target.parents) if parent.is_dir()), Path.cwd())
    root = repo_root(start)
    config, source = load_config(root, args.config)
    path = rel_path(target, root)
    rules = effective_rules(config, path)
    print(json.dumps({"path": path, "source": source, "matched": bool(rules), "rules": rules, "builtin_checks": "enabled"}, ensure_ascii=False, indent=2))
    return 0


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="本地代码评审引擎（ai-code-review）")
    sub = p.add_subparsers(dest="command", required=True)
    for name in ("review", "scan"):
        child = sub.add_parser(name)
        child.add_argument("--path", help="repository location" if name == "review" else "comma-separated paths relative to the current directory")
        child.add_argument("--paths", help="comma-separated paths or globs relative to the repository or scan root")
        child.add_argument("--commit")
        child.add_argument("--from", dest="from_ref")
        child.add_argument("--to", dest="to_ref")
        child.add_argument("--config")
        child.add_argument("--format", choices=("text", "json", "sarif"), default="text")
        child.add_argument("--fail-on", choices=SEVERITIES)
        child.add_argument("--preview", action="store_true")
        child.add_argument("--write-report", action="store_true", help="save a Markdown report under docs/local/代码评审/")
    rules = sub.add_parser("rules", help="inspect rule selection")
    rules_sub = rules.add_subparsers(dest="rules_command", required=True)
    check = rules_sub.add_parser("check")
    check.add_argument("path")
    check.add_argument("--config")
    return p


def main() -> int:
    args = parser().parse_args()
    try:
        if args.command == "rules":
            return rules_check(args)
        if args.paths is not None and not split_paths(args.paths):
            raise ValueError("--paths requires at least one selector")
        if args.command == "scan" and args.path is not None and not split_paths(args.path):
            raise ValueError("--path requires at least one selector")
        if args.command == "scan" and (args.commit or args.from_ref or args.to_ref):
            raise ValueError("scan does not accept Git diff refs")
        if args.command == "review" and args.commit and (args.from_ref or args.to_ref):
            raise ValueError("--commit and --from/--to are mutually exclusive")
        if args.command == "review" and args.to_ref and not args.from_ref:
            raise ValueError("--to requires --from")
        report, code, root = execute(args)
        if args.format == "json":
            print(json.dumps(report, indent=2))
        elif args.format == "sarif":
            print(json.dumps(make_sarif(report), indent=2))
        else:
            print(text_report(report))
        if args.write_report:
            path = write_markdown_report(root, report, code)
            eprint(f"ai-code-review: 评审报告已保存到 {path}")
        return code
    except (OSError, RuntimeError, ValueError) as exc:
        eprint(f"ai-code-review: 错误: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
