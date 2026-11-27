# 配置、输出与报告契约

## 配置

引擎只选择一份 JSON 配置（`version: 1`），优先级为：显式 `--config`、评审根目录或扫描根目录下的
`.ai-code-review/rules.json`、用户目录下的 `.ai-code-review/rules.json`、内置默认配置。
显式指定的文件不存在或非法时直接报错，不回退到下一层。

```json
{
  "version": 1,
  "fail_on": "high",
  "include": ["src/**"],
  "exclude": ["**/generated/**"],
  "max_file_bytes": 500000,
  "rules": [
    {
      "id": "team.rule",
      "path": "**/*.py",
      "category": "style",
      "severity": "medium",
      "pattern": "regex",
      "message": "问题描述",
      "suggestion": "修复方式",
      "flags": "IGNORECASE"
    }
  ]
}
```

- `path`、`include`、`exclude` 使用 Python `fnmatch` 风格，不是 `.gitignore` 规则。
- `include` 收窄候选范围，不能反向放行受保护路径；`exclude` 在保护判断之后生效。
- `max_file_bytes` 为正整数，默认 500,000 字节，超限文件记为 `too_large`。
- 自定义规则与内置检查同时运行；自定义规则不会关闭内置规则。
- 自定义规则必填字段：`id`、`path`、`category`、`severity`、`pattern`、`message`、`suggestion`；
  `flags` 可选 `IGNORECASE`、`MULTILINE`、`DOTALL`。
- 支持的类型：`bug`、`security`、`performance`、`maintainability`、`style`、`documentation`、
  `resource`、`other`；支持级别：`critical`、`high`、`medium`、`low`、`info`。
- 自定义正则来自配置文件，只使用可信来源。

## 范围与文件选择

- 默认 `review` 比较工作区与 `HEAD`，并包含未被 Git 忽略的未跟踪文件，不是仅暂存区。
  `--path` 用于定位仓库，`--paths` 用于收窄变更文件集合。
- `--commit` 分析目标提交的第一父差异（根提交则分析其引入的全部内容）。`--from <base>`
  比较合并基线与 `--to <head>`（默认 `HEAD`）。历史评审读取目标提交的 Git 对象，不读工作区副本；
  如果规则也需要随版本固定，显式传 `--config`。
- `scan --path` 接受相对当前目录的逗号分隔路径或绝对路径；`scan --paths` 接受相对扫描根
  （检测到 Git 时为仓库根，否则为当前目录）的路径。两种参数都支持 glob。
  选择器无匹配或扫描无候选文件都算输入错误。根目录之外的路径以绝对路径展示。
- 引擎只读取普通文件，读取前应用大小限制，并用有界样本检测 NUL 字节判断二进制。
  被排除或不支持的文件不参与评审，并在 `files` 中给出处置原因。
- 文档与任务元数据不参与评审：`docs/**`、`**/docs/**`、`**/ai-tasks/**`、`*.md`、`*.mdx`、
  `*.rst`、`*.adoc` 统一标记为 `excluded`，原因 `documentation or task metadata excluded`。
  评审结论只能引用代码文件，不引用文档内容。
- `scan` 遍历时直接跳过依赖与构建目录（如 `node_modules`、`.venv`、`target`、`dist`、`build`），
  不再逐个枚举后排除；跳过数量记入 `warnings`。
- 差异评审只对变更行运行逐行规则，结果与「扫描整个文件再按变更行过滤」一致；
  文件级规则（长文件、长函数）仍基于完整文件判断。

## JSON 结果

```json
{
  "status": "complete",
  "scope": {"mode": "diff", "source": "working-tree"},
  "files": [
    {"path": "src/app.py", "decision": "reviewed", "reason": "eligible", "ruleset": "builtin"}
  ],
  "findings": [
    {
      "rule_id": "security.secret-generic",
      "category": "security",
      "severity": "critical",
      "path": "src/app.py",
      "start_line": 12,
      "end_line": 12,
      "message": "A credential-like value is present in source.",
      "suggestion": "Remove it, rotate the credential, and load it from a secret store.",
      "confidence": "high",
      "source": "builtin",
      "impact_scope": "文件内",
      "related": []
    }
  ],
  "summary": {
    "files_considered": 1,
    "files_reviewed": 1,
    "files_failed": 0,
    "by_decision": {"reviewed": 1},
    "findings": 1,
    "by_severity": {"critical": 1, "high": 0, "medium": 0, "low": 0, "info": 0},
    "by_category": {"security": 1}
  },
  "score": 60,
  "quality_gate": {"fail_on": "high", "status": "failed"},
  "ruleset": {"source": "builtin", "version": 1},
  "warnings": []
}
```

历史报告额外包含 `scope.target_commit`。文件读取失败或单文件 diff 失败会出现在 `files`、
`summary.files_failed` 和 `warnings` 中，此时报告为 `incomplete`、门禁失败、`score` 为 `null`。
预览成功时 `status` 为 `preview`、`score` 为 `null`、`quality_gate.status` 为 `not_evaluated`。
被排除的覆盖范围与零候选的 Git 差异单独报告，不属于失败；门禁通过也不代表语义覆盖完整。

每条 finding 的 `impact_scope` 固定为 `文件内`，表示引擎只做了单文件文本检查，跨文件影响需上下文复核；
`related` 列出同一规则在同一次评审中的其他命中位置，最多 5 条，便于合并同类问题。

不要在报告中回显密钥值或整行凭证。行号从 1 开始。引擎评分与人工复核结论必须分开呈现。

## 引擎原始结果文件

给 `review` 或 `scan` 加 `--write-report` 即可落盘引擎原始结果：

```bash
python <skill-root>/scripts/review.py review --path <repository> --format json --write-report
```

- 位置：解析出的仓库根或扫描根下的 `docs/local/代码评审/`；不在 Git 仓库时，扫描根为当前目录。
- 文件名：`review-<YYYY-MM-DD_HH-MM-SS>.engine.md`（本地时间），例如 `review-2026-11-27_15-20-17.engine.md`；UTF-8，重名时追加序号，不覆盖历史报告；写入失败按错误退出。
- 该文件是证据，不是交付报告。文件开头标注「仅作证据」；交付报告由评审者按技能模板另存为 `review-<时间戳>.md`。
- stdout 保持所选格式（text/json/sarif）不变，保存路径打印到 stderr，便于与 JSON 输出分离。
- 不加该参数时，引擎不创建目录、不写文件。
- 预览、不完整和门禁失败的结果都可以落盘，状态字段保持原值；未产生结果就失败的错误不生成报告。
- 文件结构：标题、信息块、`## 引擎确定性问题`、`## 告警`，只包含确定性检查结果。
- Markdown 只逐条列出严重、高、中三级；低与提示级命中合并为一行计数，完整明细仍保留在 JSON 的 `findings` 中。

## 退出码

- `0`：门禁通过，或预览完成且无文件读取失败；
- `1`：门禁失败、存在无法评审的候选文件、输入或配置错误、报告写入失败；
- `2`：参数解析错误（语法层面）。
