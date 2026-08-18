# Procedural Hand via Geometry Nodes (future upgrade candidate)

Source: "How to Create a Procedural Hand with Geometry Nodes" (YouTube,
https://www.youtube.com/watch?v=yeCc2wYskXM). Notes distilled from auto-generated captions
(fetched via `yt-dlp --write-auto-sub`, no video downloaded), corrected for obvious ASR typos.

## Why this is the right kind of tutorial for us

Unlike most "how to model a hand" tutorials (manual sculpting/box-modeling, doesn't transfer to
a headless bpy pipeline), Geometry Nodes IS a node graph — the same kind of thing we already
build programmatically for materials (see `color_layer.advanced_material()`). A Geometry Nodes
setup can be constructed entirely via `bpy` (`node_group.nodes.new(...)`, `.links.new(...)`,
same API shape as shader nodes) and its control values exposed as modifier inputs that a script
can set directly — no clicking required. This is a genuine alternative to our current
sphere-stacking `extremity_cap()` fingers, with two real advantages: clean quad topology (starts
from a subdivided cube, not voxel-remeshed spheres) and built-in bend/pose control per finger
joint via a single scalar input each, without needing armature bones for the fingers at all.

## Technique outline

1. Start from a `Cube` mesh node, set Y dimension/vertices to 6 (gives enough loops along the
   finger's length to bend smoothly), feed through a Subdivision Surface node (level 2).
2. Capture per-vertex local position (`Position` node -> `Separate XYZ`), since the finger
   extends along Y. A `Less Than` math node on the Y component isolates "everything past this
   point along the finger" as a selection mask -- this is joint 1 (the middle knuckle).
3. Store that mask as a named attribute (`Store Named Attribute`) so it survives into later
   nodes, then feed it into `Set Position`: multiply the mask by a control value -> `Combine
   XYZ` (X only, since the joint bends around the X axis) -> `Rotate Vector`, wired to
   `Set Position`'s offset. The multiply node's second input becomes the "how bent is this
   knuckle" control, exposed via `Group Input` so it's settable per-instance from the modifier
   panel (i.e. from a script).
4. Joint 0 (the knuckle closest to the palm) is trickier: bending it also needs to correct a
   position drift the pure rotation introduces (the mesh creeps up +Z and forward along Y as it
   rotates). Fixed with a `Sign` node for the curl direction, then a `Subtract` fed by a
   `Divide` of the same control value to pull the mesh back down on Z proportionally as the
   joint bends, plus a `Divide`+`Absolute` pair to tame how far the rotation drifts along Y.
   The video's own admission: this part was tuned by trial and error, not derived analytically
   -- expect to do the same if we build this ourselves.
5. Group the whole finger into one node group, duplicate it 4x (index/middle/ring/pinky) plus
   once more for the thumb (thumb reuses the same joint-0/joint-1 logic, just repositioned via
   a `Transform Geometry` node and typically a shorter length), each with its own exposed
   bend-control inputs. A static palm mesh (not built procedurally -- palms don't need it) plus
   `Join Geometry` combines everything into one hand.
6. `Set Shade Smooth` + a Subdivision modifier for the final rounded look; skip both if a
   sharper/faceted style is wanted instead.

## Status: not yet built

This is a real engineering lift (a dozen-plus interlinked nodes with hand-tuned drift
correction, per the video's own trial-and-error admission) -- worth doing as a dedicated pass,
not a quick fix bolted onto the current pipeline. When we do:
- Build it once as a reusable node group in a new `build/procedural_hand.py` (mirroring how
  `color_layer.advanced_material()` is a reusable Python function around a node graph).
- Expose per-finger bend as a `bpy` modifier-input value from Python -- this doubles as free
  hand-POSING for the hands-on-hips shot without touching the arm armature's own bone weights
  at all.
- Compare directly against the current `extremity_cap()` sphere-stack fingers before switching
  over -- the sphere approach is simple and already looks acceptable at Zayn's current
  chibi/simplified proportions; this is worth it mainly if we need posed/bent fingers for
  gesture animation, not purely for static appearance.
