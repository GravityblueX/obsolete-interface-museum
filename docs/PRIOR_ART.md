# Prior Art / 资料与既有项目地图

旧接口研究最危险的两件事：

1. 抄一个网络 pinout 就开始接线；
2. 把“连接器形状”当成整个接口。

本文件把现成资料按证据等级和用途分类。

## 1. 厂商原始 Technical Reference / 标准

最高优先级。

典型来源包括：

- IBM PC / XT / AT Technical Reference；
- IBM PS/2 技术资料；
- ANSI / IEEE / ECMA / TIA/EIA 等标准；
- 芯片厂商 datasheet / application note；
- SCSI、ATA、IEEE 1284、IEEE 1394 等规范。

### 原则

电气层、时序、最大电压、电流、终端、hot-plug 等涉及真实硬件安全的结论，必须尽量回到这一级，不能只引用论坛帖子。

## 2. Bitsavers

- IBM PC 资料目录：<https://www.bitsavers.org/pdf/ibm/pc/>
- IBM PC/XT Technical Reference：<https://bitsavers.org/pdf/ibm/pc/xt/>
- IBM PC/AT Technical Reference：<https://www.bitsavers.org/pdf/ibm/pc/at/>
- IBM adapters / VGA 等资料：<https://bitsavers.org/pdf/ibm/pc/cards/>
- SCSI 相关资料示例：<https://www.bitsavers.org/components/ti/scsi/>

Bitsavers 保存大量原厂手册、技术参考、芯片资料，是本项目最重要的历史技术证据库之一。

### 本项目决策

不把 Bitsavers PDF 批量复制进仓库；保存精确文献名、版本、页码和稳定入口，在必要时记录哈希/本地档案位置。

## 3. pinouts.ru

- <https://pinouts.ru/>

这是一个规模很大的现代/旧硬件 pinout、线缆和连接器数据库。

### 它已经解决什么

- 快速查某个连接器针脚；
- 常见 cable wiring；
- 大量设备和厂商接口索引。

### 本项目不重复什么

不做“又一个 3000 条针脚表网站”。

### 适合怎么用

作为线索源和交叉核验源之一。真实硬件接线前仍要优先回原厂手册/标准。

## 4. OSDev Wiki

- Hardware Interfaces：<https://wiki.osdev.org/Category:Hardware_Interfaces>
- PS/2：<https://wiki.osdev.org/PS/2>
- I/O Ports：<https://wiki.osdev.org/I/O_Ports>

OSDev 特别适合理解 PC-compatible 的软件/硬件交界：

- legacy I/O port；
- PS/2 controller；
- serial / parallel；
- VGA；
- IDE/SCSI；
- IRQ / DMA / chipset compatibility。

### 使用边界

它是非常好的实践性二手资料，不应替代原厂 Technical Reference，尤其是电气安全与边缘时序问题。

## 5. Computer History Museum

- Computer History Museum：<https://www.computerhistory.org/>
- Storage standards 相关材料示例：<https://www.computerhistory.org/storageengine/standards-accelerate-disk-drive-integration/>

CHM 更适合补：

- 产品和标准的历史位置；
- 为什么 IDE/SCSI/Fibre Channel 等会在某个产业阶段出现；
- 设备、广告、实物与产业史证据。

它不是 pinout/reference manual 的替代品。

## 6. Living Computers: Museum+Labs 相关开源成果

- GitHub：<https://github.com/livingcomputermuseum>

保留有 Xerox Alto/Star 等模拟器和协议实现。

### 启示

“旧接口博物馆”不一定必须拥有全部真实硬件；高质量模拟器 + 原始手册 + 可重复实验也能恢复一部分历史系统行为。

## 7. 仿真器

值得利用：

- QEMU
- 86Box
- PCem
- DOSBox-X（部分设备）
- MAME（大量历史计算平台）

### 原则

仿真器用于建立可重复环境，不用于证明真实电气特性。

必须明确标：

```text
Evidence: emulated behavior
≠
Evidence: measured physical hardware
```

## 8. 逻辑分析与测量工具

本仓库可以逐渐建立自己的实验层：

- USB logic analyzer + sigrok/PulseView；
- oscilloscope；
- USB–serial adapter；
- parallel/PS2 breakout；
- old PC / PCI/ISA test machine。

### 注意

不要把“测到了电平”直接推成“标准规定如此”；测量只能说明这个具体设备/样本。

## 9. 现成知识中仍缺什么

大量网站已经告诉你“第 3 脚是什么”，但通常缺少统一的跨层解释：

```text
connector
→ voltage/signaling
→ timing
→ controller/register
→ OS driver
→ user-visible behavior
→ replacement path
```

这正是本项目的主价值。

## 10. 具体展品查重清单

每开一个接口前，AI 必须先完成：

- [ ] 原始标准/厂商手册定位；
- [ ] Bitsavers 是否已有同期资料；
- [ ] pinouts.ru 是否已有 pinout，避免重抄；
- [ ] OSDev 是否已有软件/寄存器说明；
- [ ] QEMU/86Box/PCem 是否能模拟；
- [ ] 是否有真实硬件可测；
- [ ] 哪些结论属于机械、哪些属于电气、哪些属于协议、哪些属于 OS；
- [ ] 接线/热插拔是否存在损坏风险；
- [ ] 我们的新贡献是跨层解释、实验还是历史比较？

如果只是“整理一个针脚表”，原则上不值得单独做 exhibit。
