# Electrical layer

## Scope

Document what a wire electrically means before discussing higher-level protocol semantics.

## Signaling characteristics

- Single-ended / differential:
- Nominal logic or analog levels:
- Receiver thresholds:
- Driver characteristics:
- Reference ground / common mode:
- Idle state:
- Pull-up / pull-down / biasing:
- Open-collector/open-drain behavior:

## Power

- Does the interface carry power?
- Which side sources it?
- Voltage/current limits:
- Is power optional or mandatory?

## Termination and signal integrity

- Required termination:
- Characteristic impedance, if specified:
- Stub/topology constraints:
- Documented cable-length/rate relationship:

## Electrical safety boundary

Before any hardware experiment, explicitly record the E1 source used to verify levels, direction, power and hot-plug assumptions. If unknown, mark the experiment `blocked-for-hardware`.

## Measured vs specified

Keep these separate:

```text
Specified by standard/manual:
Measured on device/setup:
Emulated/not electrically modeled:
```
