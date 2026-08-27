# Signaling and protocol

## Scope

Separate raw signaling/timing from the protocol or command model carried on top of it.

## Signaling model

- Serial / parallel:
- Synchronous / asynchronous:
- Clock source / recovery:
- Bit/word ordering:
- Framing:
- Handshake / flow control:
- Error detection / retry:

## Roles and topology

- Host / device or peer roles:
- Initiator / target or equivalent:
- Point-to-point / multidrop / shared bus:
- Addressing / IDs:
- Arbitration / bus ownership:

## Commands / transactions

Describe the smallest useful transaction without assuming a particular OS driver.

```text
precondition
→ request / command
→ data phase
→ status / response
→ error / retry path
```

## Versions and extensions

Keep baseline behavior separate from later extensions, vendor conventions, and compatibility modes.

## Layer-boundary warnings

- A connector is not a protocol.
- A UART data stream is not automatically RS-232 electrical signaling.
- A command family may survive after its original physical bus disappears.

## Evidence

For timing, framing and command semantics, link each major claim to the relevant source ID in `sources.md`.
