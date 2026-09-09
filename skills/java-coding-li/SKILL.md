---
name: java-coding-li
description: 编写、修改或审查 Java 代码时使用的工程规范，覆盖代码设计、命名、异常日志、并发、数据库、安全、测试和生产级可靠性。纯文档阅读、普通排障或不涉及 Java 代码判断的问答不使用。
metadata:
  short-description: Java 编码与审查规范
---

# Java Coding Li

在新增、修改或审查 Java 代码前应用本技能。先理解项目现有实现，再以最小影响完成需求；不得为了套用规范而重构无关存量代码。

## 优先级

1. 用户在当前任务中的明确要求。
2. 当前目录及项目的 `AGENTS.md`、构建配置、formatter、Checkstyle 和既有架构约定。
3. 本技能的强制规则。
4. 本技能的推荐规则。

用户明确要求与本技能的一般偏好冲突时，简短说明偏离原因后按用户要求执行。只有业务含义不明确、可能破坏数据或涉及不可逆操作时先确认。

## 工作方式

- 先扫描同包代码、调用方、已有工具、常量、枚举、模板和测试，优先复用项目能力。
- 新增、修改或重构 Java 代码时，以编码习惯模板作为默认落地风格；当项目已有明确且不同的局部约定时保持项目一致，并且不得为了统一风格改写无关存量代码。
- 仅修改需求必需内容，不顺手整理存量格式、命名、日志或结构。
- 修改公共契约、持久化结构或并发流程时检查生产者、消费者、兼容性和失败路径。
- Java 代码修改完成后必须评估单元测试覆盖需求；涉及业务规则、边界条件、异常处理、事务、并发、序列化或既有测试覆盖行为时，同步新增或更新测试。纯格式、注释及低风险机械修改可以不新增测试。
- 完成后按改动风险执行定向验证；全量构建、`package`、`install`、耗时任务或访问外部环境前先询问。
- 工具或验证失败必须明确报告，不得静默跳过。

## 按需加载规则

- 新增、修改或重构 Java 代码，以及审查代码是否符合编码规范时，必须读取 [coding-habit-template.md](references/coding-habit-template.md)。
- 编写或重构业务代码、设计类和方法、处理集合、时间或并发时，读取 [coding-and-design.md](references/coding-and-design.md)。
- 涉及异常、日志、RPC、MQ、缓存、异步或可靠性时，读取 [exception-and-logging.md](references/exception-and-logging.md)。
- 涉及数据库、MyBatis、事务、接口契约、权限或输入安全时，读取 [persistence-and-security.md](references/persistence-and-security.md)。
- Java 代码修改完成后的测试覆盖评估，以及新增或修改测试、执行验证、代码审查时，读取 [testing-and-review.md](references/testing-and-review.md)。

同时涉及多个场景时读取对应的多个引用，不加载无关章节。

## 不变约束

- 不新增无职责的 Service、Manager、Facade、Strategy、Factory、Context、Handler、DTO 或工具类。
- 不为单次字段赋值、简单分支、参数转发或单次读写拆出碎片方法。
- 不因无关需求删除、缩减、改写现有日志，或调整其级别和打印逻辑。
- 不直接修改可重新生成的代码；修改生成源、协议、模板或生成配置。
- 不为测试扩大生产方法可见性，也不通过反射直接测试私有实现。
- 临时代码标记统一使用 `TODO -Li：`，不得新增无归属的裸 `TODO`。
