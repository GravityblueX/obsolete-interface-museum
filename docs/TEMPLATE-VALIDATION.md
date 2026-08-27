# Template validation

M0 要求同一套展品契约不能只适合“外部插头”。这里用三种不同对象做结构验证；本页只验证**分类能力**，不把尚未完成资料审查的技术细节提前写成事实。

## Case A — RS-232

RS-232 展品需要能表达：

- 标准本身与常见 connector mapping 分开；
- electrical/signaling 层可以独立于 UART/host controller 讨论；
- DTE/DCE 等角色属于协议/生态语境，而不是连接器形状；
- null-modem/adapter 属于关系与互连实践；
- USB-RS232 实验只能代表 adapter + setup，不自动代表完整标准。

模板适配结果：`physical.md`、`electrical.md`、`protocol.md`、`host-integration.md` 都有独立位置，没有要求“RS-232 = 某个 D-sub 插头”。

## Case B — ISA

ISA 展品需要能表达：

- 展品核心可以是内部 bus，而不是外部 connector；
- physical 层仍可记录 slot/card-edge，但不会主导整个展品；
- electrical/signaling 层能记录总线约束；
- host integration 可以成为主要叙事层，容纳 I/O port、IRQ、DMA、jumper/PnP 等资源问题；
- `experiment.md` 可以承载 86Box/PCem/QEMU 的资源冲突实验，并明确为 E3。

模板适配结果：没有强迫 ISA 套用“host/device cable”叙事，`object_kind` 和每层独立状态允许 bus 型展品成立。

## Case C — IDE / ATA / PATA

该组术语特别适合验证“名字可能跨层”的情况。展品需要能表达：

- connector/cable、electrical/signaling、host register model、command model 可能需要分别命名和限定；
- 历史别名不能直接当成同层同义词；
- master/slave/cable-select 等用户可见配置应放在具体层次，而不是混进针脚表；
- 后继关系可能是 ecosystem replacement，也可能存在 command/protocol carry-over，二者应分别记录。

模板适配结果：`object_kind` 可同时标记多个对象种类，`relationships` 强制填写 layer/scope，适合在正式 source map 后拆清 ATA/IDE/PATA/ATAPI。

## M0 conclusion

当前模板至少能容纳：

1. 外部串行接口/电气标准型对象；
2. 内部共享总线型对象；
3. 跨 connector、host interface 与 command model 的存储接口家族。

因此后续新增展品时，优先复用此契约。若某展品无法自然落入六层结构，应先判断它是不是更适合作为 `study`、`lab` 或多个相互关联的 exhibit，而不是继续扩大一个模糊展品的边界。
