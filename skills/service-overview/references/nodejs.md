# Node.js 扫描规则

## 入口与路由

- 从 `package.json` 的 scripts/main/exports 和 `src/index|main|app|server` 找入口。
- Express/Koa/Fastify 查 `app/router.(get|post|put|delete|patch|use)`；NestJS 查 Controller 与方法装饰器；同时查 GraphQL/gRPC handler。

## 消息消费

搜索 KafkaJS、amqplib、Bull/BullMQ、NATS、Pulsar 和 Nest 微服务的 subscribe/consumer/process 装饰器或注册。

## 外部调用

搜索 axios、fetch、got、undici、gRPC client、Nest HttpService 和消息 producer。URL/服务名附环境变量或配置文件来源。

## 数据层与表名

Prisma 查 `schema.prisma` 的 `@@map/@map`；TypeORM/Sequelize 查 Entity/Table 模型参数；Mongoose 查 collection；Knex/SQL 查迁移与查询。模型名不等于表/集合名时以显式映射为准。

## 配置

读取 `.env*`、config 模块、Nest Config、`process.env`、容器环境变量和启动参数。依赖版本以 lockfile 为优先证据，只有范围版本时保留范围。


