# Nacos 适配器

## 检测信号

- Nacos Config 客户端依赖、`spring.cloud.nacos.config.*`、`nacos.config.*`。
- `spring.config.import=nacos:` 或扩展配置、共享配置列表。

## 必要参数

- Server Address、Namespace ID、Group、DataId、用户名/密码或 AccessKey。
- 应用名、profile、文件扩展名、shared-configs、extension-configs 和刷新配置。

## 查询方式

使用项目已有 Nacos CLI、OpenAPI 或客户端参数查询。请求必须显式携带 tenant(namespace)、group 和 dataId；响应分别保存为原始文件。

## 配置集合枚举

根据 `spring.application.name`、profile、file-extension 推导默认 DataId，再枚举 import、shared-configs、extension-configs 中每个 DataId/Group。不能只拉默认 DataId。

## 覆盖顺序

根据所用 Spring Cloud Alibaba/Nacos 客户端版本、import 顺序以及 shared/extension/default 配置顺序确认。项目显式声明优先于通用经验。

## 失败与恢复

Namespace 名称与 ID 不得混用。DataId 返回空、403、鉴权插件差异或版本规则不明时报告请求三元组并停止该集合合并。


