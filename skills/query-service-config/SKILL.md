---
name: query-service-config
description: 当用户需要查询、拉取、核对或导出某个服务当前实际生效的配置时使用。适用于本地配置、环境变量、配置中心、容器平台和云配置服务；用户提到“拉配置”“在线配置”“当前配置”“生效配置”“服务配置”“有哪些配置”时应触发。
---

# 查询服务配置

## 目标

识别当前项目真正使用的配置来源，只读取命中的适配器，拉取各来源的实际配置，并按真实加载优先级合并为语义一致的 YAML 与 Properties 文件。

## 核心约束

- 先检测再查询，不因为机器上存在某个客户端就判定项目使用它。
- 项目确认使用 Apollo 后，优先读取 `~/apollo.properties` 中活动的 `config`、`env`；项目配置、环境变量和 JVM 参数仅补充缺失字段。
- 只读取命中的适配器；未命中的配置源不查询、不试探。
- 多来源并存时必须依据框架、部署清单或配置导入顺序确定覆盖关系。
- 无法确认覆盖顺序、环境、应用标识或配置集合时暂停并询问，不猜测。
- 保留来源证据和原始错误；失败后不得静默切换到无关适配器。
- 双格式输出保证键值语义一致；YAML 必须保留原始嵌套层级和列表，Properties 使用点号和列表索引表达同一路径。
- 配置注释必须说明配置的具体业务作用；源码引用位置只作为内部证据，不得作为最终注释。

## 执行流程

### 1. 检测来源

在项目根执行：

```bash
python {SKILL_DIR}/scripts/detect_config_source.py --project {PROJECT_ROOT}
```

脚本输出命中的来源、证据、置信度和建议适配器。结合依赖文件、配置导入、部署清单、启动参数和环境变量复核结果；单个模糊关键词不能作为唯一证据。

Apollo 命中结果还必须包含主机级 `apollo.properties` 的读取状态、`config`、`env` 和缺失字段。主机文件中的活动值具有最高识别优先级，注释行不参与解析。

### 2. 路由适配器

仅按检测结果读取 `references/providers/` 中对应文件：

| 来源 | 适配器 |
|---|---|
| Spring 本地文件、环境变量、JVM 参数、configtree | `spring-local.md` |
| Apollo | `apollo.md` |
| Nacos | `nacos.md` |
| Spring Cloud Config | `spring-cloud-config.md` |
| Kubernetes ConfigMap / Secret | `kubernetes.md` |
| Consul KV | `consul.md` |
| Vault KV | `vault.md` |
| AWS AppConfig / SSM Parameter Store | `aws-config.md` |
| Azure App Configuration | `azure-app-configuration.md` |
| Google Cloud Parameter Manager | `gcp-parameter-manager.md` |

每个适配器必须闭环完成：确认必要参数、枚举全部配置集合、查询原始内容、说明覆盖顺序，并在失败时给出可恢复信息。

### 3. 拉取并记录来源

将每个配置集合保存为临时原始文件，同时记录来源类型、环境、应用、集群、命名空间或参数路径，以及查询命令/API、退出状态、优先级证据、拉取时间和版本/标签。

临时文件扩展名必须与配置集合格式一致。扩展名缺失、由接口固定生成或与内容冲突时，同时依据配置集合元数据和内容特征确认 JSON、YAML、Properties 格式，不得仅按文件名选择解析器。

不要在对话中打印完整配置。查询产生的敏感值原样写入目标文件，摘要统一脱敏。

### 4. 标准化与合并

`--source` 按低优先级到高优先级排列，后面的来源覆盖前面的同名键：

```bash
python {SKILL_DIR}/scripts/normalize_config.py \
  --source 本地默认={PATH_1} \
  --source 配置中心={PATH_2} \
  --out-properties docs/config/_config.properties \
  --out-yaml docs/config/_config.yml
```

YAML 输出必须是标准嵌套对象和列表，禁止输出扁平键 YAML。Properties 对应路径使用点号和索引，例如 YAML 中 `aws.mail.configs` 的第一项字段对应 `aws.mail.configs[0].accessKeyId`。解析明显包含缩进层级或 `- key: value` 列表项的内容时，即使临时文件后缀为 `.properties`，也必须按 YAML 处理。

