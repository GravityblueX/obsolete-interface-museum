# Interface relationship vocabulary

旧接口之间的关系不能只用“兼容/不兼容”两格表示。本仓库使用以下关系词，并要求注明关系发生在哪一层。

## `replaced-by`

A 在主要使用场景中被 B 取代。

这是一条历史/生态关系，不自动意味着协议、电气或机械兼容。

示例结构：

```yaml
relation: replaced-by
from: <A>
to: <B>
layer: ecosystem
scope: <具体场景>
notes: <迁移是直接、渐进还是经由桥接器>
```

## `compatible-with`

A 与 B 在明确限定条件下可以互操作。

必须同时写清：

- 哪一层兼容；
- 是否需要 adapter / bridge / transceiver / firmware；
- 兼容是否双向；
- 哪些功能会丢失。

禁止只写“兼容”而不限定 scope。

## `physically-similar`

连接器外形、尺寸、针数或机械结构相似。

该关系**不表示可以连接，更不表示电气或协议兼容**。它主要用于记录最容易误插/误认的历史对象。

## `protocol-carried-over`

后继接口继续承载、封装或保留了前代的命令/协议模型，但传输层、物理层或拓扑已经变化。

用于表达“思想/命令模型活下来了，但线已经完全不是那根线”。

## `electrically-related`

两个对象共享或继承某种电气/信号设计关系，例如相近驱动方式、逻辑约定或同一家族 transceiver。

必须说明具体相关点，不能用它替代正式标准族关系。

## Relationship record

建议在展品元数据中写：

```json
{
  "type": "compatible-with",
  "target": "example-interface",
  "layer": "protocol",
  "scope": "limited mode only",
  "requires": ["adapter"],
  "direction": "bidirectional",
  "evidence": ["SRC-001"],
  "notes": "Physical connector differs."
}
```

## 为什么要这样做

同一个接口名经常横跨多个层次：

- 一个连接器可能承载多个协议；
- 同一协议可能经历多个连接器；
- 命令集可能跨越并行/串行两代传输；
- 机械兼容可能恰好是危险的电气不兼容。

因此所有关系都必须回答：**哪一层、什么范围、是否需要中介、证据是什么。**
