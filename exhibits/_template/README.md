# <Exhibit name>

> One sentence: what object is this exhibit actually about, and at what layer(s)?

## Identity

- **Exhibit ID:** `<slug>`
- **Object kind:** connector / electrical-standard / signaling-system / protocol / command-model / bus / host-interface / device-interface / ecosystem
- **Aliases:**
- **Introduced:**
- **Mainstream era:**
- **Decline / replacement era:**
- **Status:** stub / researching / documented / experimented / reviewed

Do not use a familiar connector name as shorthand for a whole protocol family unless the sources justify that scope.

## The ten museum questions

1. When did it appear?
2. What original problem/use case did it address?
3. What is the physical interface, if any?
4. What electrical rules apply?
5. How are data, clock, control, power and handshaking separated?
6. How are devices addressed/selected/arbitrated, if applicable?
7. How does the host/OS discover, configure and drive it?
8. What did users actually have to understand or configure?
9. Why did it leave the mainstream?
10. What ideas, command models or constraints survived into descendants?

## Layer map

| Layer | What belongs here | Status |
|---|---|---|
| Physical | connector, cable, keying, pin count, mechanical constraints | unknown |
| Electrical | voltage/current, drivers, termination, impedance, grounding | unknown |
| Signaling | serialization, clocking, handshaking, timing | unknown |
| Protocol | frames, commands, roles, arbitration, discovery | unknown |
| Host integration | controller, registers, IRQ/DMA, firmware, driver/OS model | unknown |
| Ecosystem | devices, configuration pain, market role, replacement path | unknown |

If a layer is not applicable, mark it `not-applicable` and explain why rather than inventing content.

## What users experienced

Describe the interface as a historical user or technician encountered it: what had to be plugged, jumpered, terminated, configured, rebooted, selected, or debugged?

## What this exhibit contributes

State what is new compared with a pinout database: cross-layer explanation, source reconciliation, reproducible experiment, historical comparison, or measured artifact.

## Evidence status

- Highest evidence level:
- Primary/contemporary sources used:
- Emulation status:
- Hardware status:
- Safety blockers:
- Open conflicts:

See `docs/EVIDENCE.md` and `docs/HARDWARE-SAFETY.md`.

## Files

- `physical.md` — connector/cable/mechanical layer
- `electrical.md` — levels, drivers, termination, timing limits
- `protocol.md` — signaling/roles/commands/transfer model
- `host-integration.md` — controller, resources, firmware/OS/driver
- `experiment.md` — reproducible emulation or hardware experiment
- `descendants.md` — replacement and inheritance relationships
- `sources.md` — source ledger with evidence levels
- `exhibit.json` — machine-readable summary validated by `schemas/exhibit.schema.json`
