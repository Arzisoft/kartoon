# AutoRemesher — Auto-Retopology

MIT-licensed, open source. Repo: https://github.com/huxingyi/autoremesher (160+ stars,
released as MIT-licensed v1.0 in July 2026). Converts a dense/messy mesh (like our voxel-
remesh output) into clean, animation-ready quad topology.

Downloaded to `_review/autoremesher/` (not yet promoted anywhere requiring trust elevation —
it's a standalone executable, run directly, no Blender addon installed).

## Installation
Windows: download the release zip, extract, run `autoremesher.exe`. No installer. Executable
is at `_review/autoremesher/extracted/win32/autoremesher.exe` in this project.

## CLI usage (confirmed via `--help`, this project uses this exclusively — no GUI needed)

```
autoremesher.exe -i input.obj -o output.obj --target-quads 6000 --adaptivity 0.6 --report report.txt
```

Options:
- `-i, --input <file.obj>` — input mesh (OBJ only)
- `-o, --output <output.obj>` — output path
- `--report <report.txt>` — optional stats file (quads, non-quads, vertices, time)
- `--target-quads <count>` — default 50000; for a stylized low/mid-poly character, 3000-8000
  is plenty (used 6000 for Zayn, 4000 for Milo — proportional to character size)
- `--edge-scaling <1.0-4.0>` — default 1.0
- `--sharp-edge <degrees>` — dihedral angle threshold to preserve hard edges, default 90°
- `--smooth-normal <degrees>` — default 0.0
- `--adaptivity <0.0-1.0>` — curvature-adaptive quad density (higher = more quads in
  high-curvature areas like the face); used 0.6

## This project's workflow

1. Export the character's base mesh to OBJ (`build/export_obj.py` — reads `base_body.py`,
   exports `Zayn_Base`/`Milo_Base` as triangulated OBJ into `build/retopo/`).
2. Run `autoremesher.exe` on each OBJ (see command above).
3. Re-import the retopologized OBJ into Blender (`build/verify_retopo.py`) and re-render to
   confirm the silhouette/surface didn't change — only the topology did.

Result on this project's characters: Zayn 19,650 → 3,446 verts, Milo 19,444 → 2,200 verts,
both >98% clean quads, in ~1 second each.

## Known limitation
Auto-retopology gets a character most of the way to animation-ready, but hero characters
(ones the camera holds on, that need clean facial deformation) typically still benefit from a
human pass on face/joint edge loops — auto-topology optimizes for overall quad quality, not
specifically for where a rigger needs edge loops to sit for expression deformation.
