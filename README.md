# ai-coding

用于维护和公开分享 AI 助手工作规则与自定义技能的版本库。仓库不包含业务应用代码，主要用于规则的版本管理、审查与分发；可用技能清单以 `skills/` 目录为准。

## 仓库内容

- `AGENTS.md`：全局工作约定，包括执行原则、技能路由、文档输出位置、验证范围和代码图谱使用规则。
- `INSTALL.md`：安装流程说明，定义技能清单读取、用户勾选、客户端选择、安装与校验步骤。
- `skills/`：可按需安装的技能集合。每个一级子目录是一个独立技能，入口为 `SKILL.md`；可安装技能以目录实际内容为准。

### Java 编码与审查

[`java-coding-guide`](skills/java-coding-guide/SKILL.md) 位于 `skills/java-coding-guide/`，用于新增、修改或审查 Java 代码。提供代码设计、命名、异常日志、并发、数据库、安全和测试规范，优先沿用项目已有约定，适合日常开发和变更审查。

### C# 编码与审查

[`csharp-coding-guide`](skills/csharp-coding-guide/SKILL.md) 位于 `skills/csharp-coding-guide/`，用于新增、修改或审查 C#/.NET 代码。覆盖类型设计、异步取消、资源释放、持久化、安全、测试与可靠性，适合在现有 .NET 项目中交付和审查变更。

### 代码评审

[`ai-code-review`](skills/ai-code-review/SKILL.md) 位于 `skills/ai-code-review/`，用于评审 Git 工作区变更、指定提交、分支差异或整目录代码。先由引擎做确定性筛选与静态检查，再结合调用链与框架配置复核，按严重程度输出中文评审报告，可按需保存到被评审项目的 `docs/local/代码评审/`。结果基于启发式规则，需结合代码上下文确认。

### 测试用例生成

[`testcase-generator`](skills/testcase-generator/SKILL.md) 位于 `skills/testcase-generator/`，用于根据已确认的需求文档和测试范围，编写页面功能与交互用例，可交付 Markdown 或 XMind。仅在用户明确点名时启用，不用于生成单元测试代码或执行测试。

### 技术方案文档生成

[`docs-tech-solution`](skills/docs-tech-solution/SKILL.md) 位于 `skills/docs-tech-solution/`，用于将已确认的需求和代码证据整理成概要设计文档，适合接口改造、数据结构变更、服务迁移或系统集成的设计评审。仅在用户明确指定时启用，不用于生成需求文档或直接改代码。

### 后端服务概览

[`service-overview`](skills/service-overview/SKILL.md) 位于 `skills/service-overview/`，用于梳理后端服务定位、模块职责、主要入口、数据层、外部依赖和核心业务流程，生成结论可追溯的中文概览，适合新人上手和服务交接。

### 查询服务配置

[`query-service-config`](skills/query-service-config/SKILL.md) 位于 `skills/query-service-config/`，用于查询和核对服务实际生效的配置。先识别项目使用的配置来源，再按已确认的加载优先级合并并导出 YAML 和 Properties；适合排查配置覆盖问题或整理环境配置，对话摘要会脱敏。

## 目录结构

```text
ai-coding/
|-- AGENTS.md
|-- INSTALL.md
|-- README.md
`-- skills/
    `-- <技能名>/
        |-- SKILL.md
        `-- 其余资源文件（按需）
