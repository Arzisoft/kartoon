# Session cleanup — 2026-08-18

Scripts and renders superseded by the current pipeline, archived so `build/` only carries what's
actually live. Nothing here is deleted — all of it is real, working code, just not the current
path.

**Superseded scripts** (replaced by `cycles_sss_test.py` + `procedural_hand.py`, both still in
`build/`):
- `zayn_pose.py`, `zayn_final.py` — the hands-on-hips armature-pose experiment. Contains
  reusable, documented armature-building code (bone creation from `ZAYN_JOINTS`, auto-weight
  skinning, bone-parenting pattern for extremities) — worth reading before rebuilding the pose
  pass, not worth running as-is (predates the current proportions and procedural hands).
- `lineup_polish.py`, `lineup_toon.py`, `milo_polish.py`, `toon_test.py` — Milo/toon-shader
  exploration from before the session locked into the Cycles/SSS direction for Zayn. Milo is
  paused, not abandoned — these are where to pick back up when his turn comes.
- `zayn_polish.py`, `_debug_eyes.py`, `_milo_silhouette_check.py`, `read_tests.py` — one-off
  debug/diagnostic scripts from earlier iteration passes.

**Superseded renders**: `cycles_sss_closeup.png`, `cycles_sss_test.png`, `zayn_final.png` — old
single-frame previews from before the turnaround-loop render setup. The current best state is
`build/zayn_turnaround_{front,quarter,right,back,left}.png` (in `build/`, not here).
