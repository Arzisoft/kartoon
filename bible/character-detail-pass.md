---
type: bible
status: reference
updated: 2026-08-17
---

# Character Detail Pass — Primary / Secondary / Tertiary

The standard sculpting workflow, applied to Zayn and Milo's base meshes
(`build/base_body.py`). Three layers of increasing detail, each one locked before
moving to the next — don't add secondary detail while primary shapes are still moving.

## Honest scope note

Blender MCP (ahujasid/blender-mcp — lets an AI agent drive a live Blender session) is good
at primitives, modifiers, materials, and scene setup. It is **not** good at freehand organic
sculpting or creative topology decisions — asking it to "sculpt a realistic muscle" just
produces a placeholder. Primary and secondary forms below are scriptable (geometry, proportions,
modifiers) and MCP/bpy-appropriate. Tertiary detail is procedural (noise textures, normal maps,
bevels) not hand-sculpted wrinkles — and for this show's baby-schema toddler style, most
tertiary "realism" (skin pores, fine wrinkles) is actively the WRONG direction. Tertiary here
means: does the silhouette read instantly, do the species markers survive at a distance, do
materials/seams look intentional up close — not photorealistic anatomy.

## Layer 1 — Primary forms (silhouette, big shapes)

Goal: correct proportions and instantly-readable silhouette from a distance, no detail yet.

- Confirm height ratio holds (Milo ≈ 0.62x Zayn — the big/calm vs small/quick read has to
  work in a flat silhouette before anything else matters).
- Confirm the "one dominant recognition color" zone exists as a real, separate volume (Zayn's
  turquoise blanket, Milo's cheek patches) — not just a flat decal baked on later.
- Confirm species markers exist as actual geometry that survives the voxel remesh at a
  glance: Zayn's hump + long neck curve, Milo's hooked beak protruding clearly past the head
  surface (see issue #2 — this is exactly a primary-forms bug, not a tertiary one).
- Test: render a plain grey-clay silhouette from 3 angles (front, 3/4, side) at thumbnail
  size. If you can't tell "camel" and "bird" apart from a friend's silhouette at that size,
  stop and fix primary forms before touching anything else.

## Layer 2 — Secondary forms (medium shapes, anatomy, joints)

Goal: the body reads as physically coherent — where does it bend, where is the weight.

- Joint regions (shoulder, elbow, hip, knee) get a subtle volume change, not a uniform-radius
  capsule all the way through — real joints are usually slightly narrower than the muscle
  bellies on either side of them.
- Add subsurf + a light bevel/support-loop pass at the seams between primitives (where a ball
  meets a capsule) so the joins don't read as two separate primitives glued together.
- Weight distribution: Zayn's calm/steady personality reads through a slightly heavier,
  grounded lower body; Milo's bubbly/quick personality reads through a lighter, more
  top-heavy silhouette (bigger head-to-body ratio, thinner limbs). This is a scriptable
  proportion tweak, not a sculpt.
- Test: pose-test (as already done in `rig.py`) — do the secondary shapes still read
  correctly when bent, or does the joint pinch/balloon in a way that breaks the silhouette?

## Layer 3 — Tertiary (surface finish, materials, small readable details)

Goal: things that reward a close-up look, without adding anatomical realism this show
doesn't want.

- Materials: matte/soft roughness (not glossy — glossy reads "toy," matte reads "plush/soft,"
  matches the toddler-show genre).
- Cloth-like detail on Zayn's blanket: a light noise-driven bump/displacement to suggest woven
  fabric, not literal thread geometry.
- Feather suggestion on Milo: a few sculpted/scripted ridges along the wing edges (2-3 large
  "feather" divisions, not per-feather detail) — enough to read as "wing" in a close-up
  without the cost of real feather geometry.
- Eye highlights (a small bright specular catch-light) — cheap, disproportionately effective
  for "cute/alive" read at any distance.
- Explicitly out of scope: skin pores, fine wrinkles, individual hairs/feathers, realistic
  fur shaders. If a suggestion pushes toward photorealism, it's the wrong direction for this
  show — flag it rather than build it.

## Rigging tool update: BlenRig over plain Rigify

Research turned up [BlenRig](https://github.com/jpbouza/BlenRig) (jpbouza/BlenRig, 160★) — a
free, open-source auto-rig/skin system used by Blender Studio itself (official training exists
at studio.blender.org), feature-film quality, with an advanced built-in facial rig. It's
**biped-only**, which now matches Ali's redesign exactly, and its facial system is a direct fit
for Rhubarb lip-sync + expressions in a way plain Rigify doesn't cover out of the box. Worth
switching to for the next rigging pass instead of bare Rigify.

## Suggested working order for Ali

1. Fix Milo's primary-forms bug (issue #2) first — tertiary work on a character whose
   species markers don't read is wasted effort.
2. Secondary pass on both characters together (joints/weight), so the two-shot comparison
   stays valid throughout.
3. Tertiary/materials pass last, once primary+secondary are locked on both characters.
