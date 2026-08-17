# Hunyuan Motion — Text-to-3D-Motion

Tencent, open source (billion-parameter model). Site: hunyuanmotion.net. Generates humanoid
skeleton animation clips from plain-English text prompts — ~50x faster than traditional
motion capture per Tencent's own claim.

**Not yet installed/used in this project** — evaluated via research. Locked into the pipeline
stack (see `bible/production-notes.md`) but no animation has actually been generated yet.

## Why this matters for the pipeline
Both Zayn and Milo were redesigned from quadruped/bird to **bipedal specifically because
Hunyuan Motion (and every other humanoid motion source) only emits humanoid skeletons** — a
quadruped rig had nothing to retarget onto. This was Ali's key insight in the bipedal
redesign (PR #1).

## How to run it
- **Web demo:** free, browser-based, on Hugging Face Spaces — no local setup, good for
  quick tests.
- **Local install:** clone the repo, install dependencies, download model weights from
  Hugging Face, run the demo script with a text prompt. Needs Python 3.10+.
- **Hardware:** full model needs 24GB+ VRAM (RTX 4090/A100 class); a lighter 460M-parameter
  version needs 14GB+. **The Jetson Orin Nano's 8GB GPU will likely need the lighter model,
  or won't fit at all** — check the smaller checkpoint's actual VRAM footprint before
  assuming Orin can run this.

## Input/output
- **Input:** a plain-English (or Chinese) motion description, e.g. "A person walks forward
  confidently, turns left, and continues walking with their arms swinging naturally."
- **Output:** SMPL/SMPLH skeleton format, exportable to FBX, BVH, or others.
- **Into Blender:** import the FBX and apply the animation to the character's rig — standard
  Blender animation-retargeting workflow (bone name/proportion matching between the SMPL
  skeleton and our rig still needs to be verified once we actually try this).

## Open question for this project
Whichever rig we settle on (Rigify vs. BlenRig) needs bone names/hierarchy compatible enough
with the SMPL/SMPLH skeleton for retargeting to work smoothly — not yet verified hands-on.
