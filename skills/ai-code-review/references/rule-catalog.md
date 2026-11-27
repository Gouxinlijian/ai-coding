# 内置检测器清单

引擎只提供确定性的文本启发式检查，用于补充而不是替代编译器诊断、Linter、SAST、依赖扫描和
上下文复核。文件扩展名被接受，不代表已具备该语言的语义分析能力。

## 安全

- `security.secret-generic`：识别常见的凭据赋值与私钥标记；匹配到的值不会回显。
- `security.sql-concat`：识别查询调用中的字符串拼接或插值。
- `security.command-injection`：识别以动态字符串或 shell 解释执行进程的调用。
- `security.dynamic-eval`：识别 `eval`、`exec`、`new Function` 等动态求值。
- `security.xss-sink`：识别直接写入 HTML 或不安全渲染的写法。
- `security.weak-crypto`：识别弱哈希或非加密随机数 API。

## 缺陷与资源

- `bug.broad-exception`：识别宽泛的异常捕获；不能证明异常被吞掉。
- `resource.unclosed-resource`：识别资源打开调用；不能证明存在泄漏。

## 性能与可维护性

- `performance.loop-work`：标记循环中的重复工作，需要人工判断复杂度。
- `maintainability.long-function`：在超过 150 行的文件中检查函数声明；不测量函数体长度。
- `maintainability.long-file`：超过 300 行的文件。
- `maintainability.todo-risk`：TODO、FIXME、HACK 标记。

## 风格

- `style.naming`：特定声明模式中的单字母命名。
- `style.debug-output`：直接调用 console 或 print 的调试输出。
- `style.long-line`：超过 140 字符的行。

## 能力边界

以下问题不属于内置检测器，必须结合项目上下文确认：事务边界与回滚、鉴权位置、并发正确性、
查询次数、跨文件调用影响、框架代理行为。需要项目专属模式时，用 JSON 自定义规则补充，
自定义规则与内置规则同时生效。
