# AWS AppConfig / SSM Parameter Store 适配器

## 检测信号

- AppConfig Agent/SDK、AppConfig application/environment/profile 标识。
- SSM Parameter Store 路径、`GetParameter(s)ByPath` 权限或配置导入。

## 必要参数

- AWS profile/role、region、account。
- AppConfig application、environment、configuration profile；或 SSM path、递归和解密选项。

## 查询方式

AppConfig 使用 Data Plane 会话或 Agent 读取当前部署配置；SSM 使用 `aws ssm get-parameters-by-path --recursive --with-decryption` 分页查询。输出中保留版本与 ARN，值只写文件。

## 配置集合枚举

枚举项目声明的所有 AppConfig profile/feature flag 和 SSM 路径；处理分页 token。不能把 AppConfig 与 Parameter Store 当成同一集合。

## 覆盖顺序

AWS 服务不定义应用内部的统一覆盖关系。依据 SDK 调用顺序、框架导入和本地配置顺序决定；无法确认时询问。

## 失败与恢复

region/account/profile 不明先询问。KMS 解密失败、分页中断、部署未完成或权限不足时保留 ARN/路径和错误码，不降级为未解密密文。


