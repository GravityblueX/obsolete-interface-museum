# Obsolete Interface Museum · 旧接口博物馆

> 不只看“这个口长什么样”，而是把连接器、电气层、信号、协议、主机角色和时代生态一起复原。

## 为什么做这个

很多旧接口今天只剩一个模糊印象：

- “串口很慢”；
- “并口就是打印机口”；
- “PS/2 不能热插拔”；
- “SCSI 很麻烦”；
- “ISA 就是 PCI 之前那个槽”。

但真正有意思的是：

- 接口为什么会长成这样？
- 哪些针脚只是供电，哪些是控制、时钟、数据、握手？
- 谁是 host，谁是 device？
- 数据是串行还是并行、同步还是异步、单端还是差分？
- IRQ、DMA、终端电阻、总线仲裁、设备 ID 为什么会成为用户必须理解的东西？
- 哪些设计后来被 USB / PCIe / SATA 等继承，哪些彻底消失？

## 本项目不是 pinout 抄表

现成 pinout 数据库已经很多，本仓库不以复制针脚表为目标。

每个展品至少要把以下层次分开：

```text
Physical connector
        ↓
Electrical characteristics
        ↓
Signaling / timing
        ↓
Protocol / command model
        ↓
Driver / OS integration
        ↓
Real hardware ecosystem
```

## 每个展品的结构

```text
exhibits/<interface>/
├── README.md          # 历史、用途、生命周期
├── physical.md        # 连接器、机械结构、针脚引用
├── electrical.md      # 电平、终端、驱动方式、时序
├── protocol.md        # 命令、角色、传输模型
├── host-integration.md# IRQ/DMA/端口/驱动
├── experiment.md      # 可重复实验或模拟
├── descendants.md     # 继承关系与替代者
├── sources.md         # 手册、标准、既有资料
└── exhibit.json       # 机器可读元数据（见 schemas/exhibit.schema.json）
```

## 第一批展品

### 外部接口

- RS-232 / DE-9 / DB-25
- Centronics / IEEE 1284 并口
- PS/2 与 AT 键盘接口
- VGA
- Game Port / MIDI
- IEEE 1394 / FireWire
- eSATA

### 内部总线与存储接口

- ISA
- MCA
- EISA
- PCI（作为过渡参照）
- IDE / PATA / ATAPI
- 并行 SCSI
- PCMCIA / CardBus

## 一件展品必须回答的 10 个问题

1. 什么时候出现？
2. 原始用途是什么？
3. 物理接口是什么？
4. 电气标准是什么？
5. 数据与控制信号如何分工？
6. 地址/设备选择/仲裁怎么做？
7. 操作系统如何发现和驱动它？
8. 用户当年最常见的配置痛点是什么？
9. 它为什么退出主流？
10. 它的哪些思想活到了今天？

## 实验优先，而不是只写历史

例子：

- 用 USB–RS232 转换器抓真实串口波形；
- 用逻辑分析仪观察 PS/2 clock/data；
- 在 QEMU/86Box/PCem 中观察 ISA I/O port 与 IRQ；
- 对 IDE IDENTIFY DEVICE 命令做字段级拆解；
- 比较并行 SCSI 的终端与现代串行总线的点到点链路；
- 对 VGA legacy register 做最小实验，但不要求真的去复刻整张显卡。

## 安全边界

- 不建议对昂贵/不可替代老硬件做带风险的热插拔实验；
- 不凭网络 pinout 直接接线，必须回到厂商手册/标准交叉验证；
- 电源、总线电平、终端条件必须写清楚；
- 仿真结果与真实硬件结果分开标记。

## 第一阶段

- [ ] `docs/PRIOR_ART.md`：pinout 数据库、厂商原始手册、Bitsavers、OSDev 等资料地图；
- [ ] RS-232 完整展品；
- [ ] PS/2 完整展品；
- [ ] ISA 最小展品；
- [ ] IDE/PATA 完整展品；
- [ ] 并行 SCSI 完整展品；
- [ ] 做一张“并行接口为何大量让位给高速串行接口”的跨展品比较图；
- [ ] 每个展品至少引用一份同时代/原始技术手册。

## 最终形态

这应该是一座**接口技术史的可操作博物馆**：你不仅能看到一个 DB-25 长什么样，还能知道当年一根线为什么要这样握手、为什么终端不对就会出事、为什么后来的人决定换一种办法。
