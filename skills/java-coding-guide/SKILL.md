---
name: java-coding-guide
description: 编写、修改或审查 Java 代码时使用的工程规范，覆盖代码设计、命名、可读性、异常日志、并发、数据库、安全、测试和生产级可靠性。纯文档阅读、普通排障或不涉及 Java 代码判断的问答不使用。
metadata:
  version: 1.1.0
  short-description: Java 编码与审查规范
---

# Java Coding Guide

在新增、修改或审查 Java 代码前应用本技能。先理解项目现有实现，再以最小影响完成需求；不得为了套用规范而重构无关存量代码。

## 优先级

1. 用户明确要求。
2. 全局规则和运行环境约定。
3. 项目约定（构建、formatter、Checkstyle、架构、项目级 `AGENTS.md`）；项目级 `AGENTS.md` 与全局规则冲突时以全局为准。
4. 本技能强制规则。
5. 本技能推荐规则。

用户要求与本技能偏好冲突时，说明偏离原因后按用户要求执行；只有业务含义不明确、可能破坏数据或不可逆操作时先确认。

规则是默认值，不是填空模板：明显不适用时优先保证可读性和业务表达，并说明偏离原因；不为满足规则制造无意义注释、Builder 或分层。动手顺序：意图与正确性 → 清晰 → 性能，不为技巧牺牲可读性。

## 工作方式

- 先看同包实现、工具、常量、枚举和模板，优先复用；涉及行为、公共契约、事务、并发、持久化或既有测试覆盖行为时，再查调用方和测试。
- 以模板为默认风格；动笔前沿用同包可读实现的命名、注释密度、分层和段落节奏，模板只兜底。项目已有约定时保持一致，不为统一风格改写无关存量。
- 改存量沿用现有分层，按最小改动处理；新建模块允许完整分层，但必须复用项目公共能力（返回协议、业务异常、分页、审计字段），先出骨架和口径再写实现。
- 非平凡改动先列 3~5 个业务阶段和调用顺序，再落代码；不边写边补结构，不把调试代码留在最终代码。
- 修改公共契约、持久化结构或并发流程时检查生产者、消费者、兼容性和失败路径；“简洁”指职责清楚、流程直观，不指压缩行数。
- 关键分支、提前返回、业务异常和状态流转必须有 INFO 日志，记录业务标识和原因；见[异常、日志与可靠性](references/exception-and-logging.md)。
- 完成后说明是否建议补测试并询问；验证遵循全局规则，Java 命令、多模块构建、跳过开关、`package`/`install`、外部环境细节见[测试、验证与代码审查](references/testing-and-review.md)。
- 交付前完成模板的“变更范围风格自检”，覆盖本次全部新增和修改，不因功能通过而跳过，也不擅自引入 formatter、Checkstyle 或全仓格式化。

## 开工前

非平凡改动先探测项目现状并定口径，结论写进交付说明；项目已有约定时沿用，没有才用模板兜底。

- **探测**：同包 Service/Controller 的注入、日志、返回包装；Mapper 与 resources 的 SQL 位置、XML 命名、分页封装；公共能力（业务异常、全局异常处理、转换工具、Lombok）；数据层（主键、逻辑删除、审计字段、时间来源）。每项看 2~3 个同类文件取多数写法。
- **定口径**：时间（应用或数据库、是否同源）、计数（原子增减或重算、减到 0 的语义、父删子留怎么算）、状态（流转、终态、重复操作语义）、幂等（键、唯一约束、冲突重试还是回读）、分页（页码或游标、是否需要总数）。新建模块必做，改存量按需。

## 按需加载规则

按代码特征命中，不按任务话题判断；一次改动可能命中多个文件，全部读取。

| 代码里出现 | 必读文件 |
| --- | --- |
| 任何 Java 改动 | [coding-habit-template.md](references/coding-habit-template.md) |
| 新增或重构业务代码、需要风格对照 | [human-style-examples.md](references/human-style-examples.md)、[coding-and-design.md](references/coding-and-design.md) |
| 类/方法设计、集合、时间、相等、包装类型、精度、日期、空值 | [coding-and-design.md](references/coding-and-design.md)、[language-correctness.md](references/language-correctness.md) |
| `@Transactional`、线程池、`Retry`、`afterCommit`、`synchronized`、定时任务 | [concurrency.md](references/concurrency.md)、[exception-and-logging.md](references/exception-and-logging.md) |
| 错误码、异常转换、全局异常处理、日志埋点、RPC/MQ/缓存 | [exception-and-logging.md](references/exception-and-logging.md) |
| Mapper、XML、DDL、索引、分页查询、契约与权限 | [persistence-and-security.md](references/persistence-and-security.md) |
| 交付或提交前 | [testing-and-review.md](references/testing-and-review.md) 的「交付前自检」 |

同时涉及多个场景时读取对应多个引用，不加载无关章节。

## 不变约束

红线见[编码习惯模板](references/coding-habit-template.md)顶部；命名、注释、数据对象和排版规则也以该模板为准。无法按默认做法实现时显式声明偏离项、原因和替代验证，不静默改写法。
