# Blender Modifiers & bpy Patterns — Character Building Cheat Sheet

Source: Blender 5.2 LTS Manual (docs.blender.org/manual), plus this project's own
`build/base_body.py` and `build/color_layer.py`.

## Modifiers used in this pipeline

### Subdivision Surface (Subsurf)
Splits faces into smaller faces for a smoother, rounder appearance. Essential for the
toddler-show "soft round" look — without it, low-poly primitives render visibly faceted.
- `levels` — viewport subdivision count. `render_levels` — render-time count (can differ).
- Applied via `smooth_round()` in `base_body.py` alongside `shade_smooth()`.
- **Gotcha:** applying Subsurf to a THIN shape (a narrow cylinder, a small cube) without edge
  creases shrinks it significantly — Catmull-Clark subdivision rounds off and pulls in thin
  geometry more than bulky shapes. This broke early neck/leg attempts (v2 blockout).

### Shrinkwrap
Moves every vertex of the modified object to the nearest point on a target mesh's surface.
- `target` — the mesh to conform to.
- `wrap_method` — `'NEAREST_SURFACEPOINT'` (what we use), `'PROJECT'`, `'NEAREST_VERTEX'`,
  `'TARGET_PROJECT'`.
- `offset` — distance to keep from the target surface (small positive value avoids z-fighting).
- **This project's key technique:** instead of guessing raw XYZ coordinates for accent
  geometry (a blanket, cheek patches) against a mesh whose exact dimensions aren't known
  ahead of time, place a small rough plane near the target area and let Shrinkwrap conform it
  automatically. See `shrinkwrap_accent()` in `color_layer.py`.

### Solidify
Adds thickness to a flat (zero-thickness) mesh, e.g. a shrinkwrapped plane.
- `thickness` — how much to add, in Blender units.
- Used after Shrinkwrap to give the blanket/cheek-patch planes actual volume.

### Bevel
Rounds sharp edges/corners. Useful on hard-surface accent geometry (cubes) to avoid a boxy
look; less needed once Subsurf is already applied.
- `width`, `segments` (more segments = smoother rounding, more geometry).

### Boolean / Remesh (voxel)
Combines multiple primitive objects into one watertight mesh, then re-triangulates at a fixed
voxel resolution. This project's `fuse()` function in `base_body.py` uses this to join dozens
of scaffold primitives (balls, capsules) into one continuous character mesh.
- **Voxel size is absolute, not relative** — a smaller character needs a proportionally
  smaller voxel size to preserve the same level of surface detail (Milo's beak is ~1/3 Zayn's
  muzzle size and needs a correspondingly finer voxel setting or it dissolves into the head).
- Output is triangulated, not clean quads — this is why AutoRemesher retopology is a
  separate pipeline stage (see `autoremesher.md`).

## Core bpy patterns from this project

- **Building a scaffold from primitives, then fusing:** create many `add_sphere`/
  `add_cylinder`/`add_cube` helper-wrapped primitives parented to an Empty, then boolean-union
  + voxel-remesh them into one mesh (`_scaffold()` / `fuse()` pattern in `base_body.py`).
- **Rigid bone-parenting** (for pre-retopology, multi-object characters): capture the
  object's current `matrix_world`, set `parent_type = 'BONE'` + `parent_bone`, set
  `matrix_parent_inverse = Matrix.Identity(4)`, then re-assign `matrix_world` to the captured
  value — this preserves the visual position while binding rigidly to a single bone, avoiding
  the "many small overlapping parts confuse heat-map skinning" failure mode.
- **Headless render pattern:** `blender --background --python script.py`, with
  `bpy.ops.wm.read_factory_settings(use_empty=True)` at the start of any build function to
  guarantee a clean scene regardless of what ran before.
- **Engine fallback:** `BLENDER_EEVEE_NEXT` isn't available in every Blender build/context —
  wrap the engine assignment in `try/except` falling back to `'BLENDER_EEVEE'`.
