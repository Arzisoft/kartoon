# Chibi / Cute Character Proportion Theory

Source: "How to Make a Cute 3D Character in Blender" (YouTube,
https://www.youtube.com/watch?v=UVH7dMh3o3M). Notes below are distilled from that video's
auto-generated captions (fetched via `yt-dlp --write-auto-sub`, no video content downloaded),
not a verbatim transcript — obvious ASR errors ("hit to body ratio" -> "head to body ratio",
"mcro lenses" -> "macro lenses") corrected in the summary below.

## Core rules

1. **Shape language**: circles read as friendly/approachable/cute; squares and triangles don't.
   Aim for a soft, rounded silhouette throughout, not just at the head.
2. **Head-to-body ratio is the single biggest cuteness lever** — bigger than any other factor:
   - Adult human: ~1:6 (head:body height)
   - Toddler: ~1:2 to 1:2.5 — this is "chibi" territory
   - Pushed further for max toy/exaggerated cute: 1:1 to 1:1.5
   - Rule: when shrinking the body-to-head ratio, KEEP LIMB/BODY THICKNESS THE SAME — don't
     shrink limb radius along with length. Chunkiness sells it, not just shortness.
3. **Reduce anatomical detail as the character gets rounder/smaller**: omit elbow/knee
   definition, muscle/bone definition, facial creases. If it starts reading as uncanny, soften
   further. Useful mental model: the head silhouette (front, 3/4, and side) should read like a
   bean shape.
4. **Eyes — pupil size matters more than iris size** for the cute read. A large, dilated-
   looking pupil (not just a big iris) is what reads as cute (this is why cats look cute — huge
   pupils). Baseline spacing: about one eye-width apart, though this rule gets broken often.
5. **Oversized clothing/props** relative to the body (~1:2 to 1:2.5 prop-to-body scale)
   amplifies the toy-like read.
6. **"When in doubt, chunky"** — applies to props too. A fat spoon/mug reads cuter than a thin
   one.
7. **Camera trick for a miniature/toy feel**: place the camera BELOW eye level looking up
   (small objects read as small when shot from below, similar to real miniature/tilt-shift
   photography), and use a longer focal length or an orthographic camera to compress depth —
   the opposite of a wide-angle lens, which exaggerates size and makes things look big/close.
   Reference given: Tanaka Tatsuya's miniature photography.

## Relevance to Zayn

The proportion pass applied 2026-08-17 (`base_body.py`: legs shortened ~20%, limb capsules
thickened ~10%, eyes enlarged ~25%) is a direct, moderate application of rule #2 — moderate
because Zayn's documented species-read priorities (long neck, long snout, one clear hump) cap
how far the ratio can push without losing the camel silhouette entirely. Full chibi (1:1.5
head:body) would likely break the camel read; the pass aimed for a middle ground instead.

Not yet applied, worth trying next:
- **Rule #4** (pupil size, not just sclera size) — Zayn's pupils could grow relative to the
  sclera for extra cuteness without changing overall eye size.
- **Rule #5** (oversized clothing) — the current shirt/shorts are close-fitted, not
  exaggerated; a looser/bigger cut (in the same spirit as the turtleneck fix) may read cuter.
- **Rule #7** (camera below eye level) — the turnaround renders use a level camera by design
  (needed for consistent multi-angle review); a hero/thumbnail shot could use this trick.

## Bonus: cheap fabric texture (Magic Texture node)

From the same video — a UV-unwrap-free "fabric weave" look:

```
Magic Texture (Depth 5-8, Texture Coordinate = Object, with scale applied)
  -> Bump node (Strength ~0.5, lower Distortion to kill creepy cavities)
  -> Normal input
```

Add a ColorRamp to sharpen the pattern into distinct highlight/shadow bands. For extra
variation, mix in a second ColorRamp + Noise Texture pass (Multiply blend) to break up
uniformity. Not yet used on Zayn (current cloth materials are flat-color Principled BSDF) —
relevant if/when we want visible fabric weave on the shirt/shorts instead of flat color.
