# Host / OS integration

## Controller boundary

- Which controller/chipset/adapter terminates the interface on the host?
- Which registers, ports, memory windows or descriptors are visible to software?
- Which parts are firmware-configured versus OS-configured?

## Discovery and configuration

- Fixed resources / jumpers / DIP switches:
- Firmware enumeration:
- Plug-and-play mechanism:
- Device IDs / class codes / signatures:
- User-visible configuration burden:

## Interrupts and DMA

- Interrupt model:
- DMA model:
- Shared/exclusive resources:
- Typical conflict modes:

## Driver path

Describe a minimal path:

```text
application / user action
→ OS subsystem
→ driver
→ controller/register/descriptor
→ interface transaction
→ device response
```

## Era-specific behavior

Separate historical PC-compatible conventions from properties of the interface standard itself.

## Reproducibility

If using QEMU/86Box/PCem/MAME/etc., record emulator version, machine profile, device model and exact configuration. Emulator behavior is E3 evidence.
