# Procedural Iris/Pupil Eye Texture

Source: "How to Make Procedural Stylized cartoon eye texture in Blender" (YouTube,
https://www.youtube.com/watch?v=PlOABGprmQY). Notes distilled from auto-generated captions
(fetched via `yt-dlp --write-auto-sub`, no video downloaded), corrected for obvious ASR typos.

## Why this mattered

Zayn's eyes (`base_body.py`, `_preview_eyes`/`_eye_material`) were a flat white sclera sphere
plus a flat solid-dark pupil sphere -- no iris colour at all, just a black dot. This is the
single biggest missing piece for eye quality, bigger than the earlier pupil-size increase.

## Technique used (implemented in `_iris_pupil_material()` in `base_body.py`)

The video's full technique builds a separate transparent "cornea" bulge mesh via manual
grid-fill + snap-to-sphere steps -- that part needs the Blender GUI and was skipped (doesn't
fit our headless pipeline; the existing simple pupil sphere already reads fine without a
refractive cornea bulge). The material technique, however, is 100% node-graph / scriptable:

1. `Texture Coordinate` (Object space -- no UV unwrap needed) feeds a spherical `Gradient
   Texture`, which produces concentric rings expanding outward from the object's own origin.
2. A `ColorRamp` maps those rings to colour: black near the centre (pupil), a sharp transition
   to the iris colour partway out, and a darker "limbal ring" right at the outer edge (real
   irises have a visibly darker rim, and it's what makes a stylised iris read as an eye instead
   of a flat coloured sticker).
3. The video also mixes in a small amount of `Voronoi`/`Noise` texture (Overlay blend, low
   factor) so the iris band isn't a flat colour -- fine streak variation, still readable at
   character scale.
4. The video additionally exposes an iris-size `Value` node feeding the `Mapping` node's scale,
   so pupil dilation is a single animatable number -- directly the mechanism
   [chibi-proportion-theory.md](chibi-proportion-theory.md)'s cuteness rule #4 (pupil size
   matters more than iris size) needs to actually act on. Not yet exposed as a parameter in our
   version (kept simple, fixed ColorRamp stops) -- worth adding if we want dilation as a
   posable/animatable expression control later, not just an authored static size.

## Result

Applied 2026-08-17: Zayn's pupil material now shows a warm amber-brown iris ring with a darker
limbal edge and subtle noise streaking, instead of a flat black dot -- purely a material swap,
no geometry change, so it's zero-risk to the already-tuned eye size/position.
