"""Detect configuration sources used by a project and emit JSON evidence."""

import argparse
import json
import re
from pathlib import Path

TEXT_FILE_NAMES = {"pom.xml", "build.gradle", "build.gradle.kts", "go.mod", "package.json",
                   "requirements.txt", "pyproject.toml", "docker-compose.yml", "docker-compose.yaml"}
TEXT_SUFFIXES = {".yml", ".yaml", ".properties", ".toml", ".json", ".env", ".tf"}
SKIP_DIRS = {".git", ".idea", ".vscode", "node_modules", "target", "build", "dist", ".venv", "venv"}
SOURCE_PATTERNS = {
    "apollo": [r"apollo\.bootstrap", r"app\.id\s*[:=]", r"apollo-client", r"apollo\.meta"],
    "nacos": [r"nacos-config", r"spring\.cloud\.nacos\.config", r"alibaba\.nacos"],
    "spring-cloud-config": [r"spring-cloud-starter-config",
                            r"spring\.config\.import\s*[:=].*configserver:",
                            r"spring\.cloud\.config\.uri"],
    "kubernetes": [r"\bkind\s*:\s*(ConfigMap|Secret|Deployment|StatefulSet)\b",
                   r"configMapKeyRef", r"secretKeyRef", r"envFrom"],
    "consul": [r"spring-cloud-starter-consul-config", r"spring\.cloud\.consul\.config",
               r"consul(?:Template|\.kv|://)"],
    "vault": [r"spring-cloud-starter-vault-config", r"spring\.cloud\.vault",
              r"vault://", r"VAULT_(?:ADDR|TOKEN|NAMESPACE)"],
    "aws-config": [r"appconfig", r"parameter[-_. ]store", r"ssm:GetParameter", r"AWS_APPCONFIG"],
    "azure-app-configuration": [r"azure-app-configuration",
                                r"spring\.cloud\.azure\.appconfiguration",
                                r"AZURE_APP_CONFIGURATION"],
    "gcp-parameter-manager": [r"parameter manager", r"parametermanager\.googleapis\.com",
                              r"google\.cloud\.parametermanager"],
}
LOCAL_NAMES = re.compile(r"^(application|bootstrap)(-[^.]+)?\.(yml|yaml|properties)$")
APOLLO_PROPERTY_KEYS = {"config", "env"}


def read_apollo_properties(path):
    values = {}
    for raw_line in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        line = raw_line.strip()
        if not line or line.startswith(("#", "!")):
            continue
        match = re.match(r"^([^:=\s]+)\s*[:=]\s*(.*)$", line)
        if match and match.group(1) in APOLLO_PROPERTY_KEYS:
            values[match.group(1)] = match.group(2).strip()
    return values


def attach_apollo_properties(sources, path):
    apollo_source = next((item for item in sources if item["source"] == "apollo"), None)
    if apollo_source is None:
        return

    parameters = {
        "properties_file": str(path),
        "precedence": "highest",
        "status": "missing",
    }
    if not path.is_file():
        apollo_source["parameters"] = parameters
        return

    values = read_apollo_properties(path)
    missing = sorted(APOLLO_PROPERTY_KEYS - values.keys())
    parameters.update(values)
    parameters["missing"] = missing
    parameters["status"] = "complete" if not missing else "incomplete"
    apollo_source["parameters"] = parameters
    apollo_source["evidence"].append({
        "file": str(path),
        "scope": "user-home",
        "signals": [f"active {key}" for key in sorted(values)],
    })


def iter_text_files(project):
    for path in project.rglob("*"):
        if not path.is_file() or any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.name in TEXT_FILE_NAMES or path.suffix.lower() in TEXT_SUFFIXES:
            yield path


def detect(project, apollo_properties):
    matches = {name: [] for name in SOURCE_PATTERNS}
    local_evidence = []
    for path in iter_text_files(project):
        relative = path.relative_to(project).as_posix()
        try:
            content = path.read_text(encoding="utf-8-sig", errors="replace")
        except OSError:
            continue
        if LOCAL_NAMES.match(path.name) or "spring.config.import" in content or "configtree:" in content:
            local_evidence.append(relative)
        for source, patterns in SOURCE_PATTERNS.items():
            signals = [pattern for pattern in patterns if re.search(pattern, content, re.IGNORECASE)]
            if signals:
                matches[source].append({"file": relative, "signals": signals})

    sources = []
    if local_evidence:
        sources.append({"source": "spring-local",
                        "adapter": "references/providers/spring-local.md",
                        "confidence": "high", "evidence": sorted(set(local_evidence))})
    for source, evidence in matches.items():
        if evidence:
            signal_count = sum(len(item["signals"]) for item in evidence)
            sources.append({"source": source, "adapter": f"references/providers/{source}.md",
                            "confidence": "high" if signal_count > 1 else "medium",
                            "evidence": evidence})
    attach_apollo_properties(sources, apollo_properties)
    return sources


def main():
    parser = argparse.ArgumentParser(description="检测项目实际使用的配置来源")
    parser.add_argument("--project", type=Path, default=Path.cwd(), help="项目根目录")
    parser.add_argument("--apollo-properties", type=Path, default=Path.home() / "apollo.properties",
                        help="Apollo 主机级配置文件")
    args = parser.parse_args()
    project = args.project.resolve()
    if not project.is_dir():
        parser.error(f"项目目录不存在: {project}")
    result = {"project": str(project), "sources": detect(project, args.apollo_properties)}
    result["status"] = "matched" if result["sources"] else "unresolved"
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["sources"] else 2)


if __name__ == "__main__":
    main()


