# Go 扫描规则

## 入口与路由

- `rg --files -g 'go.mod' -g 'main.go'` 确认模块和入口。
- 搜索 Gin/Echo/Fiber/Chi/标准库的路由注册，以及 gRPC `Register*Server`。
- 从 `cmd/` 下不同 main 区分多个可部署服务。

## 消息消费

搜索 Sarama、Kafka-go、NATS、RabbitMQ、Pulsar、NSQ 的 Consume/Subscribe/Handler 注册。主题和 consumer group 附常量或配置来源。

## 外部调用

搜索 `http.Client`、Resty、gRPC `New*Client`、消息 Producer 和内部 SDK 初始化。以构造函数到业务调用的链路证明实际使用。

## 数据层与表名

GORM 查 `TableName() string`、`Table(...)` 和模型迁移；sqlx/database/sql 查 SQL 字面量与查询构造器；同时扫描 migrations。仅按 struct 名推断时明确标低置信度。

## 配置

读取 YAML/TOML/JSON、环境变量、flag、Viper/Koanf/Envconfig 初始化。追踪默认值、文件、环境变量和命令行的加载顺序。


