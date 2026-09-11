# 编码 Skill 命名与 C# 扩展设计

## 目标

将公开 Java skill 的名称从带个人后缀的 `java-coding-li` 迁移为 `java-coding-guide`，补充全局 Markdown 文档输出目录约定，并创建结构对等、语言语义适配的 `csharp-coding-guide`。

## 范围

本次包含：

- Java skill 目录、skill 名称和仓库引用的迁移。
- 全局规则中新增 Markdown 业务文档的输出位置。
- C#/.NET 编码、设计、可靠性、持久化、安全、测试与审查 skill。
- Codex 和 Claude 的本地规则与 skill 同步。

本次不改动：

- `TODO -Li` 标记。
- `coding-habit-template.md` 的既有编码风格和 JUnit 4 + Mockito 示例。
- 已确认的“不主动执行编译、测试或构建”策略。
- CodeBuddy 的已定义安装机制；`INSTALL.md` 仅更新名称和安装目录。

## Java Skill 迁移

源目录由 `skills/java-coding-li/` 重命名为 `skills/java-coding-guide/`，其 `SKILL.md` frontmatter 中的 `name` 同步改为 `java-coding-guide`。

仓库中的 `AGENTS.md`、`README.md`、`INSTALL.md` 和所有相关文字引用同步使用新名称及目录。安装端的 Codex、Claude skill 目录也同步重命名。迁移完成后不保留旧目录，避免同一规则被两个名称发现和加载。

迁移仅改变公开标识和路径，不改变 Java 规则内容、按需加载路由或 `TODO -Li` 标记。

## 文档输出约定

全局规则新增以下约定：新建或输出的 Markdown 业务文档必须放在当前项目的 `docs/local/{具体业务范围}/` 下。业务范围目录使用能表达领域的名称，例如黑名单管理文档放在 `docs/local/黑名单管理/`。

该约定只约束任务产出的业务文档。仓库根目录的 `README.md`、`AGENTS.md`、`INSTALL.md`、skill 的 `SKILL.md` 和引用文件属于配置或项目元文件，继续位于既有路径，不迁移到 `docs/local/`。

## C# Skill 结构

创建 `skills/csharp-coding-guide/`，采用与 Java skill 相同的三层结构：

```text
csharp-coding-guide/
|-- SKILL.md
|-- agents/
|   `-- openai.yaml
`-- references/
    |-- coding-habit-template.md
    |-- coding-and-design.md
    |-- exception-and-logging.md
    |-- persistence-and-security.md
    `-- testing-and-review.md
```

入口文件负责优先级、最小改动、按需引用路由、不主动验证和不变约束。默认加载 C# 编码习惯模板；业务代码、集合、时间、并发或设计改动加载编码与设计；异常、日志、HTTP、消息、缓存、异步或可靠性加载可靠性引用；EF Core、事务、接口契约、授权或输入安全加载持久化与安全引用；实际测试修改、已确认验证或代码审查加载测试引用。

## C# 专项规则

规则保持 Java skill 的工程目标，但使用 .NET 语义：

- ASP.NET Core 分层、DI 生命周期、Options 模式、Controller 与 Application Service 边界。
- `async`/`await`、`CancellationToken` 传递、受控后台任务、异常传播和并发安全。
- nullable reference types、`IDisposable`/`IAsyncDisposable`、`using`、集合和 LINQ 副作用边界。
- `decimal` 精度、`DateTimeOffset` 与时区、枚举和固定值复用。
- EF Core 查询、跟踪策略、事务、乐观并发、批量操作、SQL 参数化和迁移风险。
- 授权、输入校验、敏感信息、日志脱敏、HTTP/MQ/缓存失败语义。
- xUnit、NUnit、MSTest 和 Mock 框架均遵循目标项目现状；测试与构建命令一律在用户明确确认后才执行。

不复制 Java 专属框架和工具细节，例如 MyBatis、Spring 注解、JUnit 4 Runner 或 Java 的 `TODO -Li` 标记。

## 验证与同步

完成实现后：

1. 使用 skill 校验器检查两个 skill 的结构、frontmatter 和引用完整性。
2. 使用 `git diff --check` 检查变更格式。
3. 递归比较仓库、Codex、Claude 中两个 skill 的 SHA-256，确认每个文件一致。
4. 比较仓库与 Codex、Claude 的全局规则，允许目标环境只存在用户称呼替换差异。
5. 不运行 Maven、Gradle、`dotnet build`、测试或其他编译构建命令。
