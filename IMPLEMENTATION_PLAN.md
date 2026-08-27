# IMPLEMENTATION_PLAN.md — Obsolete Interface Museum

## Phase 0 — Exhibit contract

- [x] `docs/EVIDENCE.md`；
- [x] `docs/HARDWARE-SAFETY.md`；
- [x] `schemas/exhibit.schema.json`；
- [x] `exhibits/_template/`；
- [x] 定义 `replaced-by / compatible-with / physically-similar / protocol-carried-over / electrically-related`；
- [x] 用 RS-232 / ISA / IDE 三种不同层次对象验证模板（见 `docs/TEMPLATE-VALIDATION.md`）。

## Phase 1 — RS-232

- [ ] 原始/同期资料 source map；
- [ ] 标准与常见 DE-9/DB-25 映射分开；
- [ ] DTE/DCE；
- [ ] TX/RX/GND 与 modem control；
- [ ] RS-232 电平 vs TTL UART；
- [ ] null modem；
- [ ] 安全条件允许时 USB-RS232 loopback；
- [ ] 仿真/实测分别标注。

## Phase 2 — PS/2

- [ ] XT → AT → PS/2 历史链；
- [ ] connector 与协议分开；
- [ ] clock/data 双向；
- [ ] host/device；
- [ ] scan code；
- [ ] 8042/PC compatible 语境；
- [ ] 先仿真，真实逻辑分析仪实验为可选增强。

## Phase 3 — ISA resource-conflict lab

- [ ] I/O port；
- [ ] IRQ；
- [ ] DMA；
- [ ] jumper/DIP；
- [ ] PnP 前后差异；
- [ ] 86Box/PCem/QEMU 中可重复冲突实验；
- [ ] `studies/from-jumpers-to-enumeration.md`。

## Phase 4 — IDE/PATA/ATAPI

- [ ] ATA/IDE/PATA/ATAPI 术语表；
- [ ] master/slave/cable select；
- [ ] task-file registers；
- [ ] PIO/DMA；
- [ ] IDENTIFY DEVICE 字段级实验；
- [ ] ATAPI packet command 关系。

## Phase 5 — Parallel SCSI

- [ ] SCSI command model 与物理总线分开；
- [ ] initiator/target；
- [ ] IDs/arbitration；
- [ ] termination；
- [ ] narrow/wide；
- [ ] single-ended/differential；
- [ ] 至少一个安全的仿真或样本分析。

验收：读者能解释为什么“SCSI”不是一种插头。

## Phase 6 — Why serial won

产出 `studies/why-serial-won.md`，比较 PATA→SATA、parallel SCSI→SAS、PCI→PCIe，讨论 skew、SI、clocking、connector/cable、shared bus vs point-to-point，以及序列化为何能换取更高速率。

## Phase 7 — Real hardware library

仅在硬件条件允许时：

- logic analyzer traces；
- oscilloscope data；
- adapter/cable photos；
- known-good rigs；
- calibration/measurement limits。

任何真实实验都必须附完整 setup metadata。

## 每阶段门禁

- 至少一份原始/同期资料支持关键事实；
- 明确 evidence level；
- 仿真/实测分离；
- 不输出未经验证的接线建议；
- 不伤害不可替代硬件；
- checkpoint 后继续。
