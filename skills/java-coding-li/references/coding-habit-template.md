# Java 编码习惯模板

本模板定义 AI 编写 Java 代码时的默认落地风格。它提炼自常见 Spring Boot 项目的工程实践，但不复制历史代码中的缺陷。项目已有明确约定时优先保持项目一致；多个方案都正确时，优先选择本模板的写法。

## 总体风格

- 先复用同包代码、项目工具、常量、枚举、Repo、Converter 和公共协议，不另造同义实现。
- 简单逻辑直接内联；只有完整、稳定且命名清晰的业务步骤才抽取方法。
- 普通转换可以使用 Stream；包含状态修改、异常分支、外部调用或多个副作用时，优先使用普通 `if`/`for`。
- 注释使用简短中文，说明业务阶段、特殊规则或原因。不要逐行翻译代码，也不要生成大段模板化 JavaDoc。
- 不为了“更优雅”改变无关代码、日志、返回协议、异常语义或现有调用层次。

## 类内顺序

默认按以下顺序组织，新代码不要让 public 和 private 方法无规律穿插：

1. 静态常量。
2. 依赖字段和成员字段。
3. 构造器或依赖注入。
4. public 方法，重载方法相邻。
5. protected 方法。
6. private 方法，按照主流程首次调用顺序排列。
7. 必要的内部类或内部枚举。

同一个类只围绕一个职责或一组高度内聚的用例。类较大不是单独拆分类的理由，但出现无关变化原因、独立事务边界或独立外部能力时应拆分。

## 业务入口模板

入口方法使用卫语句减少嵌套，主体从上到下体现真实业务顺序。至少存在三个不易从调用名称识别的业务阶段时，使用简短编号注释作为目录；简单方法不机械编号。

```java
public ExampleResponse execute(ExampleRequest request) {
    // 1. 校验业务前置条件
    ExampleEntity entity = exampleRepo.findById(request.getId());
    validateExecutable(entity);

    // 2. 准备本次处理数据
    ExecuteContext context = buildExecuteContext(entity, request);

    // 3. 执行核心业务并保存结果
    applyExecution(entity, context);
    exampleRepo.update(entity);

    // 4. 完成事务外动作
    publishResult(entity, context);
    return convertResponse(entity);
}
```

模板不是要求把每一步都抽成方法。单次查询、简单赋值、简单判断和一次性转换直接放在主流程中；`validateExecutable`、`buildExecuteContext` 等方法必须对应完整且稳定的业务步骤。

## 命名习惯

- 类、方法、字段严格使用标准 Java 大小写：类名 UpperCamelCase，方法和字段 lowerCamelCase，常量 UPPER_SNAKE_CASE。
- 方法名优先使用能表达结果或动作的准确动词，例如 `validate`、`build`、`convert`、`save`、`update`、`sync`、`publish`、`remove`。
- 不使用 `extracted`、`handlePre`、`processData`、`doSomething`、`getResult` 等脱离上下文后无法判断职责的名称。
- 提交前检查英文拼写，特别是 `update`、`header`、`robot`、`cron`、`response` 等常用词。
- 布尔变量表达肯定语义，例如 `enabled`、`matched`、`completed`，避免 `flag`。
- 同一概念沿用项目已有词汇，不为同一个动作创造多个近义词。

## Spring Boot 条件模板

以下模板仅在项目已经使用对应框架或组件时采用，不为套模板引入 Spring、Lombok、Swagger、MapStruct、MyBatis 或新的公共返回协议。

### Controller

Controller 保持轻量：边界校验、调用 Service、返回项目协议。不要在 Controller 中承载数据库查询、复杂转换或业务状态决策。

```java
@RestController
@RequiredArgsConstructor
@RequestMapping("/examples")
public class ExampleController {

    private final ExampleService exampleService;

    @PostMapping
    public ExampleResponse create(@Validated @RequestBody ExampleCreateRequest request) {
        return exampleService.create(request);
    }
}
```

- 项目已有 Swagger/OpenAPI 时补齐现有体系要求的 Controller、方法和模型字段注解。

### Service

- public 方法展示业务流程，事务边界由业务一致性决定。
- 数据准备、状态判断、保存和后置动作按真实顺序排列，避免在多层回调或复杂 Stream 中隐藏主线。
- 方法过长时按稳定业务能力拆分，不按行数切成 `step1`、`step2` 或无语义 helper。
- 同一流程需要积累日志、任务、标签等批量数据时，先在内存中完成准备，再使用项目已有批量接口统一处理。

