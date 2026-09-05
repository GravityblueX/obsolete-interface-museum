# Evidence model

本仓库把“事实从哪里来”当成展品结构的一部分，而不是写完以后再补脚注。

## Evidence levels

| Level | 类型 | 可支持什么 | 不能单独支持什么 |
|---|---|---|---|
| E1 | 标准、原厂手册、同时代技术参考、datasheet | 标准规定、电气边界、时序、寄存器、命令、兼容性范围 | 某一具体机器一定按标准实现 |
| E2 | 可靠的后续技术文档、博物馆资料、维护文档 | 历史背景、实现惯例、生态关系、交叉解释 | 覆盖或推翻 E1 的硬件安全边界 |
| E3 | 仿真器、模拟器、参考实现 | 可重复的软件可见行为、寄存器/协议实验 | 真实电气特性、模拟器未实现部分 |
| E4 | 本项目实测 | 指定设备、指定 setup 下的实际行为 | 整个标准或所有设备的普遍结论 |
| E5 | pinout 数据库、论坛、博客、个人笔记 | 线索、检索入口、待验证假设 | 未交叉验证的真实接线与安全结论 |

`exhibit.json` 中的 `evidence_summary.primary_sources` 统计展品实际使用的 E1
来源。因此该值大于零时 `highest_level` 必须是 `E1`；没有 E1 来源时，则应在
E2 至 E5 中记录当前实际可用的最高等级。

## Claim discipline

每个关键结论应尽量记录：

```text
Claim: <一句可核验陈述>
Layer: physical | electrical | signaling | protocol | host | ecosystem
Evidence: E1..E5
Source: <文献/页码/稳定链接/实验记录>
Scope: <标准 / 某实现 / 某设备 / 仿真器>
Confidence: confirmed | supported | tentative
Notes: <冲突、版本差异、限制>
```

### 最低要求

- 涉及电压、电流、终端、方向、hot-plug、供电针脚的结论：优先需要 E1；
- 涉及历史位置和产业生态：E1 + E2 最理想；
- 涉及 OS/driver 行为：E1/E2 与可重复软件实验可互补；
- E3 必须写明 emulator/version/config；
- E4 必须附 setup metadata；
- E5 不得作为危险接线建议的唯一依据。

## 冲突怎么处理

不要把冲突资料“平均一下”。应先判断冲突是否来自：

1. 标准版本不同；
2. connector mapping 与 protocol 定义混淆；
3. PC-compatible 惯例与正式标准不同；
4. 厂商扩展；
5. 文档错误；
6. 单台设备偏离标准。

无法消解时保留冲突，并把结论降为 `supported` 或 `tentative`。

## 仿真和实测必须分开

推荐标签：

```text
Evidence: emulated behavior
Evidence: measured hardware
Evidence: documented requirement
```

例如“QEMU 在此端口返回某值”只能证明指定版本/配置的 QEMU 行为，不能直接证明真实 ISA 卡电气上如何驱动总线。

## 引用粒度

关键技术事实尽量给到：文献名、版本/日期、章节或页码。不要只写一个站点首页。

## 展品完成门槛

一件展品在本阶段标记完成前，至少需要：

- 一份 E1 或能解释为何暂时找不到；
- 关键跨层结论有来源；
- 仿真、实测、二手资料不互相冒充；
- 所有安全相关未知项明确标出，而不是猜测补齐。