若来源顺序没有代码或部署证据，停止合并并询问用户。解析失败、YAML 重复键或无法无歧义转换时，报告具体文件与节点，不丢弃内容。

### 5. 分析具体业务作用并补充注释

对每个配置键先定位绑定字段或读取入口，再继续追踪字段在业务代码中的调用链，直到能回答“这个值控制、限制、指定或影响什么”。只找到 `@Value`、`@ConfigurationProperties` 或读取 API 不算完成。

重点识别：

- 开关：找到实际条件分支，说明开启和关闭分别改变什么行为。
- 阈值、数量、时间：说明限制对象、单位，以及达到阈值后的行为。
- Topic、Consumer Group、队列、路由键：说明对应的消息用途、生产或消费方向，以及对消费隔离、进度或路由的影响。
- 地址、路径、资源标识：说明连接的系统或选择的资源，以及被哪个业务环节使用。
- 策略、模式、枚举：说明每个有效值对应的业务差异。

根据已确认的调用链生成临时 `docs/config/_config-descriptions.json`。值必须是简洁中文业务说明，不写源码路径、类名清单或“直接引用”。例如：

```json
{
  "feature.enabled": "控制功能任务是否启用；true 时执行任务，false 时跳过。",
  "message.consumer-group": "指定任务消息消费者所属的 Consumer Group，用于隔离消费进度并协调同组实例分担消息。"
}
```

```bash
python {SKILL_DIR}/scripts/annotate_config.py \
  --properties docs/config/_config.properties \
  --project {PROJECT_ROOT} \
  --descriptions docs/config/_config-descriptions.json \
  --output docs/config/_config.annotated.properties
```

原始有效注释优先保留。源码路径、字段名和调用位置仅用于支撑分析，不得把源码路径写入最终注释。无法从当前仓库、依赖源码或明确文档确认具体行为时，标记“未确认具体作用（需继续分析配置绑定后的业务调用链）”，禁止只按键名或配置值猜业务含义。

### 6. 版本保存

应用标识优先使用配置系统的 app/service 标识，其次使用 `spring.application.name`、模块名。保存到：

```text
docs/config/{appId}-config.yml
docs/config/{appId}-config.properties
```

首次写入不带版本号。再次拉取时，先将现有正式文件备份为下一个 `-v{N}`，再把已完成标准化和注释的临时文件移入正式位置。两个格式必须成对备份、成对替换。

### 7. 输出摘要

只输出：命中来源及证据、环境与应用标识、配置集合数量、键数量、覆盖数量、无法确认项和文件路径。密码、令牌、密钥、连接串及疑似凭据值显示为 `***`。

## 失败处理

| 场景 | 处理 |
|---|---|
| 未识别来源 | 列出已检查位置和缺失证据，停止 |
| 命中多个来源 | 读取全部命中适配器，按真实加载链处理 |
| 环境或应用标识冲突 | 展示冲突值与来源，询问用户 |
| 权限/网络/客户端失败 | 保留原始错误、命令和参数名，提示缺少的授权或工具 |
| 配置集合枚举不完整 | 不生成“完整配置”，明确缺少的集合 |
| 覆盖顺序不明 | 不合并，询问用户 |
| 格式转换失败 | 保留原始文件，报告失败节点 |

## 完成检查

- 检测证据与所选适配器一致。
- 每个命中来源的配置集合已完整枚举。
- 合并顺序有可引用证据，覆盖统计可追溯。
- Properties 每个键前是原始有效注释、已确认的具体业务作用，或“未确认具体作用”。
- 已确认注释说明配置影响的对象和行为，不包含源码路径或“直接引用”描述。
- YAML 保留嵌套对象和列表，Properties 使用点号/索引表达相同叶子路径，两者键值语义一致。
- YAML 中不存在 `"- key"` 顶层伪键，也不存在“扁平键输出”内容。
- 旧版本备份发生在最终文件写入之前。
- 对话摘要已脱敏且包含全部未确认项。

