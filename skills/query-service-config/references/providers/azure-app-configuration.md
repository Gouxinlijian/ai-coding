# Azure App Configuration 适配器

## 检测信号

- Azure App Configuration SDK/Starter、endpoint/connection string 配置。
- Key Vault 引用、label/filter、feature flag 声明。

## 必要参数

- Subscription/tenant（需要时）、endpoint、身份方式、key filter、label filter、snapshot。

## 查询方式

使用当前 Azure CLI 身份或 SDK，通过 endpoint 枚举 key-values；同时记录 key、label、content type、etag。Key Vault 引用按应用身份解析，不能只保存引用 URI 后声称已生效。

## 配置集合枚举

枚举代码和配置中全部 Select/filter/label、snapshot、feature flag 与 Key Vault 引用；无 label 与具体 label 分开保存。

## 覆盖顺序

依据客户端注册的 Select 顺序、label 选择和本地 provider 顺序确认。同 key 不同 label 的选择不是简单按时间覆盖。

## 失败与恢复

endpoint/tenant 不一致、RBAC、私有网络、Key Vault 权限或引用解析失败时保留 key 和错误类型，值不输出到对话。


