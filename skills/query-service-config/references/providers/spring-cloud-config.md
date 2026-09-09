# Spring Cloud Config 适配器

## 检测信号

- `spring-cloud-starter-config`、`spring.config.import=configserver:`。
- `spring.cloud.config.uri/name/profile/label` 或服务发现模式。

## 必要参数

- Config Server 地址或服务实例、application/name、profile、label、认证与 TLS 参数。

## 查询方式

请求 Config Server 的 `/{application}/{profile}/{label}` JSON 环境端点以获取 propertySources 和来源名；需要原始文件时再请求带文件名的资源端点。保存完整响应。

## 配置集合枚举

枚举 `spring.cloud.config.name` 的所有名称、激活 profile、label，以及响应中的全部 `propertySources`。复合应用名逐个处理。

## 覆盖顺序

以 Config Server 响应 `propertySources` 顺序和客户端本地 PropertySource 顺序为证据。不要按 Git 文件名自行排序。

## 失败与恢复

服务发现失败、label 不存在、401/403、响应为空或 `fail-fast` 行为不明时保留状态码与请求路径；不能用本地默认值冒充远端结果。


