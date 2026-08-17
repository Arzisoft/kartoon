# Muzzle/Snout Construction Technique

Source: "Muzzle/Snout Tutorial - How To Draw A Furry Head" (YouTube,
https://www.youtube.com/watch?v=bc_JsBHFWhU). A 2D drawing tutorial, not Blender-specific, but
the shape-breakdown technique is medium-independent. Notes distilled from auto-generated
captions (fetched via `yt-dlp --write-auto-sub`, no video downloaded), corrected for obvious
ASR typos.

## The technique

Break the head into simple 3D primitives before drawing/modelling detail: **head = a
sphere/orb, muzzle = a cylinder (or a second, smaller orb) attached to the front of the head
sphere, ears = cones/triangles**. This is presented as the fix for the single hardest thing
about drawing anthro/furry heads: getting the muzzle's volume and perspective right, especially
from a 3/4 ("quarter") angle -- straight front and straight side views are comparatively easy;
the 3/4 view is where the muzzle's 3D form actually has to be understood, not faked, and where
beginner mistakes are most visible ("this Voit-meme-like flat/broken look").

## Relevance to Zayn -- mostly confirms, one concrete action item

`base_body.py`'s existing muzzle construction (stacked, tapering spheres running forward from
the head ball -- see the "snout" section of `build_zayn_base()`) already matches this
orb-plus-cylinder breakdown almost exactly. This source doesn't suggest a construction change.

**What it DID surface as a real gap**: our turnaround QA render (`cycles_sss_test.py`) only
ever checked front/right/back/left -- clean 90-degree angles, never a 3/4 view. Per this
source, that's specifically the angle most likely to expose a muzzle that reads fine from the
"easy" angles but is actually flat or malformed. Added a `"quarter"` (45 deg) camera angle to
the turnaround loop 2026-08-17 to close that QA gap.
