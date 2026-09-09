# Kubernetes ConfigMap / Secret 适配器

## 检测信号

- Pod/Deployment/StatefulSet 中的 `env`、`envFrom`、`configMapKeyRef`、`secretKeyRef`、Volume。
- Spring Cloud Kubernetes 或其他 Kubernetes 配置客户端依赖。

## 必要参数

- 当前 kube-context、namespace、workload、container、service account 权限。
- ConfigMap/Secret 名称、键、挂载路径及启动命令。

## 查询方式

用 `kubectl get`/API 读取实际 workload 清单以及引用的 ConfigMap/Secret。Secret 的 `data` 需 base64 解码后写入原始临时文件，但不得在对话中显示值。

## 配置集合枚举

从指定容器枚举所有 `env`、`envFrom`、Volume/VolumeMount、projected volume 和配置客户端声明；同名资源必须带 namespace。

## 覆盖顺序

区分环境变量、挂载文件、命令行参数和应用配置文件。Kubernetes 只负责注入，最终覆盖顺序由容器启动命令和应用框架决定，需与对应应用适配器联合确认。

## 失败与恢复

context/namespace/workload 不明先询问。RBAC 禁止读取 Secret 时列出资源名和缺失权限，不生成伪值；资源不存在时核对实际 ReplicaSet/Pod 模板。


