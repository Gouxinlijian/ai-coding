# Apollo 适配器

## 检测信号

- Apollo 客户端依赖、`app.id`、`apollo.meta`、`apollo.bootstrap.*`、`apollo.properties`。
- 仅出现普通 `app.id` 不足以单独确认，必须再有 Apollo 依赖或配置键。

## 必要参数

- 确认项目使用 Apollo 后，最高优先级读取 `~/apollo.properties`（即当前用户目录下的 `apollo.properties`）。
- 只解析未被 `#` 或 `!` 注释的活动项：`config` 作为 Meta/Config Service 地址，`env` 作为目标环境；同名活动项以后出现的值为准。
- 主机文件缺失或缺少某个字段时，才从项目配置、环境变量、JVM 参数补充对应字段。发生冲突时记录各来源，但以主机文件的活动值为准。
- Meta/Config Service 地址、AppId、环境、集群、鉴权信息。
- `apollo.bootstrap.namespaces`、公共 namespace 关联和格式。

## 查询方式

先读取 `~/apollo.properties`，取得 `config`、`env` 后再选择 Apollo OpenAPI/Portal API 或 Config Service API。按该环境、实例真实集群和 namespace 请求并把每个响应保存为独立原始文件；不得固定 `default` 集群。

## 配置集合枚举

先从 bootstrap 配置和 Apollo API 枚举应用私有、公共关联以及动态增加的全部 namespace；记录 namespace 名、格式、发布版本与关联关系。

## 覆盖顺序

依据客户端 bootstrap namespace 顺序、公共/私有 namespace 关系和 Apollo 客户端版本确认。相同键的覆盖结论必须引用实际 namespace 顺序或客户端规则。

## 失败与恢复

主机文件不存在或未同时取得 `config`、`env` 时，明确列出缺失字段和采用的回退来源。环境与 AppId 后缀冲突、namespace 无权限、未发布或集群不存在时保留原始响应并询问。缺少任一已配置 namespace 时不得声称完整。

