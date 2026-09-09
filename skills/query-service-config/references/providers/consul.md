# Consul KV 适配器

## 检测信号

- Consul Config 客户端依赖、`spring.cloud.consul.config.*`、`consul:` 导入。
- consul-template、KV 前缀或 `CONSUL_HTTP_ADDR`。

## 必要参数

- HTTP Address、Datacenter、Namespace/Partition（企业版）、ACL Token。
- 应用名、profile、prefix、defaultContext、profileSeparator 和 format。

## 查询方式

使用 `consul kv get -recurse` 或 HTTP `/v1/kv/{prefix}?recurse`，显式携带 datacenter、namespace/partition 和 token；解码每个 Value 并保留 KV 路径。

## 配置集合枚举

按客户端配置枚举 defaultContext、应用 context、profile context 及额外 watch/prefix。FILES/KEY_VALUE/YAML/PROPERTIES 格式分别处理。

## 覆盖顺序

依据客户端版本生成的 context 列表与 PropertySource 顺序确认，profile/application/default 的覆盖顺序不能只凭路径名称推断。

## 失败与恢复

ACL 拒绝、跨 datacenter、空 prefix 或 format 不匹配时保留 HTTP 状态和路径。递归结果不完整时不得继续标准化。


