---
name: java-coding-guide
description: 编写、修改或审查 Java 代码时使用的工程规范，覆盖代码设计、命名、异常日志、并发、数据库、安全、测试和生产级可靠性。纯文档阅读、普通排障或不涉及 Java 代码判断的问答不使用。
metadata:
  short-description: Java 编码与审查规范
---

# Java Coding Guide

在新增、修改或审查 Java 代码前应用本技能。先理解项目现有实现，再以最小影响完成需求；不得为了套用规范而重构无关存量代码。

## 优先级

1. 用户在当前任务中的明确要求。
2. 全局规则和全局运行环境约定。
3. 当前项目的构建配置、formatter、Checkstyle、既有架构约定及项目级 `AGENTS.md`；项目级 `AGENTS.md` 仅作参考，与全局规则冲突时以全局规则为准。
4. 本技能的强制规则。
5. 本技能的推荐规则。

用户明确要求与本技能的一般偏好冲突时，简短说明偏离原因后按用户要求执行。只有业务含义不明确、可能破坏数据或涉及不可逆操作时先确认。

## 工作方式

- 先检查与改动直接相关的同包实现和已有工具、常量、枚举、模板；涉及行为、公共契约、事务、并发、持久化或既有测试覆盖行为时，再检查调用方和测试，优先复用项目能力。
- 新增、修改或重构 Java 代码时，以编码习惯模板作为默认落地风格；当项目已有明确且不同的局部约定时保持项目一致，并且不得为了统一风格改写无关存量代码。
- “简洁”指职责清楚、流程直观，不指压缩行数。新增或修改的声明遵循[编码习惯模板](references/coding-habit-template.md)中的多行 JavaDoc、成员间距及 import 规则；不能把偶见的历史紧凑写法当作项目约定。
- 修改公共契约、持久化结构或并发流程时检查生产者、消费者、兼容性和失败路径。
- Java 代码修改完成后，必须说明是否建议新增或更新单元测试及原因，并询问用户是否需要生成或更新；用户确认后再修改测试文件。
- 完成后按改动风险确定最小验证方案，但不主动执行编译、测试或构建验证。说明推荐的最小验证命令、验证目的和预期影响后，询问用户是否执行；只有得到用户明确确认才可运行。多模块构建、测试跳过开关、全量构建、`package`/`install`、耗时任务或访问外部环境的细节见[测试、验证与代码审查](references/testing-and-review.md)。
- 工具或验证失败必须明确报告，不得静默跳过。
- 交付前必须完成编码习惯模板中的“变更范围风格自检”，覆盖本次全部新增和修改的 Java 片段，不只检查用户点名的类。功能检查或编译通过不能替代这项检查；不因此擅自引入 formatter、Checkstyle 或全仓格式化。

## 按需加载规则

| 触发场景 | 必读文件 |
| --- | --- |
| 改动或审查任何 Java 代码 | [coding-habit-template.md](references/coding-habit-template.md) |
| 类与方法设计、集合、时间 | [coding-and-design.md](references/coding-and-design.md) |
| 相等、包装类型、精度、集合陷阱、日期、空值 | [language-correctness.md](references/language-correctness.md) |
| 线程、锁、线程池、异步编排、可见性、性能 | [concurrency.md](references/concurrency.md) |
| 异常、日志、RPC、MQ、缓存、异步可靠性 | [exception-and-logging.md](references/exception-and-logging.md) |
| 数据库、MyBatis、事务、契约、权限、输入安全 | [persistence-and-security.md](references/persistence-and-security.md) |
| 测试、已获确认的验证、代码审查 | [testing-and-review.md](references/testing-and-review.md) |

同时涉及多个场景时读取对应多个引用，不加载无关章节。

## 不变约束

- 不新增无职责的 Service、Manager、Facade、Strategy、Factory、Context、Handler、DTO 或工具类。
- 不为单次字段赋值、简单分支、参数转发或单次读写拆碎片方法。
- 不因无关需求删改现有日志或调整其级别与打印逻辑。
- 不直接修改可重新生成的代码；只改生成源、协议、模板或生成配置。
- 不为测试扩大生产方法可见性，也不反射直测私有实现。
- 临时代码统一用 `TODO(负责人)：` + 处理计划，不新增无归属的裸 `TODO`。
