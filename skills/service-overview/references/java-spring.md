# Java / Spring 扫描规则

## 入口与路由

- `rg --files -g '*Application.java' -g '*Application.kt'` 找启动类。
- `rg -n '@(RestController|Controller|RequestMapping|GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping)' -g '*.java' -g '*.kt'` 找 HTTP 入口。
- 同时查 `@GrpcService`、Dubbo 服务注解、`@Scheduled` 和启动 Runner。

## 消息消费

搜索 `@KafkaListener`、`@RocketMQMessageListener`、`@RabbitListener`、JMS Listener 及项目封装的 Consumer 接口；主题、group 和 tag 必须取自注解、配置键或常量定义。

## 外部调用

搜索 `@FeignClient`、RestTemplate、WebClient、HTTP Client、gRPC/Dubbo 客户端和消息 Producer。服务名、URL 与 topic 附声明位置；只存在客户端定义不能证明主流程一定调用。

## 数据层与表名

- MyBatis-Plus：`rg -n '@TableName\s*\(\s*"[^"]+"' -g '*.java'`。
- JPA：查 `@Table(name=...)`；MyBatis：查 Mapper XML 的 `FROM|JOIN|INSERT INTO|UPDATE`。
- 同时查 Flyway/Liquibase/SQL 迁移。无注解实体仅可按命名策略推断，标注“推断、依据、低/中置信度”。
- 查 dynamic-datasource、`@DS`、DataSource Bean 与路由实现，区分主从和多业务库。

## 配置

读取 `application*`、`bootstrap*`、配置导入、`@ConfigurationProperties`、`@Value` 和部署参数。版本从 parent/BOM/dependencyManagement 解析；当前 POM 未直接给出时不猜。


