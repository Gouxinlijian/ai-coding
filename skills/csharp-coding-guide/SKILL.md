---
name: csharp-coding-guide
description: 编写、修改或审查 C# 代码时使用的工程规范，覆盖 .NET 设计、异步取消、资源释放、持久化、安全、测试和生产级可靠性。纯文档阅读、普通排障或不涉及 C# 代码判断的问答不使用。
metadata:
  short-description: C#/.NET 编码与审查规范
---

# C# Coding Guide

在新增、修改或审查 C# 代码前应用本技能。先理解项目现有实现，再以最小影响完成需求；不得为了套用规范而重构无关存量代码。

## 优先级

1. 用户在当前任务中的明确要求。
2. 全局规则和全局运行环境约定。
3. 当前项目的 `.editorconfig`、分析器、构建配置、既有架构约定及项目级 `AGENTS.md`；项目级 `AGENTS.md` 仅作参考，与全局规则冲突时以全局规则为准。
4. 本技能的强制规则。
5. 本技能的推荐规则。

用户明确要求与本技能的一般偏好冲突时，简短说明偏离原因后按用户要求执行。只有业务含义不明确、可能破坏数据或涉及不可逆操作时先确认。

## 工作方式

- 先检查与改动直接相关的同目录实现、现有抽象、扩展方法、Options、常量、枚举和模板；涉及行为、公共契约、事务、并发、持久化或既有测试覆盖行为时，再检查调用方和测试，优先复用项目能力。
- 新增、修改或重构 C# 代码时，以编码习惯模板作为默认落地风格；项目已有明确且不同的局部约定时保持项目一致，不为统一风格改写无关存量代码。
- 修改公共契约、数据库结构、异步流程或并发流程时检查生产者、消费者、兼容性、取消语义和失败路径。
- C# 代码修改完成后评估单元测试覆盖需求，说明是否建议新增或更新测试及原因；实际新增或修改测试前读取测试引用。
- 完成后按改动风险确定最小验证方案，但不主动执行编译、测试或构建验证。说明推荐命令、验证目的和预期影响后，询问用户是否执行；`dotnet test`、`dotnet build`、`dotnet publish`、耗时任务或访问外部环境必须单独说明。
- 工具或验证失败必须明确报告，不得静默跳过。

## 按需加载规则

- 新增、修改或重构 C# 代码，以及审查代码是否符合编码规范时，必须读取 [coding-habit-template.md](references/coding-habit-template.md)。
- 编写或重构业务代码、设计类型和方法、处理集合、时间、异步、并发或性能时，读取 [coding-and-design.md](references/coding-and-design.md)。
- 涉及异常、日志、HTTP、消息、缓存、后台任务、重试或可靠性时，读取 [exception-and-logging.md](references/exception-and-logging.md)。
- 涉及 EF Core、数据库、事务、接口契约、授权或输入安全时，读取 [persistence-and-security.md](references/persistence-and-security.md)。
- 新增或修改测试、执行已获确认的验证、或进行代码审查时，读取 [testing-and-review.md](references/testing-and-review.md)。

同时涉及多个场景时读取对应的多个引用，不加载无关章节。

## 不变约束

- 不新增无职责的 Service、Manager、Facade、Strategy、Factory、Context、Handler、DTO、Repository 或 extension helper。
- 不为单次属性赋值、简单分支、参数转发或单次读写拆出碎片方法。
- 不因无关需求删除、缩减、改写现有日志，或调整其级别和打印逻辑。
- 不直接修改可重新生成的代码；修改生成源、协议、模板或生成配置。
- 不为测试扩大生产成员可见性，也不通过反射测试私有实现。
- 临时代码使用明确处理计划的 `TODO:`，不得新增无说明的裸 `TODO`。
