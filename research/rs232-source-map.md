# RS-232 资料审查：标准、PC 实现与待核验冲突

> 状态：source map complete；正式展品尚未开始。
>
> 最后核验：2026-09-01。

这份资料地图的目标不是先抄出一张针脚表，而是回答三个更基础的问题：

1. `RS-232` 这个名字在哪些资料里指完整接口标准，在哪些场景里只是电气层、连接器或 PC 串口的简称；
2. 哪些来源可以分别支持 connector、electrical、signaling、protocol/roles 与 host integration；
3. 在写出接线或实验步骤前，还缺哪些规范文本与交叉验证。

## 先给结论：这里至少有五个不同对象

```text
PC software / BIOS / driver API
        ↓
UART / ACE registers and byte framing
        ↓
line driver + line receiver
        ↓
EIA/TIA-232 electrical + functional interface
        ↓
connector, cable and DTE/DCE mapping
```

它们经常被一句“串口”压成同一个东西，但不能互换：

- UART/ACE 负责并串转换、起止位、奇偶校验和寄存器接口；
- line driver/receiver 在逻辑电平与线路电平之间转换；
- V.28 / TIA-232 的电气要求约束 interchange point 上的电压、阻抗和转换特性；
- V.24 描述 interchange circuits 的功能、方向和 DTE/DCE 语义；
- 25-contact 与 PC 常见 9-contact D-sub 是具体 mechanical mapping，不能反过来定义整个标准；
- BIOS、操作系统和应用看到的是 UART/driver 抽象，不是裸线上的电气状态。

因此正式展品的工作标题应是 **“EIA/TIA-232 family and the PC serial-port implementation”**，而不是把 `RS-232`、`DE-9`、`COM1` 和 `TTL UART` 当作四个同义词。

## 来源总表

证据等级沿用 [`docs/EVIDENCE.md`](../docs/EVIDENCE.md)。“可支持”一栏只列本轮实际检查过的章节，不代表该来源的全部内容。

