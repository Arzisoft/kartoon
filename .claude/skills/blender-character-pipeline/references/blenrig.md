# BlenRig — Feature-Film-Quality Auto-Rig + Facial System

Free, open source. Repo: https://github.com/jpbouza/BlenRig (160+ stars). Used by Blender
Studio itself (official training exists at studio.blender.org/training/blenrig). Recommended
in this project over plain Rigify specifically for its facial rig — needed for Rhubarb
lip-sync + expressions.

**Not yet installed in this project** — evaluated via research, not hands-on. Install/apply
before relying on details below; confirm current UI against whatever version ships.

## Requirements
- Blender 4.0+ (3.x no longer supported as of BlenRig v4.0.0)
- **Biped characters only** (current version) — matches this project's redesigned Zayn/Milo,
  did NOT match the original quadruped Zayn (archived `v2-quadruped`).

## Basic workflow (per project README)
1. Access via Object Add Panel > Armature menu.
2. Controls live in the View3D Sidebar (N key).
3. Use the **Rigging Assistant**'s "Automated Rigging Guides" to streamline fitting the rig
   to a custom character.
4. **Weight Transfer Meshes** feature automatically weights characters — relevant for
   transferring weights onto our AutoRemesher-retopologized meshes.
5. Facial system: "one of the most advanced facial rigs available" — includes automatic
   shapekey/driver generation (v2.1.0+ "Shapekeys Sculpting Workflow") rather than hand-built
   blend shapes for every expression.

## Why this over plain Rigify for this project
Plain Rigify has no dedicated facial-rig system out of the box. Rhubarb Lip Sync needs mouth
shapes to drive, and toddler-show expressiveness needs a real facial rig, not just body bones.
BlenRig's automatic shapekey/driver generation is a large amount of otherwise-manual work
(dozens of hand-sculpted blend shapes) done for you.

## Open questions for actual setup (resolve when installing)
- Exact mesh-orientation/naming requirements for fitting the auto-rig guides to a non-human
  biped (camel head, budgie head) — the README doesn't detail this, will need hands-on
  testing.
- Compatibility with AutoRemesher's output topology vs. BlenRig's own expected topology
  conventions.
