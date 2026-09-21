# Java 正确性

本文件只收录会影响运行结果的 Java 语言级陷阱与正确性规则；日常写法和结构划分不在本文件。项目已有工具类或编码规范可覆盖时优先复用。

## 对象相等与哈希

- 重写 `equals` 必须同时重写 `hashCode`，且满足相等对象哈希一致的契约；作为 `Map` 键或 `Set` 元素的对象必须正确实现两者。
- `BigDecimal` 比较数值使用 `compareTo`，不使用 `equals`：`new BigDecimal("1.0").equals(new BigDecimal("1.00"))` 为 `false`。金额求和、比较和取余使用 `BigDecimal`，入参为字符串构造器或 `valueOf`。
- 明确比较方式后不混用 `==` 与 `equals`：基本类型、枚举用 `==`，对象用 `equals`（必要时 `Objects.equals(a, b)` 处理空值）。
- 重写 `equals` 的参数类型必须是 `Object`，并处理参数为 `null`、类型不同和自反比较。

## 包装类型与拆装箱

- 包装类型（`Integer` 等）之间比较使用 `equals`；`==` 只对 `-128 ~ 127` 缓存区间内可靠，区间外为 `false`。
- 三目运算符两侧类型不一致时会发生自动拆箱，空包装类型会抛 NPE：`boolean b ? i1 : i2` 中若 `i1`/`i2` 一个基本类型一个为 `null` 包装类型即触发。
- 方法参数、返回值和字段在可能为 `null` 时使用包装类型；明确非空且表达业务量的内部值可用基本类型，不混用至语义不清。

## 集合陷阱

- `Arrays.asList(...)` 返回固定大小视图，不支持 `add`/`remove`；需要可变集合时用 `new ArrayList<>(...)`。
- `subList` 返回原列表视图，修改视图会影响原列表；持久化或跨层传递前拷贝。
- 遍历集合时不得直接对其 `add`/`remove`，使用迭代器的 `remove`、`removeIf` 或先收集再批量操作。
- 可变对象（含可变 List/Map）作为 `Map` 键时，键内容变化会破坏索引，使用不可变键或不变字段。
- `Map` 用 `getOrDefault`、`computeIfAbsent`、`putIfAbsent` 时注意默认值/映射函数副作用与空值语义，不为掩盖缺失语义而返回空集合或默认值。
- 除 `EnumMap` 外不得在运行时修改枚举；`enum` 常量比较使用 `==`，需索引或映射时使用 `EnumMap`/`EnumSet`。

## 数值与精度

- 精确小数（金额、利率、计量）使用 `BigDecimal`；禁止用 `double`/`float` 承载金额或做精确相等比较。
- 整数除法、取模和溢出边界显式处理：`int` 运算溢出不抛异常，大数使用 `long` 并显式 `L` 后缀或 `Math.addExact` 等。
- 浮点比较使用误差范围而非 `==`；跨系统金额以最小货币单位为整数或字符串，避免二进制浮点误差。

## 日期与时间

- 使用 `java.time`（`LocalDate`/`LocalDateTime`/`Instant`/`ZonedDateTime`/`Duration`/`Period`）而非 `Date`/`Calendar`。
- `SimpleDateFormat`、`Calendar` 非线程安全，不得作为静态共享实例；线程安全格式化使用 `DateTimeFormatter`（不可变）或 `ThreadLocal`。
- 跨系统、存储和审计时间统一 `Instant` 或带时区的 `ZonedDateTime`；仅业务日历语义使用 `LocalDate`/`LocalDateTime`，并明确时区转换点。

## 字符串与资源

- 循环内字符串拼接使用 `StringBuilder`（或 `String.join`/`String.format`）；单语句拼接量小可直接 `+`。
- 常用正则预编译为 `static final Pattern`，避免循环内重复 `String.matches` 编译。
- 字符集、数字和日期格式化在协议边界显式指定，不得依赖 JVM 默认字符集或 locale。
- 可关闭资源用 try-with-resources，且关闭顺序按声明逆序；实现 `Closeable`/`AutoCloseable` 时保证幂等关闭。

## 空值与 Optional

- 明确 `null`、空字符串和空集合三种语义，不互相替代；在可信边界完成校验后不重复兜底。
- `Optional` 用于方法返回值表达"可能无值"，不用于字段、方法参数或集合元素。
- 已知非空对象直接使用，不写 `Optional.of(x).orElse(...)`；`Optional` 不替代明确的边界校验，不通过 `Optional.ofNullable(...).orElseThrow()` 掩盖真实错误。

## Lombok（仅当项目已使用）

- `@Data` 生成 `equals/hashCode/toString`，继承场景会遗漏父类字段，需 `@EqualsAndHashCode(callSuper = true)` 或显式处理；别名为集合/大对象时评估 `toString` 泄露与性能。
- `@Builder` 对字段默认值不生效，需默认值时构造器内初始化或用 `@Builder.Default`。
- 敏感字段不因 `@Data`/`@ToString` 被完整序列化进日志或响应。
