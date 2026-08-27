# Roadmap

旧接口博物馆先建立“跨层展品”方法，再扩大展品数量。

## M0 — 展柜标准

- [x] `exhibits/_template/`；
- [x] `docs/EVIDENCE.md`：原厂手册 / 二手资料 / 仿真 / 实测的证据分层；
- [x] `docs/HARDWARE-SAFETY.md`：电平、接线、热插拔、未知设备规则；
- [x] `schemas/exhibit.schema.json`；
- [x] 定义接口关系：`replaced-by / compatible-with / physically-similar / protocol-carried-over / electrically-related`。

### M0 验收

已用 `docs/TEMPLATE-VALIDATION.md` 验证同一模板分别描述 RS-232、ISA、IDE 时，仍能明确区分：

- connector；
- electrical；
- signaling；
- protocol；
- OS integration。

模板不以“外部插头”为前提，内部 bus 和跨层存储接口家族也可以表达。

---

## M1 — 两个外部接口完整展品

### RS-232

重点：

- [ ] 标准与常见 DE-9/DB-25 映射区分；
- [ ] TX/RX/GND 与 RTS/CTS、DTR/DSR；
- [ ] DTE / DCE；
- [ ] 电气电平与 UART TTL 不是一回事；
- [ ] null modem；
- [ ] 真实 USB-RS232 loopback 实验；
- [ ] modem/control signal 的时代背景。

### PS/2

重点：

- [ ] AT keyboard 与 PS/2 关系；
- [ ] clock/data 双线；
- [ ] host/device 双向通信；
- [ ] 8042/controller 的 PC 兼容历史；
- [ ] scan code；
- [ ] 仿真 + 条件允许时逻辑分析仪抓波形。

### 验收

两件展品都必须引用原始/同期技术文档，不能只引用 pinout 网站。

---

## M2 — “PC 配置地狱”展厅

选择 ISA + 一个典型设备模型：

- I/O port；
- IRQ；
- DMA；
- jumper / DIP switch；
- PnP 前后的差异。

目标：解释为什么当年“装一块卡”需要用户理解资源冲突。

可在 86Box/PCem/QEMU 中设计可重复冲突实验。

产物：

- [ ] `exhibits/isa/`；
- [ ] `labs/isa-resource-conflict/`；
- [ ] 一篇 `studies/from-jumpers-to-enumeration.md`。

---

## M3 — 存储接口展厅

### IDE / PATA / ATAPI

- [ ] master/slave 历史与 cable select；
- [ ] task file registers；
- [ ] PIO / DMA；
- [ ] IDENTIFY DEVICE；
- [ ] ATAPI 为什么把 packet command 引进 ATA。

### Parallel SCSI

- [ ] initiator / target；
- [ ] IDs 与仲裁；
- [ ] termination；
- [ ] narrow/wide、single-ended/differential 等历史分化；
- [ ] SCSI command model 与物理总线分离。

### 验收

能清楚解释：

> “SCSI”为什么不能简单等同于某一种 50-pin 插头。

---

## M4 — 并行到高速串行

跨展品比较：

- Parallel ATA → SATA
- Parallel SCSI → SAS
- PCI/PCI-X → PCIe
- parallel printer → USB printer class（作为用户体验参照）

研究问题：

- skew；
- signal integrity；
- cable/connector complexity；
- clocking；
- point-to-point vs shared bus；
- serialization overhead 为什么反而能换来更高速度。

产物：`studies/why-serial-won.md`。

---

## M5 — 真实硬件实验库

只有硬件条件允许时做：

- logic analyzer traces；
- oscilloscope screenshots/data；
- adapter/cable photos；
- known-good test rigs；
- equipment calibration/limitations。

所有实测记录必须写：

```text
device model
adapter model
measurement tool
probe point
sample rate
software/driver
uncertainty
```

不要用一个样本代表整个标准。

---

## AI 可直接领取的第一批任务

### Task A — 建展品模板

已完成。模板位于 `exhibits/_template/`，证据、安全、关系词和 schema 已一并落地。

### Task B — RS-232 资料审查

先定位 EIA/TIA/厂商技术资料、IBM PC 串口资料、pinouts.ru 和 OSDev；输出 `research/rs232-source-map.md`，标注证据等级和冲突点。

### Task C — PS/2 历史链

专门厘清 XT keyboard → AT keyboard → PS/2 connector/interface 的继承关系，防止把“Mini-DIN-6 插头”和完整协议混为一谈。

### Task D — IDE vs SCSI 术语清理

创建 `research/storage-interface-terminology.md`，先解释 ATA/IDE/PATA/ATAPI/SCSI/SAS 各是什么层次，再决定怎么建展品。

### Task E — 实验硬件清单

只列低风险、便宜、可替换的实验器材与用途，不采购：USB-RS232、PS/2 breakout、logic analyzer、老 PCI/ISA 机器等。

## Stop conditions

- pinout 未经原厂资料交叉验证就准备接线；
- 需要对不可替代硬件做风险热插拔；
- 仿真行为被写成真实电气结论；
- “SCSI = 某个接口形状”这类层次混淆；
- 新页面只是复制已有 pinout 表，没有跨层解释。

博物馆的核心不是收藏接口名字，而是恢复**当时的人为什么必须这样连、这样配、这样驱动**。
