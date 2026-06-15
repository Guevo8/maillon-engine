# Bot Architecture Overview

## Current Module Map

```
src/maillon_v04/
├── bot.py                   ← re-export facade (backwards compatibility only)
├── bot_registry.py          ← BotPolicy Literal, choose_bot_action() dispatcher
├── bot_legacy.py            ← choose_rusher_action, choose_phase_player_action + helpers
├── bot_personality.py       ← personality ID registry + phase-specific weight tables
├── bot_utility.py           ← utility scoring engine (candidate gen, scoring, selection)
├── bot_utility_tunneler.py  ← tunnel-action overlay (feature scoring + opportunity cost)
├── bot_tunnel_probe.py      ← simple priority-tree tunnel probe (no scoring)
└── bot_exploit.py           ← calibration probe bots (opening_resource_spammer, tunnel_all_in_probe)
```

`docs/` and `analysis/` are outside `src/` and contain no runtime code.

---

## Policy Dispatch: `bot_registry.py`

`bot_registry.py` contains the canonical dispatcher implementation; `bot.py` remains the backwards-compatible import facade. Every policy call goes through:

```python
choose_bot_action(state: GameState, actor: ActorId, policy: BotPolicy) -> Action
```

`BotPolicy` is a `Literal` type covering all twelve currently registered policies:

```
"rusher"                "phase_player"
"utility_balancer"      "utility_rusher"       "utility_economist"
"utility_fortifier"     "utility_aggro_turtle" "utility_opportunist"
"tunnel_probe"          "utility_tunneler"
"opening_resource_spammer"  "tunnel_all_in_probe"
```

### Dispatch order inside `choose_bot_action`

| Priority | Policy | Implementation |
|---|---|---|
| 1 | `rusher` | `choose_rusher_action()` — defined in `bot_legacy.py` |
| 2 | `phase_player` | `choose_phase_player_action()` — defined in `bot_legacy.py` |
| 3 | `tunnel_probe` | `choose_tunnel_probe_action()` from `bot_tunnel_probe.py` |
| 4 | `utility_tunneler` | `choose_utility_tunneler_action()` from `bot_utility_tunneler.py` |
| 5 | `opening_resource_spammer` | `choose_opening_resource_spammer_action()` from `bot_exploit.py` |
| 6 | `tunnel_all_in_probe` | `choose_tunnel_all_in_probe_action()` from `bot_exploit.py` |
| 7 | `utility_*` | `choose_best_utility_action(state, actor, personality)` from `bot_utility.py`, personality resolved via `UTILITY_POLICY_TO_PERSONALITY` |

---

## Bot Categories

### Legacy Bots (`bot_legacy.py`)

`rusher` and `phase_player` were the original handcrafted bots before the utility system existed. Their decision logic — including helper functions like `choose_rusher_action`, `choose_phase_player_action`, `conservative_fortify_action`, and `rusher_finish_build_action` — lives in `bot_legacy.py`.

Both use explicit priority trees with deterministic coordinate tie-breaking (distance to opponent core, then `(x, y)`). No weighted scoring. No personality.

### Utility Bots (`bot_utility.py` + `bot_personality.py`)

Six policies: `utility_balancer`, `utility_rusher`, `utility_economist`, `utility_fortifier`, `utility_aggro_turtle`, `utility_opportunist`. All share the same scoring engine; only the personality weight tables differ.

See `docs/utility_weighting_mechanics.md` for the full scoring pipeline.

### Probe Bots (`bot_exploit.py`)

Purpose-built calibration instruments that test a single hypothesis each. Not intended to be competitive in themselves — they measure whether a specific extreme strategy is viable.

**`opening_resource_spammer`** — hypothesis: "Securing 2 Holz + 2 Korn quickly, then converting all resources into build/raid with zero delay beats cautious bots." No fortify, no upgrades, no rebuild.

Priority tree: build Holz (until 2) → build Korn (until 2) → raid → build (expansion, Korn-or-Holz based on cap pressure) → wait.

**`tunnel_all_in_probe`** — hypothesis: "Forcing maximum tunnel pressure as fast as possible is advantageous, even at collapse risk." Skips surface build/raid entirely until all tunnel options are exhausted. No collapse avoidance.

Priority tree: tunnel_raid → repair_build → tunnel_extend → tunnel_entrance → surface build → wait.

### Tunnel Priority-Tree Probe (`bot_tunnel_probe.py`)

`tunnel_probe` is an earlier, simpler probe that demonstrates the tunnel action set is reachable. It uses a handcrafted priority tree (same style as the legacy bots) but extends it with tunnel actions ranked above surface actions. No feature scoring. Includes surface fallbacks (raid, field_upgrade, core_upgrade, rebuild).

### Tunnel Feature-Scoring Overlay (`bot_utility_tunneler.py`)

`utility_tunneler` is a separate scoring overlay — not a variant of the utility engine. It scores only tunnel actions (plus `wait`) using explicit features, then compares the best tunnel score against a `balancer`-personality baseline before deciding whether to play a tunnel action or fall back to the normal utility system.

See `docs/utility_weighting_mechanics.md` §Tunneler Overlay for details.

---

## Why `bot.py` Is a Compatibility Facade

The three original concerns of `bot.py` — policy dispatch, legacy bot logic, and shared helpers — have been extracted into separate modules:

| File | Contains |
|---|---|
| `bot_registry.py` | `BotPolicy` Literal, `UTILITY_POLICY_TO_PERSONALITY`, `choose_bot_action()` dispatcher |
| `bot_legacy.py` | `choose_rusher_action`, `choose_phase_player_action`, and all their helpers |
| `bot.py` | Re-exports only, kept for backwards compatibility |

`bot.py` is now a thin re-export facade: it imports and re-exports `choose_bot_action`, `BotPolicy`, `UTILITY_POLICY_TO_PERSONALITY` from `bot_registry.py`, and the legacy helpers from `bot_legacy.py`. Callers that imported from `bot.py` continue to work.

---

## Dependency Graph (current)

```
bot_registry.py  (canonical dispatcher)
├── bot_legacy.py           (choose_rusher_action, choose_phase_player_action + helpers)
├── bot_exploit.py          (probe bots)
├── bot_tunnel_probe.py     (priority-tree tunnel probe)
├── bot_utility_tunneler.py
│   ├── bot_utility.py      (baseline scoring)
│   └── tunnels.py / tunnel_collapse.py / tunnel_rules.py
└── bot_utility.py
    └── bot_personality.py

bot.py → re-export facade; imports from bot_registry.py + bot_legacy.py
```

`actions.py` is imported by most bot modules for the `affordable_*_targets()` family of functions.
