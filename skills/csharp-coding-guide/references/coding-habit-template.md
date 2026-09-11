# C# 编码习惯模板

本模板定义 AI 编写 C#/.NET 代码时的默认落地风格。它适用于现代 C#、.NET 和 ASP.NET Core 项目；项目已有 `.editorconfig`、分析器、框架版本和架构约定优先。

## 总体风格

- 先复用同目录代码、项目服务、扩展方法、Options、常量、枚举、仓储和公共协议，不另造同义实现。
- 简单逻辑直接内联；只有完整、稳定且命名清晰的业务步骤才抽取方法。
- LINQ 只用于无副作用且可读的筛选、投影、分组或聚合；包含状态修改、异常分支、外部调用或多个副作用时，优先使用明确的 `if`/`foreach`。
- 注释使用简短中文，说明业务阶段、特殊规则或原因；不要逐行翻译代码，也不要生成大段模板化 XML 文档。
- 不为了“更优雅”改变无关代码、日志、返回协议、异常语义或既有调用层次。

## 类型与成员顺序

遵循项目现有风格和 `.editorconfig`。没有明确约定时，按以下顺序组织：

1. 常量和 `static readonly` 字段。
2. 依赖字段和实例字段。
3. 构造器或主构造器。
4. public 成员，重载成员相邻。
5. protected 成员。
6. private 成员，按主流程首次调用顺序排列。
7. 必要的嵌套类型。

一个类型只围绕一个职责或高度内聚的用例集合。类型较大不是单独拆分的理由；出现无关变化原因、独立事务边界或独立外部能力时再拆分。

## 业务入口模板

入口方法使用卫语句减少嵌套，主体从上到下体现真实业务顺序。至少存在三个不易从调用名称识别的业务阶段时，使用简短编号注释；简单方法不机械编号。

```csharp
public async Task<ExampleResponse> ExecuteAsync(
    ExampleRequest request,
    CancellationToken cancellationToken)
{
    // 1. 校验业务前置条件
    var entity = await exampleRepository.FindByIdAsync(request.Id, cancellationToken);
    ValidateExecutable(entity);

    // 2. 准备本次处理数据
    var context = BuildExecutionContext(entity, request);

    // 3. 执行核心业务并保存结果
    ApplyExecution(entity, context);
    await exampleRepository.UpdateAsync(entity, cancellationToken);

    // 4. 完成事务外动作
    await publisher.PublishAsync(entity, context, cancellationToken);
    return responseMapper.Map(entity);
}
```

模板不是要求把每一步都抽成方法。单次查询、简单赋值、简单判断和一次性转换直接放在主流程中；抽取的方法必须对应完整且稳定的业务步骤。

## 命名与可空性

- 类型、方法、属性、事件和公共字段使用 PascalCase；局部变量和参数使用 camelCase；私有实例字段默认使用 `_camelCase`，并优先沿用项目既有风格。
- 接口使用 `I` 前缀；异步方法返回 `Task`、`Task<T>` 或 `ValueTask` 时使用 `Async` 后缀。事件处理器是少数允许 `async void` 的场景。
- 布尔值表达肯定语义，例如 `isEnabled`、`hasPermission`、`canRetry`，避免 `flag`、`data`、`result` 等无语义名称。
- 启用 nullable reference types 的项目中，准确表达可空性。不得用空抑制运算符 `!` 掩盖未知空值；只有不变量已在同一流程建立且代码不明显时才使用，并用短注释说明。
- 使用 `record`、`class`、`struct` 和 `readonly struct` 时按值语义、可变性、序列化和项目约定选择，不为简写改变既有领域模型语义。

## ASP.NET Core 条件模板

以下规则仅在项目使用 ASP.NET Core、内置 DI、EF Core 或对应组件时采用，不为套模板引入框架、库或新的统一响应协议。

### Controller 与端点

- Controller 或 Minimal API 只处理边界校验、认证授权上下文、调用应用服务和返回项目协议；不要在端点中承载数据库查询、复杂转换或业务状态决策。
- 沿用项目的验证、错误响应、ProblemDetails、OpenAPI 和授权策略；项目未使用时不机械新增一套框架封装。

### 服务与依赖注入

- 依赖使用构造器注入或项目已采用的主构造器。不要通过 `IServiceProvider` 充当 Service Locator，也不要在业务代码中手工 `new` 出可注入依赖。
- `Singleton` 必须线程安全，且不得直接持有 scoped 依赖（包括 `DbContext`）。后台 singleton 需要 scoped 服务时，通过 `IServiceScopeFactory` 创建并及时释放作用域。
- 容器创建和管理的 `IDisposable` 或 `IAsyncDisposable` 服务由容器释放，业务代码不得自行释放。

### EF Core 与模型

- 读取查询按项目约定选择跟踪；只读且不修改实体的查询通常使用 `AsNoTracking()`。不要将 EF 实体直接作为外部 API 契约，除非项目已有明确约定。
- 请求 DTO、命令、查询模型和响应模型仅在字段、生命周期、权限或边界契约确有差异时转换，不复制同构模型。

## 生产流程习惯

- 复杂写流程优先按“校验身份与权限、确定操作范围、获取必要锁、执行原子事务、安排事务后动作、返回结果、清理资源”的顺序展开。
- 所有 I/O 异步路径传递可用的 `CancellationToken`；不要使用 `.Result`、`.Wait()` 或无所有者的 fire-and-forget `Task` 阻塞、隐藏或丢失异步失败。
- 资源使用 `using` 或 `await using` 绑定作用域。只有实际拥有资源生命周期时才实现或调用 `Dispose`/`DisposeAsync`。
- 批量流程先整理输入，再批量查询并建立索引，随后在内存中完成业务处理，最后批量写入或调用外部能力；响应顺序有契约时显式保持顺序。
- 并发、事务、可靠消息和缓存细节分别遵循对应专项引用。

## 不复制的历史写法

即使在参考项目中看到，也不得作为默认编码习惯继续生成：

- 静态可变全局状态、同步阻塞异步调用、无取消令牌的长 I/O 路径或无观察者的后台任务。
- 在 `lock` 中执行 `await`、将 scoped 服务注入 singleton、共享同一个 `DbContext` 跨线程使用。
- 在 LINQ 查询中执行写操作、网络调用、日志或改变外部状态。
- 为减少主方法行数制造碎片方法，或为形式补充长篇 XML 文档、逐行注释和没有处理计划的 TODO。

## 单元测试模板

测试通过 public/protected 入口验证业务结果、状态变化或异常，方法名表达可观察行为。Mock 交互只用于证明关键副作用或没有发生危险调用，不能代替业务断言；完整测试规则以测试与审查引用为准。

```csharp
public sealed class ExampleServiceTests
{
    [Fact]
    public async Task ShouldReturnEmptyResultWhenNoDataMatches()
    {
        // Arrange: 使用项目现有 Mock 方式配置仓储返回空集合。

        // Act
        var result = await exampleService.FindEnabledAsync(CancellationToken.None);

        // Assert: 断言业务结果，并验证没有发生危险副作用。
        Assert.Empty(result);
    }
}
```

测试框架、断言库、Mock 风格和时间控制方式沿用项目现状；该示例不要求项目采用 xUnit。
