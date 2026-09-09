# Vault KV 适配器

## 检测信号

- Vault 客户端依赖、`spring.cloud.vault.*`、`vault://`、Vault Agent 模板。
- `VAULT_ADDR`、认证角色、KV mount/path 声明。

## 必要参数

- Address、Namespace、认证方式与必要角色参数、KV mount、KV 版本、secret path。

## 查询方式

优先复用当前已认证的 Vault CLI/Agent；用 `vault kv get -format=json -mount={mount} {path}` 或等价 API 查询。不要把 token 写入命令文本或摘要。

## 配置集合枚举

从应用配置枚举 generic/application、应用名、profile、database 等全部 backend/context；KV v2 必须区分 mount 与 `data/metadata` API 路径。

## 覆盖顺序

依据应用客户端的 backend/context 顺序、profile 和本地 PropertySource 顺序确认。Vault 返回版本号用于追溯，不代表覆盖优先级。

## 失败与恢复

认证过期、403、mount 版本错误、路径不存在或 seal 状态异常时保留非敏感错误信息。不得尝试其他身份或扫描无关路径。


