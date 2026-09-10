# 安装说明

本文件用于指导 Codex、Claude 或 CodeBuddy 为当前用户安装本仓库的全局规则和 `java-coding-li` skill。根据当前运行的客户端，只执行对应章节；不要同时修改其他客户端的配置。

## 执行前确认

在执行任何下载、复制、覆盖或修改操作前，只询问用户以下一个问题，并等待回答：

> 全局规则中应该如何称呼你？例如：涛哥

记录用户提供的称呼为 `USER_TITLE`。不得自行猜测、沿用示例或从仓库内容提取称呼。

## 安装来源

- 仓库：`https://github.com/Gouxinlijian/ai-coding.git`
- 分支：`main`
- 若当前工作区已经是该仓库，使用当前工作区中已拉取的 `main` 内容；否则自行通过 Git 获取该仓库，不要求用户手动下载或复制文件。
- 安装源文件和目录不得被修改。

## 共同规则

- 覆盖已有全局规则或 skill 前，先在原路径创建带时间戳的备份。
- 全局规则源文件为仓库根目录的 `AGENTS.md`。仅在安装目标中，将所有 `涛哥` 替换为 `USER_TITLE`；不得修改源文件。
- Java skill 源目录为 `skills/java-coding-li/`。复制整个目录及全部子文件；`java-coding-li` 是公开 skill，不得替换其中任何文字、称呼或个人信息。
- 不修改其他规则、skill、插件、项目文件或 Git 配置。
- 不运行 Maven、Gradle、编译、测试或构建命令。
- 发生文件权限、Git 拉取或复制失败时，明确报告失败原因和未完成项，不得静默跳过。

## Codex

1. 将处理过称呼替换的全局规则安装到 `$CODEX_HOME/AGENTS.md`；`CODEX_HOME` 未设置时安装到 `~/.codex/AGENTS.md`。
2. 将完整 `skills/java-coding-li/` 安装到 `$CODEX_HOME/skills/java-coding-li/`；`CODEX_HOME` 未设置时安装到 `~/.codex/skills/java-coding-li/`。
3. 校验目标全局规则除 `USER_TITLE` 替换外与源 `AGENTS.md` 一致；递归校验 skill 每个文件的 SHA-256 与源目录一致。

## Claude

1. 将处理过称呼替换的全局规则安装到 `~/.claude/CLAUDE.md`。
2. 将完整 `skills/java-coding-li/` 安装到 `~/.claude/skills/java-coding-li/`。
3. 校验目标全局规则除 `USER_TITLE` 替换外与源 `AGENTS.md` 一致；递归校验 skill 每个文件的 SHA-256 与源目录一致。

## CodeBuddy

1. 创建或更新 `~/.codebuddy/rules/global-workflow.md`。
2. 在目标文件顶部写入以下 frontmatter，再写入处理过称呼替换的 `AGENTS.md` 全文：

   ```yaml
   ---
   description: 个人全局工作约定
   alwaysApply: true
   enabled: true
   ---
   ```

3. 将完整 `skills/java-coding-li/` 安装到 `~/.codebuddy/skills/java-coding-li/`。
4. 校验全局规则：除 CodeBuddy frontmatter 和 `USER_TITLE` 替换外，其余内容与源 `AGENTS.md` 一致；递归校验 skill 每个文件的 SHA-256 与源目录一致。

## 生效方式

安装完成后，安装 AI 必须告知用户按当前客户端执行以下操作：

- **Codex**：结束当前任务并新建一个任务或会话；新会话会重新加载全局 `AGENTS.md` 和已安装 skill。若新会话中未识别 `java-coding-li`，完全退出并重新打开 Codex 后再新建会话。
- **Claude**：结束当前对话并新建对话或重新启动 Claude；在新对话中再请求 Java 代码编写、修改或审查，使其重新加载 `CLAUDE.md` 和 skill。
- **CodeBuddy**：新建一个聊天会话。若新会话仍未加载规则或发现 skill，重启 CodeBuddy 后新建会话；然后询问“当前应用了哪些规则和 skill？”确认 `global-workflow` 与 `java-coding-li` 已生效。

不得声称当前已打开的会话会自动加载刚安装的规则或 skill。

## 交付

完成后报告：

1. 使用的仓库提交号和客户端类型。
2. 用户称呼、备份路径和安装路径。
3. 全局规则与 skill 的校验结果。
4. 按“生效方式”章节给出当前客户端的明确下一步，并说明规则和 skill 不会自动注入当前已打开的会话。
