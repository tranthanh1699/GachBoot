# Tool AI Handover

This folder is the handover package for the AI that will develop the PC flashing tool.

The tool must be developed outside the `Boot` firmware folder. Recommended implementation folder:

```text
Tool/flashing_tool/
```

Authoritative bootloader protocol documents:

- `Boot/bootloader/docs/flashing_protocol.md`
- `Boot/bootloader/docs/bootloader_flow.md`
- `Boot/bootloader/docs/memory_map.md`

Read this handover folder first, then use the bootloader docs above as the protocol contract.

## Files

| File | Purpose |
|---|---|
| `tool_ai_requirements.md` | Functional and quality requirements for the Python/Qt tool |
| `tool_ai_flashing_flow.md` | Required user and protocol flashing flow |
| `tool_ai_protocol_contract.md` | Stable frame, command, payload, response, and error contract |
| `tool_ai_development_plan.md` | Milestones and validation expected from Tool AI |
| `flowcode/flashing_client_flow.pseudo` | Pseudocode for the flashing client service |
| `flowcode/frame_codec_flow.pseudo` | Pseudocode for frame encode/decode |

## Current Bootloader Status

The bootloader protocol, frame codec, session handling, and UART receive path exist.
STM32H7 flash erase/write and final firmware CRC/valid-marker handling are still stubbed until hardware validation.

The tool should still implement the full protocol flow now, but it must handle `ERROR_RESPONSE` cleanly when firmware write/finalization is not yet available on the target.