依赖优先使用构造器注入和 `final` 字段：

```java
@Slf4j
@Service
@RequiredArgsConstructor
public class ExampleServiceImpl implements ExampleService {

    private final ExampleRepo exampleRepo;
    private final ExampleConvert exampleConvert;

    @Override
    public ExampleResponse getById(Long id) {
        ExampleEntity entity = exampleRepo.findById(id);
        return exampleConvert.convert(entity);
    }
}
```

只有项目确实依赖无参构造、框架限制或循环迁移等原因时才沿用字段注入，不新增大写开头的依赖字段。

### Repo 与 Mapper

- Repo 封装明确的数据访问能力和查询条件；Service 决定状态、模式、租户、开关等业务规则。
- Mapper 只接收已经确定的查询参数，不通过 `mode`、`flag` 等参数代替 Service 的业务判断。
- 查询为空时按照现有契约返回空集合、空分页或 `Optional`，不要随意混用 `null`。

```java
public List<ExampleEntity> findEnabledByIds(Collection<Long> ids) {
    if (CollectionUtils.isEmpty(ids)) {
        return Collections.emptyList();
    }

    return list(new LambdaQueryWrapper<ExampleEntity>()
            .in(ExampleEntity::getId, ids)
            .eq(ExampleEntity::getEnabled, Boolean.TRUE));
}
```

### Converter 与 DTO

- 项目已有 MapStruct 时，将稳定的对象边界转换集中在 Converter；不要在多个 Service 中重复复制字段。
- 转换包含查询、权限判断或状态迁移时留在 Service，不把业务行为塞入 MapStruct 表达式。
- 请求 DTO 在系统边界使用 Bean Validation 表达必填、范围和格式；复杂跨字段规则使用命名清楚的校验方法或项目已有校验器。
- Builder 用于字段较多、构造过程需要表达业务含义的 DTO 或上下文对象；简单可变实体按业务阶段设置字段即可。
- 只有字段、生命周期、权限或接口契约确有差异时新增 DTO/BO/VO，不复制同构模型。

## 生产流程习惯

- 复杂写流程优先按“校验身份与权限、确定操作范围、获取必要锁、执行原子事务、安排事务后动作、返回结果、清理资源”的顺序展开。
- 长耗时流程优先按“固化任务快照、异步推进状态、可靠投递、失败补偿”的方式保持同一业务口径；定时任务入口继续线性展示抢占、执行、更新和清理。
- 批量流程先整理输入，再批量查询并建立索引，随后在内存中完成业务处理，最后批量写入或调用外部能力；响应顺序有契约时显式保持顺序。
- 锁、时间与模式选择的细节遵循 [编码与设计](coding-and-design.md)，事务、状态、快照与权限遵循 [持久化、事务与安全](persistence-and-security.md)，消息与补偿遵循 [异常、日志与可靠性](exception-and-logging.md)。

## 不复制的历史写法

即使在参考项目中看到，也不得作为默认编码习惯继续生成：

- 大写开头的字段名、通配符 import、拼写错误和无语义方法名。
- 每次请求创建可复用的重量对象，或在业务代码中通过静态工具临时获取 Spring Bean。
- 一个 Service 长期混合互不相关的业务、定时调度、外部适配和数据访问职责。
- 不为减少主方法行数制造碎片方法，也不为形式补充作者日期、长篇 JavaDoc、逐行注释或没有处理计划的 TODO；相关约束以本技能的不变约束和编码与设计引用为准。

## 单元测试模板

测试通过 public/protected 入口验证业务结果、状态变化或异常，方法名表达可观察行为。Mock 交互只用于证明关键副作用或没有发生危险调用，不能代替业务断言；完整测试规则以测试与审查引用为准。

```java
@RunWith(MockitoJUnitRunner.class)
public class ExampleServiceImplTest {

    @Mock
    private ExampleRepo exampleRepo;

    @InjectMocks
    private ExampleServiceImpl exampleService;

    @Test
    public void shouldReturnEmptyResultWhenNoDataMatches() {
        when(exampleRepo.findEnabled()).thenReturn(Collections.emptyList());

        List<ExampleResponse> result = exampleService.findEnabled();

        assertTrue(result.isEmpty());
        verify(exampleRepo, never()).loadDetails(anyCollection());
    }
}
```

测试框架、断言库和 Mock 风格沿用项目现状，不为统一模板迁移 JUnit 版本。