| ID | 来源与定位 | 等级 | 可支持 | 不能单独支持 |
|---|---|---:|---|---|
| S1 | TIA-232-F-1997, *Interface Between Data Terminal Equipment and Data Circuit-Terminating Equipment Employing Serial Binary Data Interchange*；[封面/目录预览（含 2012 reaffirmation）](<https://www.normsplash.com/Samples/TIA/127475168/TIA-232-F-1997-(R2012)-en.pdf>)。封面使用 `TIA-232-F-1997`，其中复现的 1997 contents page 标为 `ANSI/TIA/EIA-232-F` | E1（仅审阅预览，未取得全文） | 标准身份、正式标题、修订/重申日期与目录范围 | 本轮未读到正文，不能据此声称具体针脚、电压或时序条文 |
| S2 | ITU-T Recommendation V.24 (02/2000), *List of definitions for interchange circuits between DTE and DCE*；[公开全文入口](https://www.itu.int/rec/T-REC-V.24-200002-I/en)，§§1–4，尤其 pp. 1–6、13–17 | E1 | DTE/DCE 边界；103/104、105/106、107、108/2、109、125 等 circuits 的功能、方向和相互关系 | 不应当被写成完整 TIA-232-F 的逐条替代品；§1.2、§1.3 明确把 electrical 与 mechanical 特性委托给别的规范 |
| S3 | ITU-T Recommendation V.28 (03/1993), *Electrical characteristics for unbalanced double-current interchange circuits*；[公开全文入口](https://www.itu.int/rec/T-REC-V.28-199303-I/en)，§§1–7，pp. 1–5 | E1 | interchange point 的等效电路、负载/发生器边界、±3 V 判定区、数据与控制 circuit 的极性语义、转换区与失效检测 | 连接器针脚；PC UART 寄存器；任意具体适配器一定达到的实测值 |
| S4 | ISO 2110:1989 (3rd ed.), *Information technology — Data communication — 25-pole DTE/DCE interface connector and contact number assignments*；[IEC catalog record](https://webstore.iec.ch/en/publication/61738) 与 [Amd 1:1991 record](https://webstore.iec.ch/en/publication/61739)。V.28 Figure 2 note 2 只写无版次的 `ISO 2110`；V.24 §1.3 则把 mechanical characteristics 分派给 ISO/IEC connector standards | E1（仅元数据/交叉引用；未取得全文） | 标准身份、1989/1991 版本边界与 25-contact mechanical mapping 的规范入口 | 实际 contact assignment；1989/1991 文本是否可不变地套用到 IBM 1984 或更早设备 |
| S5 | IBM, *IBM Personal Computer Technical Reference*, April 1984, part no. 6322507；[Internet Archive 扫描](https://archive.org/details/IBMPCIBM5150TechnicalReference6322507APR84)，pp. 3-3、5-8、5-50–5-54、8-2–8-5 | E1 | IBM PC 电源为何给 EIA driver/receiver 提供 ±12 V；BIOS 数据区与 8250；INT 14h 串口服务；当时 IBM 对 DTE/DCE、25-contact RS-232C 与 modem control 的解释 | 后来的 PC DE-9 mapping；所有兼容机；现代 USB 转换器行为 |
| S6 | Texas Instruments, *MC1488, SN55188, SN75188 Quadruple Line Drivers*, SLLS094C；[datasheet](https://www.ti.com/lit/ds/symlink/sn75188.pdf)，pp. 1–4 | E1（器件） | 一类经典 line driver 的逻辑输入、双电源与线路输出；器件声明满足 TIA/EIA-232-E 与 V.28 | 整个接口标准；某块 IBM 卡一定使用哪个具体厂牌/修订器件 |
| S7 | Texas Instruments, *MC1489(A), SN55189(A), SN75189(A) Quadruple Line Receivers*, SLLS095D；[datasheet](https://www.ti.com/lit/ds/symlink/sn75189a.pdf)，pp. 1–4 | E1（器件） | 一类经典 line receiver 的 3–7 kΩ 输入、线路侧输入范围与 5 V logic 输出 | 标准规定与单一器件能力之间不能画等号 |
| S8 | Texas Instruments, *Interface Circuits for TIA/EIA-232-F*, SLLA037A, September 2002；[application report](https://www.ti.com/lit/an/slla037a/slla037a.pdf)，pp. 1–9 | E2 | UART/ACE 与 line interface 的分层；版本沿革；PC 9-contact mapping；modem-control 语义；null-modem 的一个完整示例 | 它把 9-contact shell 称为 “DB9S”，不能据此裁决 D-sub shell-size nomenclature；应用笔记不能覆盖标准原文 |
| S9 | Analog Devices/Maxim, *MAX220–MAX249 +5V-Powered, Multichannel RS-232 Drivers/Receivers*；[datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/MAX220-MAX249.pdf)，pp. 1–7 | E1（器件） | 单 5 V 逻辑系统通过 charge pump 产生线路摆幅的实现例；明确分开 TTL/CMOS pins 与 RS-232 pins | 不能把 MAX232 家族的能力写成所有历史 RS-232 设备的能力 |
| S10 | Cinch, DE9S D-sub connector product page；[manufacturer page](https://www.cinch.com/products/d-shape/connectors/de9s) | E2（机械命名交叉核验） | `DE9` 是厂商仍在使用的 shell/contact nomenclature；可用来标注俗称 `DB9` 的术语风险 | PC serial pin assignment 或 RS-232 兼容性 |
| S11 | OSDev Wiki, [Serial Ports](https://wiki.osdev.org/Serial_Ports) | E2 | 现代可检索的 PC-compatible UART/COM 实践说明与进一步线索 | 电气安全、规范要求、历史上的所有实现 |
| S12 | pinoutguide/pinouts.ru, [PC 9-pin serial port](https://pinoutguide.com/SerialPorts/Serial9_pinout.shtml) | E5 | 常见 PC mapping 的线索与待比较对象 | 未经 S1/S4/原厂手册交叉验证的接线依据 |

### 获取状态说明

- S2、S3 所列章节以及 S5–S12 的内容已在本轮打开核对；外链不等于将原文版权内容提交进仓库。
- 2026-09-01 最终自动化可达性复查中，S1、S4–S9、S11–S12 使用 browser user-agent 返回 200；S10 同样返回 200，但 generic curl 被 403 bot filter 拦截；ITU 的 S2/S3 permalink 从本审计网络返回 500。后两项是当前站点访问限制，不能据此声称文献撤回，也不应写成“所有链接直接返回 200”。
- S1 与 S4 是正式标准入口，但本轮没有取得合法可审阅全文，故明确标为 **未取得全文**。S4 的官方 catalog 将第三版标为 `ISO 2110:1989`，另列 `Amd 1:1991`；V.28 (1993) 的注释只写无版次的 `ISO 2110`，不能据此把 1989/1991 文本倒灌给 IBM 1984 或更早设备。
- S2/S3 是公开可读的国际规范，能先建立功能与电气骨架；它们不是把 S1 悄悄替换掉的借口。
- IBM 扫描的页码使用书内印刷页码，而不是 PDF viewer 的文件页序号。

## 按层整理的 claim ledger

### A. 对象边界：RS-232 不等于 TTL UART

**Claim A1**

```text
UART/ACE 的逻辑侧与符合 232/V.28 的线路侧是两个电气域，通常由 line driver/receiver 隔开。
```

- Layer: electrical / host
- Evidence: S5 pp. 3-3、5-50–5-54；S6 pp. 1–4；S7 pp. 1–4；S8 p. 1；S9 pp. 1–6
- Scope: IBM 5150 implementation + documented transceiver families
- Confidence: confirmed
- Notes: IBM 的 ±12 V 电源供给 EIA drivers/receivers，而 8250 由 BIOS/寄存器层操作；TI SLLA037A 又把 ACE 放在 232 line interface 之前。三者共同支持分层，但不意味着所有实现都必须使用 ±12 V rail 或同一芯片。

**安全结论：** `TX/RX/GND` 名字相似不能证明线路可以直连。没有确认具体设备的 electrical domain 前，不写 TTL UART ↔ RS-232 直连步骤。

### B. Electrical：电压的意义依 circuit 类型而变

**Claim B1**

```text
V.28 在 interchange point 把 data circuit 的 < -3 V 解释为 binary 1、> +3 V 解释为 binary 0；
对 control/timing circuit，则 > +3 V 为 ON、< -3 V 为 OFF。
```

- Layer: electrical / signaling
- Evidence: S3 §5、Table 1，pp. 3–4
- Scope: V.28 documented requirement
- Confidence: confirmed
- Notes: “正电压就是 1”或“负电压就是 OFF”都不是可跨 circuit 类型使用的说法。`mark/space`、`binary 1/0` 与 `ON/OFF` 必须分别写。

**Claim B2**

```text
V.28 的合规边界在规定负载下定义；发生器开路电压、短路电流、负载电阻与电容都属于接口要求的一部分。
```

- Layer: electrical
- Evidence: S3 §§2–6，pp. 1–4
- Scope: V.28 documented requirement
- Confidence: confirmed
- Notes: 后续展品应引用 clause，而不是只摘“±12 V”这一种典型实现值。V.28 §4 给出的 open-circuit generator magnitude 上限是 15 V，并注明现场旧设备可能达到 25 V；这也是不能把 3.3/5 V UART 直接接上的原因之一。

### C. Roles：TX/RX 方向取决于 DTE/DCE 视角

**Claim C1**

```text
V.24 circuit 103 (Transmitted data) 是 To DCE；104 (Received data) 是 From DCE。
RTS/DTR 来自 DTE，CTS/DSR/received-line-signal detector 来自 DCE。
```

- Layer: protocol / ecosystem
- Evidence: S2 Table 1 and §§3.5–3.12，pp. 3–7；S5 pp. 8-2–8-5
- Scope: DTE/DCE interface semantics
- Confidence: confirmed
- Notes: 后续 physical page 不应只列 “TX pin / RX pin”，还要给观察视角。IBM 的同期说明有助于恢复这些信号原本围绕外置 modem 建立连接的语境。

**Claim C2**

```text
RTS/CTS、DTR/DSR 等不是 UART 字节本身的一部分，而是独立 interchange/control circuits；
具体应用可以只实现其中一部分。
```

- Layer: protocol / host
- Evidence: S2 §§4.1–4.6，pp. 13–17；S8 pp. 7–9
- Scope: V.24 semantics + later PC implementation guidance
- Confidence: supported
- Notes: V.24 §4.5 明确讨论 complementary equipment 未提供某些 circuits 的情况。正式展品要区分标准功能、PC 常见 subset 和某台设备的 wiring。

### D. Mechanical：25-contact 标准路径与 PC 9-contact 惯例分开

**Claim D1**

```text
V.24 本身不把一种连接器形状当作全部接口：§1.2 指向 electrical Recommendations，
§1.3 再分别指向 25/26/37/50-pole mechanical standards。
```

- Layer: physical / model boundary
- Evidence: S2 §§1.2–1.3，p. 2
- Scope: V.24 (2000) document structure
- Confidence: confirmed

**Claim D2**

```text
IBM 5150 资料展示 25-contact RS-232C modem connection；后来的 PC 9-contact mapping 是缩减后的 PC implementation，
不能用 9-contact connector 反向定义 RS-232 family。
```

- Layer: physical / ecosystem
- Evidence: S5 pp. 8-3–8-4；S8 pp. 1–3、7–9
- Scope: IBM 5150 + TI's 2002 PC implementation account
- Confidence: supported
- Notes: S8 自己称其 9-contact PC interface 是 full 232 的 subset。

**术语决定：** 展品正文用 `DE-9 (often called “DB-9” in PC documentation)`。S8 的 “DB9S” 保留为来源原词；S10 只交叉核验 D-sub shell 命名，不拿来证明 serial mapping。

### E. Host integration：COM port 不是插头的别名

**Claim E1**

```text
IBM PC BIOS 把串口暴露为 8250 base address、状态位和 INT 14h 服务；
这是 host/software integration，不能从连接器针脚表推出。
```

- Layer: host
- Evidence: S5 pp. 5-8、5-50–5-54
- Scope: IBM 5150 BIOS documented implementation
- Confidence: confirmed
- Notes: pp. 5-50 onward的 BIOS listing 给出初始化、发送、接收和状态路径，并读取 line/modem status。正式展品需要把这一层与 V.24 control circuits 对齐，但不能声称后来的 OS 必须通过 BIOS 调用。

## 已发现的冲突与易错点

### 1. “V.24 等同于 RS-232C”只能当同期表述保存

IBM S5 p. 8-3 直接称 V.24 “equivalent to” RS-232C。当前 S2 却明确把 functional circuits、electrical characteristics 与 mechanical connector 分派给不同 Recommendations/ISO standards。

处理方式：

- 在历史页引用 IBM 的同期说法，说明当时面向使用者的等同表达；
- 在技术分层中采用当前规范自身的边界；
- 不写 `V.24 = RS-232` 这种无版本、无层次的恒等式。

### 2. `DB-9` 是常见名，不是可以悄悄规范化的名

TI S8 使用 “DB9S”，大量 PC 文档也沿用 `DB9`；连接器厂商 S10 将该 9-contact shell 列为 `DE9`。两种词都应该可检索，但正文必须让读者知道它们不是两种不同的 PC 串口。

处理方式：

- canonical label: `DE-9`；
- aliases: `DE9`, `DB-9`, `DB9`；
- 引用来源时不改写来源标题或图注；
- 不因外壳同为 DE-9 就推断 protocol/electrical compatibility。

### 3. Null modem 不是唯一一根“标准线”

S8 Figure 7 给出一个 full-handshake null-modem 示例；现实中还会见到只交叉 data、局部回环 control 或不同 flow-control 假设的变体。

处理方式：

- `null modem` 作为 DTE↔DTE role adaptation 解释；
- 每个 wiring variant 必须命名其 handshake 假设与适用范围；
- 在 S1/S4 与至少一份设备手册交叉核验前，不发布可执行 pin-to-pin 接线表。

### 4. “9600 baud”不能自动写成完整吞吐量

UART 的 start/stop/parity framing、modem symbol rate 与 application bytes/s 不是一个单位。S5 的 BIOS 参数表能证明 IBM 支持的配置路径，不能证明线路上每秒交付多少有效字节。

处理方式：正式 protocol/host pages 分别记录 bit/s、symbol/s（若适用）、frame format 与 payload throughput，不混用 `baud`。

### 5. 现代 USB–serial adapter 不是透明时间机器

USB bridge 可能省略 modem-control lines、使用不同 transceiver、做 buffering，并由现代 driver 暴露为 tty/COM device。一次 loopback 只能说明 adapter + driver + configuration。

处理方式：任何 E4 实测都记录 vendor/product ID、bridge/transceiver（能确认时）、driver、OS、line settings、使用的 signals、测量工具和限制。

## 二手资料查重结果

| 资料 | 已经擅长的内容 | 本项目不重复 | 可新增的博物馆价值 |
|---|---|---|---|
| pinoutguide/pinouts.ru (S12) | 快速查常见 PC 9-contact pin label | 再造一张无语境 pinout | 把 pin label 还原到 DTE/DCE role、line electrical、UART/BIOS 与 modem-era use |
| OSDev Serial Ports (S11) | PC-compatible UART port programming | 复制寄存器教程 | 把软件可见 register/status 与 V.24 circuits、line transceiver 和历史用户体验连起来 |
| TI SLLA037A (S8) | 232 electrical 概览、PC mapping、器件选择 | 改写应用笔记 | 用标准/同期 IBM 资料审计其简化和术语，再展示 25-contact → PC 9-contact 的历史缩减 |

## 正式 exhibit 的安全施工顺序

### Gate 1 — 必须先补齐

- [ ] 合法取得并审阅 TIA-232-F 全文，记录版次、clauses 与勘误/重申状态；
- [ ] 合法取得并审阅 ISO 2110 的相关版次：以 1989 第三版及 Amd 1:1991 核对 V.28-era mapping；若比较 IBM 1984，则另查当时有效的 1980 第二版，不能以后版倒灌；
- [ ] 找到 IBM 9-contact serial implementation 的原厂 technical reference，用来交叉核验 S8；
- [ ] 把 RS-232C、EIA-232-D、TIA/EIA-232-E/F 的版本变化做成单独表，不把后版条文倒灌给 1981 设备。

### Gate 2 — 可以先写、不涉及接线

- [ ] `README.md`：生命周期、modem → general peripheral/console use、退出主流的范围；
- [ ] `protocol.md`：DTE/DCE、103/104 与 modem control；
- [ ] `host-integration.md`：IBM 8250/BIOS 个案，再与现代 tty/COM 抽象分开；
- [ ] `descendants.md`：只建立有 layer/scope 的关系，不写“USB 直接替代 RS-232”这种跨层一句话。

### Gate 3 — 有明确设备后才做

- [ ] 为一只可替换 USB–serial adapter 建立 datasheet/source record；
- [ ] 先做 connector continuity 与无电安全核验，再决定 loopback fixture；
- [ ] 若测线路电压/波形，记录 probe point、input limits、sample rate、driver 与 line settings；
- [ ] 把 software loopback、adapter line-side measurement 与真实 legacy DTE↔DCE 分成三个实验，不互相代替。

## 建议的首个可重复实验（尚未执行）

首个实验不应宣称“测量 RS-232 标准”，而应命名为：

> **指定 USB–serial adapter 的 local loopback 与 line-side sample**

最低记录字段：

```yaml
adapter_vendor_product_id: pending
bridge_chip: unknown
line_transceiver: unknown
os_driver: pending
connector_mapping_source: pending
signals_used: [pending]
line_settings: pending
measurement_tool: pending
probe_point: pending
sample_rate: pending
result_scope: this adapter and setup only
```

在这些字段未完成、S1/S4 未交叉核验前，实验状态是 `blocked-for-hardware`，但 source review 与软件层研究可以继续。

## Source map 验收

- [x] 定位正式 TIA 标准入口，并明确全文缺口；
- [x] 用公开 E1 规范分别覆盖 functional (V.24) 与 electrical (V.28)；
- [x] 用同期 IBM technical reference 覆盖 PC host integration 与 modem 语境；
- [x] 用 driver/receiver datasheets 证明 UART logic 与 line electrical 不可混同；
- [x] 审计 PC 9-contact、`DB9`/`DE-9` 与 null-modem 术语风险；
- [x] 把 pinout database 与 OSDev 降为线索/实践性二手资料；
- [x] 给出不会越过硬件安全门禁的下一步施工顺序。

这份地图的价值不是“已经知道第几脚是什么”，而是现在知道：**每一类结论应该回到哪份资料、哪些结论目前还不能安全地写。**
