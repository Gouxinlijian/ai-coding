# 人类风格代码示例

本文件提供流程编排和“像人写的代码”的完整正反例，供首次编写、重构或需要风格对照时参考；规则本身见[编码习惯模板](coding-habit-template.md)。

## 流程编排示例

```java
/**
 * 导入客户：过滤错误行、批量匹配已有客户、区分新增与变更后落库。
 */
public List<ImportError> importCustomers(ImportRequest request) {
    // 1. 校验并过滤导入行，错误行收集后返回
    List<ImportError> errors = new ArrayList<>();
    List<ImportRow> rows = checkAndFilter(request.getRows(), errors);
    if (rows.isEmpty()) {
        log.info("importCustomers..过滤后无可导入数据..requestId:{}", request.getRequestId());
        return errors;
    }

    // 2. 按客户编码批量查询已有记录
    Map<String, Customer> existing = customerRepo.findByCodes(codesOf(rows));

    // 3. 区分新增与变更，分别批量落库
    saveNewAndChanged(rows, existing);

    // 4. 返回错误行，成功行已入库
    log.info("importCustomers..导入完成..total:{}, failed:{}", request.getRows().size(), errors.size());
    return errors;
}
```

阶段按实际业务划分，不要求每个阶段都抽成方法；没有实质内容的步骤不写编号。

## 反例与正例

```java
// 反例：注释逐行复述、重复兜底
// 1. 校验参数
if (request == null) {
    throw new BizException("参数不能为空");
}
// 2. 查询客户
CustomerDO customerDO = customerMapper.selectById(request.getCustomerId());
// 3. 判断是否存在
if (customerDO == null) {
    throw new BizException("客户不存在");
}
// 4. 更新
customerDO.setAuditStatus(AuditStatus.PASS.getCode());
customerMapper.updateById(customerDO);

// 正例：注释只讲阶段和业务规则
/**
 * 审核客户：校验存在性后更新审核状态与审核人。
 */
public void approve(ApproveRequest request) {
    // 1. 客户不存在时拒绝审核，避免产生无主记录
    Customer customer = customerRepository.get(request.getCustomerId());
    if (customer == null) {
        throw new BizException(CUSTOMER_NOT_FOUND);
    }

    // 2. 审核状态与审核人同时落库
    customer.setAuditStatus(AuditStatus.PASS.getCode());
    customer.setApproverId(request.getApproverId());
    customerRepository.update(customer);
}
```

## 存量代码修改

### 默认保留原风格

```java
// 原文件用 xxxList / Objects.isNull / 显式类型；改动时沿用，不顺手改名或换写法
List<Order> orderList = orderRepo.findByOrderNos(orderNoList);
if (Objects.isNull(orderList) || orderList.isEmpty()) {
    return Collections.emptyList();
}
```

### 最小规范化

```java
// 只规范本次触碰的行：把折行改一行、补字段注释；不重排无关代码
order.setRemark(StringUtils.defaultString(vo.getRemark()));
```

默认保留原风格；只有本次新增或修改的片段按新规范写，不批量重命名或重排。原写法有正确性、安全或性能风险时，才在本次范围内最小修复并说明原因。

## 去 AI 味红线

美化或去 AI 味只改风格，不改行为、公共契约、权限、校验和资源释放；不为“像人”引入 bug、死代码、错误命名或破坏编译。改造后必须能通过原有测试或等价验证。
