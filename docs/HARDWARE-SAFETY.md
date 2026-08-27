# Hardware safety

本项目可以研究真实旧硬件，但默认目标是**理解接口**，不是证明某块不可替代设备能承受多少误操作。

## 默认规则

1. 不凭连接器外形判断兼容。
2. 不凭单个网络 pinout 接线。
3. 未确认电平、方向、地参考和供电关系前不连线。
4. 未确认标准/设备明确支持 hot-plug 前，按“不支持”处理。
5. 状态未知、昂贵、稀有、不可替代设备不承担探索性风险。
6. 能用仿真、breakout、廉价适配器和可替换设备验证的问题，优先不用古董硬件验证。

## 接线前检查表

真实连线前至少回答：

- 两端连接器型号是否只是“长得一样”？
- 每一端的角色是什么：host/device、DTE/DCE、initiator/target 等？
- 信号是单端还是差分？参考地是什么？
- 逻辑/电气标准是什么？允许电压范围是什么？
- 是否存在供电针脚？谁向谁供电？
- 输出对输出短接是否可能发生？
- 是否需要 termination / pull-up / open-collector/open-drain 条件？
- 线缆是否有方向、交叉、twist、阻抗或长度要求？
- 是否允许带电插拔？
- 错接时最坏会损坏什么？

如果其中任一安全关键项未知，实验状态为 `blocked-for-hardware`。

## 电平隔离

必须明确区分：

- TTL/CMOS logic；
- RS-232 类双极性电平；
- differential signaling；
- 总线供电轨；
- analog/joystick/MIDI 等可能共享连接器时代生态但电气不同的接口。

“协议上能翻译”不代表“导线可以直连”。需要 transceiver/level shifter 时必须写出来。

## 测量优先级

推荐从低风险到高风险：

1. 查标准/原厂资料；
2. 仿真/模拟器；
3. 断电连续性检查；
4. breakout + 限流/隔离条件；
5. 逻辑分析仪；
6. 示波器；
7. 真实双端设备互连。

测量工具本身也有输入限制，probe ground 可能造成短路；任何示波器实验都应先确认接地方式。

## 真实实验记录模板

```text
Experiment ID:
Date:
Device A:
Device B / adapter:
Cable / breakout:
Power state:
Measurement tool:
Probe point:
Sample rate / bandwidth:
Software / driver:
Expected behavior:
Observed behavior:
Safety assumptions verified from:
Uncertainty / limitations:
Evidence level: E4
```

## 禁止的捷径

- “网上都这么接”；
- “插头能插进去”；
- “USB 转接器会自己保护”；
- “我只通电几秒”；
- “这台机器便宜所以可以乱试”；
- 用一台设备的实测反推完整标准。

## 仿真不是退而求其次

对于 IRQ/DMA 冲突、寄存器访问、命令流程、枚举前后的用户体验等问题，仿真往往比真实老机器更可重复。只有当研究问题本身涉及真实电气、时序容差、线缆、终端或具体实现差异时，实测才不可替代。
