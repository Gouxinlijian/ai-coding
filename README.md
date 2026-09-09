# ai-coding

用于维护和公开分享 Codex 工作规则与自定义技能的版本库。仓库不包含业务应用代码，主要用于对 AI 编码规范、文档工作流和服务分析工具进行版本管理、审查与分发。

## 仓库内容

- `AGENTS.md`：Codex 全局工作约定，包括执行原则、Java 技能路由、验证范围和 CodeGraph 使用规则。
- `skills/java-coding-li`：Java 编码、设计、测试与代码审查规范。
- `skills/docs-tech-solution`：设计概要类技术文档生成技能。
- `skills/service-overview`：后端服务概览与新人上手文档生成技能。
- `skills/query-service-config`：服务实际生效配置的检测、拉取、合并和说明技能。

## 目录结构

```text
ai-coding/
|-- AGENTS.md
|-- README.md
`-- skills/
    |-- docs-tech-solution/
    |-- java-coding-li/
    |-- query-service-config/
    `-- service-overview/
```

每个技能以独立目录保存，入口为 `SKILL.md`，并按需要包含 `agents/`、`references/`、`scripts/` 或其他配套资源。目录内文件应作为一个整体维护和分发。

## 使用方式

使用前先审查目标环境中的现有配置，避免直接覆盖本地修改：

1. 将 `AGENTS.md` 合并或复制到 Codex 配置目录中的 `AGENTS.md`。
2. 将需要的完整技能目录复制到 Codex 的 `skills/` 目录。
3. 重新启动任务或会话，使新的规则和技能被重新加载。

## 源版本约定

本仓库是个人 Codex 与 Claude 技能的唯一源版本。技能改动应先提交到 `skills/` 对应目录，再同步到本地工具目录；不要直接编辑本机的 Codex 或 Claude 技能副本。

## 公开维护要求

- 不提交密码、Token、密钥、连接串或其他敏感配置。
- 可公开复用的技能不得包含真实姓名、私人称呼、本机绝对路径或其他个人信息。
- 修改技能时保持 `SKILL.md` 中的引用与实际文件同步，并在提交前运行技能格式和资源完整性检查。