```

技能目录名即技能名，安装时以 `skills/` 下实际存在的目录为准；目录内文件作为一个整体维护和分发。

## 安装

### 通用安装提示词

要浏览技能清单或一次安装多个技能，复制下面的提示词发送给当前 AI 助手：

```text
请从 https://github.com/Gouxinlijian/ai-coding.git 获取本仓库（当前工作区已是该仓库则直接使用），阅读 README.md 和 INSTALL.md，先扫描 skills/ 列出全部技能的名称与用途，再用选择题让我勾选要安装哪些技能、以及要安装到哪些客户端（Codex / Claude / CodeBuddy / Qoder）。在我明确选择之前，不要安装任何内容，也不要替我预设技能、客户端或安装范围。
```

AI 会先列出技能清单，再询问你的称呼，然后按你的勾选完成拉取、备份、安装和校验；未勾选的技能和客户端不会被改动。全局规则中包含 Java、C# 等编码技能的路由，未安装对应技能时该路由不会生效，不影响其他技能。

### 按技能安装提示词

只装一个技能时，复制对应代码块发送给当前 AI 助手。提示词只指定技能；目标客户端仍由你选择。安装与技能使用分开：确认后才复制文件，不在安装时执行技能任务。

#### 安装 `java-coding-guide`

```text
1. 我只想安装 java-coding-guide。优先使用当前 ai-coding 工作区，否则从 https://github.com/Gouxinlijian/ai-coding.git 获取仓库。阅读 INSTALL.md，检查 skills/java-coding-guide/ 下的 SKILL.md 和引用文件。
2. 请让我选择目标客户端（Codex / Claude / CodeBuddy / Qoder），列出安装路径和已有副本，等我确认。若需要新增或更新 Java 自动加载规则，请另行确认，不要默认修改全局规则。
3. 确认后按 INSTALL.md 整目录安装并逐文件校验 SHA-256，告知如何在新会话中确认技能已加载。不要运行 Java 编译或测试。
```

#### 安装 `csharp-coding-guide`

```text
1. 我只想安装 csharp-coding-guide。优先使用当前 ai-coding 工作区，否则从 https://github.com/Gouxinlijian/ai-coding.git 获取仓库。阅读 INSTALL.md，检查 skills/csharp-coding-guide/ 下的 SKILL.md 和引用文件。
2. 请让我选择目标客户端（Codex / Claude / CodeBuddy / Qoder），列出安装路径和已有副本，等我确认。若需要新增或更新 C# 自动加载规则，请另行确认，不要默认修改全局规则。
3. 确认后按 INSTALL.md 整目录安装并逐文件校验 SHA-256，告知如何在新会话中确认技能已加载。不要运行 .NET 构建或测试。
```

#### 安装 `ai-code-review`

```text
1. 我只想安装 ai-code-review。优先使用当前 ai-coding 工作区，否则从 https://github.com/Gouxinlijian/ai-coding.git 获取仓库。阅读 INSTALL.md，检查 skills/ai-code-review/ 下的 SKILL.md、脚本和规则说明。
2. 请让我选择目标客户端（Codex / Claude / CodeBuddy / Qoder），列出安装路径、已有副本和使用前置条件（Python 3.9+；Git 差异审查还需 Git），等我确认。不要自动安装依赖或修改全局规则。
3. 确认后按 INSTALL.md 整目录安装并逐文件校验 SHA-256，告知如何在新会话中确认技能已加载。不要在安装时执行审查或配置提交钩子。
```

#### 安装 `testcase-generator`

```text
1. 我只想安装 testcase-generator。优先使用当前 ai-coding 工作区，否则从 https://github.com/Gouxinlijian/ai-coding.git 获取仓库。阅读 INSTALL.md，检查 skills/testcase-generator/ 下的 SKILL.md、参考资料与 XMind 转换脚本。
2. 请让我选择目标客户端（Codex / Claude / CodeBuddy / Qoder），列出安装路径和已有副本，等我确认。不要修改全局规则或设置自动触发。
3. 确认后按 INSTALL.md 整目录安装并逐文件校验 SHA-256，告知我在新会话中如何点名启用该技能，以及导出 XMind 需要 Python。不要在安装时生成用例。
```

#### 安装 `docs-tech-solution`

```text
1. 我只想安装 docs-tech-solution。优先使用当前 ai-coding 工作区，否则从 https://github.com/Gouxinlijian/ai-coding.git 获取仓库。阅读 INSTALL.md，检查 skills/docs-tech-solution/ 下的 SKILL.md、写作规则和文档模板。
2. 请让我选择目标客户端（Codex / Claude / CodeBuddy / Qoder），列出安装路径和已有副本，等我确认。不要修改全局规则或设置自动触发。
3. 确认后按 INSTALL.md 整目录安装并逐文件校验 SHA-256，告知我在新会话中如何点名启用该技能。不要在安装时生成设计文档。
```

#### 安装 `service-overview`

```text
1. 我只想安装 service-overview。优先使用当前 ai-coding 工作区，否则从 https://github.com/Gouxinlijian/ai-coding.git 获取仓库。阅读 INSTALL.md，检查 skills/service-overview/ 下的 SKILL.md、文档模板和语言适配说明。
2. 请让我选择目标客户端（Codex / Claude / CodeBuddy / Qoder），列出安装路径和已有副本，等我确认。不要安装额外工具或修改全局规则。
3. 确认后按 INSTALL.md 整目录安装并逐文件校验 SHA-256，告知我在新会话中如何请求梳理后端服务。不要在安装时扫描业务项目或生成概览。
```

#### 安装 `query-service-config`

```text
1. 我只想安装 query-service-config。优先使用当前 ai-coding 工作区，否则从 https://github.com/Gouxinlijian/ai-coding.git 获取仓库。阅读 INSTALL.md，检查 skills/query-service-config/ 下的 SKILL.md、配置脚本和来源适配说明。
2. 请让我选择目标客户端（Codex / Claude / CodeBuddy / Qoder），列出安装路径、已有副本和使用前置条件（Python；查询外部配置源时按实际来源准备工具和权限），等我确认。不要自动安装依赖或修改全局规则。
3. 确认后按 INSTALL.md 整目录安装并逐文件校验 SHA-256，告知如何在新会话中使用。不要在安装时连接配置中心、索取凭据或导出配置。
```

## 更新

之前安装过、需要同步仓库最新版本时，复制下面这一条：

```text
请从 https://github.com/Gouxinlijian/ai-coding.git 获取本仓库最新版本（当前工作区已是该仓库则先拉取更新），阅读 README.md 和 INSTALL.md 的更新流程。先对比本机已安装技能与 skills/ 目录，列出「技能名｜本机状态｜与仓库差异」清单，再用选择题让我勾选要更新哪些技能、更新到哪些客户端（Codex / Claude / CodeBuddy / Qoder），并单独确认是否同时更新全局规则。更新前先备份，在我明确选择之前不要覆盖任何内容，也不要替我预设技能、客户端或更新范围。
```

更新只覆盖你勾选的内容：未勾选的技能、仅本机存在的技能、其他客户端的配置都不会被删除或修改；覆盖前的备份可用于回滚。

## 源版本约定

本仓库是个人 Codex、Claude、CodeBuddy 与 Qoder 技能的唯一源版本。技能改动应先提交到 `skills/` 对应目录，再同步到本地工具目录；不要直接编辑本机的各客户端技能副本。

## 公开维护要求

- 不提交密码、Token、密钥、连接串或其他敏感配置。
- 可公开复用的技能不得包含真实姓名、私人称呼、本机绝对路径或其他个人信息。
- 新增或修改技能时保持 `SKILL.md` 和本文件中的技能链接与实际文件同步；完整技能清单以 `skills/` 目录为准。
