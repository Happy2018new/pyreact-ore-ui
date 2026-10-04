# Page Capture Routes

Recipes contain `steps` with `move`, `click`, `scroll`, `drag`, `key`, and bounded
`wait`. Coordinates are normalized client pixels. Store recipes alongside their
before/after captures, version and client size. `run` never retries input after
a focus failure. Inspect the current page before resuming unfinished steps.

```json
{"steps":[{"do":"click","at":[0.5,0.5]},{"do":"wait","ms":800}]}
```

At the home page locate the Settings and Play commands from the capture.
Settings opens Ore navigation: capture Accessibility, General, Video and Touch,
including scroll positions containing switches, fields, continuous/stepped
sliders, dropdowns, headings and disabled rows. Hover both selected and unselected
navigation entries; click another category and capture selection separately.

Play opens the World/Realms/Servers tab bar and world cards. Locate a world edit
pencil, open its settings without entering the world, and capture General,
Advanced and Multiplayer. Observe segmented choices, setting-row separators,
toggle normal/hover/pressed, dropdown normal/open/option hover/close hover,
slider normal/hover/disabled and integer stop positions. Do not save changed
world configuration; restore temporary values before leaving.

For Pyreact comparisons the client pixel size is not its logical layout size.
Record both. Match the measured scale to international controls. Preserve a
native screenshot and a separate aligned comparison, never overwrite raw pixels.

## Observed route on international 1.26.5203.0

These points were verified in a 2015×1162 client on 2026-10-04. Inspect the
starting page first; coordinates are examples for this version and size.

| Start page | Destination | Normalized click |
| --- | --- | --- |
| Home | Settings | `[0.5, 0.577]` |
| Home | Play | `[0.5, 0.47]` |
| Settings, initial sidebar | Video | `[0.1, 0.91]` |
| Play, world grid | First world's edit pencil | `[0.29, 0.644]` |
| World edit, initial sidebar | Advanced | `[0.15, 0.791]` |
| World edit, initial sidebar | Multiplayer | `[0.15, 0.873]` |
| Settings or world edit | Back | `[0.021, 0.037]` |

Wait at least 100 ms after moving before clicking or scrolling. A large single
wheel event can be coalesced; inspect scroll position or drag the measured
scrollbar. Screenshots have a same-stem JSON sidecar, so put recipe JSON in a
separate `recipes` directory to avoid overwriting it.
