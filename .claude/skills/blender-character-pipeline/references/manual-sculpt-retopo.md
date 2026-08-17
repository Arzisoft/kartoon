# Manual Sculpt + Retopology Workflow (alternative to AutoRemesher)

Source: "Tutorial: Cartoon head in Blender (A to Z)" (YouTube,
https://www.youtube.com/watch?v=IgJ-tJvry-c), a ~6-hour full workflow video. Notes below are
distilled from that video's auto-generated captions (fetched via `yt-dlp --write-auto-sub`, no
video content downloaded), corrected for obvious ASR typos, not a verbatim transcript.

## Why this matters for us

Our current pipeline (`base_body.py` primitives -> boolean fuse -> voxel remesh ->
AutoRemesher) is fast and fully scriptable, but [autoremesher.md](autoremesher.md) already
flags its known limitation: "auto-topology optimizes for overall quad quality, not specifically
for where a rigger needs edge loops... hero characters... typically still benefit from a human
pass." This video is a full demonstration of that human pass — worth returning to once Zayn's
proportions/design are locked and we're ready for real facial rigging (lip-sync + expressions).

## Workflow outline

1. Start from a simple base mesh (a subdivided cube/sphere blockout), not a sculpt from scratch.
2. Crank Multires/Subdivision to ~3 levels, sculpt in Sculpt Mode with symmetry enabled (Blender
   mirrors one side automatically while sculpting the other).
3. Primary shaping tool: the **Crease brush**, used to define hard boundaries — eyelids,
   nostril edges, ear folds, jaw line, mouth corners. This is the most-used brush in the video
   by a wide margin.
4. Iterate sculpt <-> remesh: periodically apply the Remesh modifier to refresh mesh
   resolution mid-sculpt as detail increases, rather than sculpting at max resolution the whole
   time.
5. Keep the Mirror modifier on for the whole sculpt; toggle its viewport visibility off
   temporarily only when working right at the center seam (nose bridge, philtrum) to see the
   unmirrored surface clearly.
6. **Retopology is manual, not an auto-remesher.** The video explicitly rejects paid
   auto-retopo add-ons (name-checks "Quad Remesher," ~EUR100, deliberately skipped) and instead
   retopologizes by hand using:
   - The **F2 add-on** (bundled with Blender, enable in Preferences > Add-ons, search "F2") —
     fills a face from a single selected edge/vertex loop. By far the most-repeated tool in the
     video; this is what makes manual quad-by-quad retopology fast enough to be practical.
   - **Grid Fill** to close off loops (e.g. around a nostril) with clean quad topology.
   - A paid **"Mask Preserve Brush"** add-on (~$7) for reshaping retopologized geometry while
     preserving the underlying sculpted volume underneath.
7. Eyes are sculpted as their own rough separate forms early — not carved as a socket first.
   Makes it much easier to iterate the eye shape/size independently before finalizing the
   socket geometry around it.

## Takeaway for our pipeline

- AutoRemesher is still the right choice for now — we're iterating on Zayn's proportions
  frequently (see the 2026-08-17 leg-shortening pass), and this manual workflow is GUI-
  interactive, not headless-scriptable, so it doesn't fit our automated pipeline yet.
- Once proportions are locked, a single manual retopology pass on just the FACE (F2 + Grid
  Fill, done by hand in the Blender GUI) would give meaningfully better edge loops around the
  eyes/mouth for the lip-sync work already planned via Rhubarb (see
  [rhubarb-lipsync.md](rhubarb-lipsync.md)) and for future expression shape keys.
- The Crease-brush + Mirror-modifier-toggle sculpting pattern is worth adopting if we ever move
  from primitive-based scripted construction (current approach) to direct sculpting for facial
  detail finer than spheres/capsules can achieve (e.g. eyelid folds, nostril shape).
