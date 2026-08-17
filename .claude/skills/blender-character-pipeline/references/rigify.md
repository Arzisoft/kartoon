# Rigify — Blender's Built-in Auto-Rigging Addon

Free, ships with Blender. Source: Blender Manual (docs.blender.org), Blender Developer Docs,
CGDive's "Rig Anything with Rigify" series.

## Enable it
Edit > Preferences > Add-ons > search "Rigify" > enable > save preferences. (Already enabled
programmatically in this project's `rig_test.py` via
`bpy.ops.preferences.addon_enable(module='rigify')`.)

## Core workflow

1. **Add a metarig** — Shift+A > Armature > Human (Meta-Rig), or build a custom one from a
   single bone (Add > Armature > Single Bone) for non-human body plans.
2. **Position bones in Edit Mode** to match the character's proportions. Each bone gets a
   `rigify_type` assignment (in the Bone properties) that determines what rig component gets
   generated there (e.g. `limbs.arm`, `spines.basic_spine`).
3. **Generate** — in Armature properties, click "Generate". Rigify reads every bone's
   `rigify_type`, instantiates the matching rig component (controls, mechanism bones,
   deformation bones), sets up parenting/constraints, and builds custom control-bone shapes.
   Produces a separate generated rig object — the metarig itself is left untouched and can be
   regenerated repeatedly while iterating.
4. **Bind the mesh** — select the character mesh, then shift-select the generated rig
   (rig must be active), Ctrl+P > Armature Deform > With Automatic Weights. For finer control,
   Weight Paint mode lets you manually adjust bone influence per vertex.
5. **Test in Pose Mode.**

## Limitations relevant to this project
- Sample metarigs (human, generic quadruped/bird templates if present in a given Blender
  version) are a starting point, not a guarantee — a highly stylized non-human body plan
  (Zayn's camel proportions, Milo's bird-with-arms hybrid) will need custom bone placement,
  not just the human template with renamed bones.
- Automatic weights work far better on a clean quad mesh (post-AutoRemesher) than on a raw
  voxel-remesh/triangulated mesh — retopologize before Rigify-binding for best results.
- Rigify does NOT include a dedicated facial rig system out of the box the way BlenRig does —
  see `blenrig.md` for the facial-rig alternative under consideration for this project.
