# AGENTS.md — Obsolete Interface Museum

本仓是可操作的接口技术史博物馆，不是 pinout 抄表站，也不是危险硬件实验指南。

## 开工前阅读

先读 `README.md`、`ROADMAP.md`、`IMPLEMENTATION_PLAN.md`、`docs/PRIOR_ART.md`，再读当前 exhibit/lab 相关文件。

## 必须保持的层次

任何展品都应尽量区分：

```text
physical connector
→ electrical characteristics
→ signaling/timing
→ protocol/command model
→ host/OS integration
→ real hardware ecosystem
```

禁止把“同一种插头”“同一协议家族”“同一电气层”混为一件事。例如 SCSI 不能等同于某个 50-pin 连接器，RS-232 也不能等同于 TTL UART。

## 证据等级

关键结论优先使用：

1. 标准/原厂手册/同时代技术资料；
2. 可靠的后续技术文档与博物馆资料；
3. 仿真/模拟器行为；
4. 自己的实测；
5. 二手 pinout/论坛/博客仅作辅助。

仿真结果不得写成真实电气结论；单台设备实测不得代表整个标准。

## 硬件安全

- 未经标准/原厂资料交叉验证的 pinout 不得指导接线；
- 不对昂贵、不可替代、状态未知的老硬件做风险热插拔；
- 不把 TTL、RS-232、电源轨等不同电平直接相连；
- 真实实验必须记录设备、适配器、测量工具、probe point、sample rate、软件/driver 与局限；
- 不因为“看起来插得进去”就认为兼容。

## 默认施工循环

1. 检查当前仓库状态；
2. 从 `IMPLEMENTATION_PLAN.md` 选择最早可做任务；
3. 先做 source map/术语清理；
4. 建立 exhibit 跨层结构；
5. 有安全条件再做仿真/实测；
6. 标注证据等级和不确定性；
7. 提交 checkpoint；
8. 继续下一依赖安全任务。

## 完成定义

展品不是“有一张针脚表”就完成。至少要回答其物理、电气、信号/协议、主机集成、历史痛点、退出原因与继承关系中的本阶段要求，并有可追溯来源。

## Stop conditions

- pinout 未交叉验证；
- 需要风险接线/热插拔；
- 仿真被误当实测；
- 层次概念混乱；
- 只是复制现有 pinout 数据库；
- 关键结论没有权威资料支撑。
