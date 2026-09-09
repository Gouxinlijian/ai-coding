# Google Cloud Parameter Manager 适配器

## 检测信号

- Parameter Manager 客户端、`parametermanager.googleapis.com`、parameter/version 资源名。
- Terraform、部署清单或代码中的 Parameter Manager API 调用。

## 必要参数

- 当前 gcloud/ADC 身份、project、location、parameter、version（或 latest）。

## 查询方式

使用官方 gcloud 命令或 Parameter Manager API 按完整资源名读取版本 payload。记录 project/location/parameter/version，payload 只写临时文件。

## 配置集合枚举

从项目声明枚举全部 parameter；对每项解析应用实际请求的固定版本或 `latest`，并记录最终版本号。不要无授权地遍历其他 project/location。

## 覆盖顺序

Parameter Manager 只提供参数版本。多个参数与本地配置的覆盖关系由应用读取/导入顺序决定，必须从代码或部署配置确认。

## 失败与恢复

API 未启用、IAM、project/location 错误、版本禁用或 payload 格式不支持时保留完整资源名和错误码，不回退到其他项目。


