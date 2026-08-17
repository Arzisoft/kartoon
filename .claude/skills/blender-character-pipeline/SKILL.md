---
name: blender-character-pipeline
description: Build, retopologize, rig, animate, and lip-sync stylized 3D characters for the kartoon show using Blender (bpy scripting) + Rigify/BlenRig + AutoRemesher + Hunyuan Motion + Rhubarb Lip Sync. Use when modeling, rigging, animating, or fixing Zayn/Milo or any future character in this pipeline.
---

# Blender Character Pipeline

Practical, tool-by-tool reference for this project's character pipeline, distilled from
official docs/manuals plus what we've actually learned building Zayn and Milo. Read the
relevant reference file for the tool you're touching — don't load all of them for a small task.

## Pipeline stages (in order)

1. **Base body** (`build/base_body.py`) — bpy scripting: primitives → boolean fuse → voxel
   remesh. See [references/bpy-modifiers.md](references/bpy-modifiers.md).
2. **Retopology** (`build/retopo/`) — AutoRemesher cleans the voxel-remesh output into
   animation-ready quads. See [references/autoremesher.md](references/autoremesher.md).
3. **Materials/colour** (`build/color_layer.py`) — matte + subsurface-scattering shaders,
   shrinkwrap-conformed accent geometry (blankets, cheek patches). See
   [references/bpy-modifiers.md](references/bpy-modifiers.md).
4. **Rig** (`build/rig.py`) — currently a hand-built armature with rigid bone-parenting.
   Planned upgrade to Rigify or BlenRig for proper skinning + facial rig. See
   [references/rigify.md](references/rigify.md) and [references/blenrig.md](references/blenrig.md).
5. **Animation** — Hunyuan Motion generates humanoid motion clips from text prompts,
   exported as FBX. See [references/hunyuan-motion.md](references/hunyuan-motion.md).
6. **Lip sync** — Rhubarb Lip Sync generates mouth-shape timing from a voice track. See
   [references/rhubarb-lipsync.md](references/rhubarb-lipsync.md).

## Design theory & technique, learned from tutorials (2026-08-17)

Distilled from free YouTube tutorials via `yt-dlp`-fetched auto-captions (transcripts only, no
video downloaded) — not verbatim, corrected for obvious ASR errors. Read the relevant one
before the next proportion or topology pass:

- [references/chibi-proportion-theory.md](references/chibi-proportion-theory.md) — the design
  theory behind toy/chibi character proportions (head:body ratio, pupil-vs-iris cuteness,
  oversized props, miniature-photography camera tricks) that directly informed Zayn's
  2026-08-17 leg-shortening/eye-enlarging pass.
- [references/manual-sculpt-retopo.md](references/manual-sculpt-retopo.md) — a professional
  manual sculpt + hand-retopology workflow (Crease brush, F2 add-on, Grid Fill) as the
  higher-control alternative to our current AutoRemesher pass. NOTE: this requires the Blender
  GUI (not headless-scriptable) — per project preference, avoid unless there's no scriptable
  alternative; see the two entries below for the scriptable path instead.
- [references/procedural-hand-geometry-nodes.md](references/procedural-hand-geometry-nodes.md)
  — a fully `bpy`-scriptable Geometry Nodes technique for a clean-topology, per-joint-poseable
  hand (no manual sculpting, no armature bones needed for the fingers). Not yet built — a real
  engineering lift — but the correct alternative to `extremity_cap()` sphere-stack fingers when
  we need posed/bent fingers for gesture animation.
- [references/anthropomorphic-design-theory.md](references/anthropomorphic-design-theory.md) —
  human/animal-blending design principles for bipedal animal characters (no manual technique,
  pure design judgment). Confirms several of Zayn's existing design calls (visible eye whites,
  mobile brow, added mouth, enlarged eyes) were the right ones per general anthro-design theory.
- [references/procedural-iris-eye-texture.md](references/procedural-iris-eye-texture.md) — a
  fully scriptable Gradient-Texture/ColorRamp technique for a real coloured iris ring + limbal
  edge instead of a flat black pupil dot. Implemented 2026-08-17 as `_iris_pupil_material()` in
  `base_body.py` — pure material swap, no geometry change.
- [references/muzzle-drawing-technique.md](references/muzzle-drawing-technique.md) — a
  medium-independent orb+cylinder shape breakdown for muzzles; mostly confirms our existing
  construction, but flagged that our turnaround QA never checked the 3/4 angle specifically
  (the angle most likely to expose muzzle volume problems) — a `"quarter"` (45°) view was added
  to the `cycles_sss_test.py` render loop as a result.

## Project-specific lessons (learned the hard way this session — read before repeating)

- **Don't guess raw coordinates against a mesh you can't see live.** Placing accent geometry
  (Zayn's blanket, Milo's cheek patches) by hand-tuned XYZ took ~8 failed headless-render
  iterations before it worked. The fix: use a Shrinkwrap modifier so the geometry conforms to
  the real surface automatically — see `shrinkwrap_accent()` in `color_layer.py`.
- **Face-selecting a region on a fused/remeshed mesh gives jagged edges.** Milo's first cheek
  patches (selected by proximity on the voxel-remeshed mesh) read as fangs, not markings, in
  a close-up render. Use small separate shrinkwrapped geometry instead of face-selecting on
  the fused body.
- **Rigid bone-parenting (not heat-map auto-weight) for primitive-blockout characters.**
  Heat-map skinning collapsed Milo's mesh the first time — too many small overlapping parts
  confuse the automatic weight solver. Parenting each part rigidly to its single best-fit bone
  is simpler and reliable for a body built from many separate primitives (before retopology).
  Once a character is fully retopologized into one continuous quad mesh (post-AutoRemesher),
  proper heat-map/envelope skinning becomes viable again.
- **Test at the actual viewing distance, not just a studio medium shot.** A thumbnail-
  silhouette test and a close-up face render caught problems (Milo not reading as a bird at
  all, cheek-patch fang artifact) that a normal-distance render never showed.
- **AI video generation (Seedance/Kling/Veo) was rejected for character consistency** — every
  generation is new pixels, no persistent asset. Real rigged 3D (this pipeline) guarantees
  consistency because the same geometry is reused every episode.
