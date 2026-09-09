# Spring 本地与运行时配置适配器

## 检测信号

- `application*.yml|yaml|properties`、`bootstrap*`、`spring.config.import`、`spring.config.additional-location`。
- 启动命令中的 `--key=value`、`-Dkey=value`，部署清单中的环境变量与 `configtree:`。

## 必要参数

- 实际启动 profile、工作目录、启动命令、环境变量和挂载目录。
- `spring.config.location` / `additional-location` / `import` 的真实值。

## 查询方式

读取启动时可见的全部候选文件、命令行参数、JVM System Properties、环境变量和 configtree 文件。优先从部署脚本、容器命令或进程参数取值；只有项目文件时必须注明“仓库默认值”，不得称为线上生效值。

## 配置集合枚举

枚举默认文件、profile 文件、外部目录文件、导入文件、configtree 目录、环境变量、JVM 参数和命令行参数；同时记录每项是否在本次启动中实际加载。

## 覆盖顺序

以项目所用 Spring Boot 版本和实际 `spring.config.*` 参数为准。命令行、System Properties、环境变量、外部文件、包内文件及 profile 的相对顺序必须从版本文档或启动日志确认，不套用跨版本固定表。

## 失败与恢复

拿不到进程参数、环境变量或挂载内容时，只能输出仓库可见默认配置，并列出缺失项。profile 或导入顺序不明时停止合并。


