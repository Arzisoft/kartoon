# Rhubarb Lip Sync — Audio-Driven Mouth Shapes

Free, open source. Repo: https://github.com/DanielSWolf/rhubarb-lip-sync. Command-line tool,
Windows/macOS/Linux. Analyzes a voice recording and outputs mouth-shape timing to drive
lip-sync animation.

**Not yet installed/used in this project** — evaluated via research.

## Installation
Download the release for your OS, unpack anywhere — no installer needed (matches
AutoRemesher's "portable executable" pattern already used in this project).

## Basic usage
```
rhubarb -o output.txt my-recording.wav
```

Key flags:
- `-r pocketSphinx` (English, default) or `-r phonetic` (other languages — relevant given
  the bilingual English/Arabic show)
- `-d dialog.txt` — supply the script text for improved accuracy (worth doing, we'll always
  have the script)
- `--extendedShapes` — opt into optional mouth shapes G, H, X
- `-f tsv|xml|json` — output format. JSON is most convenient for scripted Blender import.

## Input/output
- **Input:** WAVE (.wav) or Ogg Vorbis (.ogg) audio.
- **Output:** timestamped mouth-shape codes A through X (TSV/XML/JSON).

## Blender integration
Rhubarb's own docs list integrations for After Effects, Moho, OpenToonz, Spine, Vegas Pro,
Visionaire Studio — **no official Blender integration documented**. This project's earlier
research (`bible/production-notes.md`) referenced a community Blender addon
(`blender-rhubarb-lipsync`, e.g. github.com/scaredyfish/blender-rhubarb-lipsync) that maps
Rhubarb's output codes onto Blender mouth-shape keyframes/shape keys — that addon (not
Rhubarb itself) is what actually wires this into Blender, and hasn't been installed/tested
yet either.

## Open question for this project
Which mouth-shape system it drives (shape keys vs. bone-based mouth control) depends on
whichever facial rig we end up with (BlenRig's shapekey system is the leading candidate —
see `blenrig.md`) — the Rhubarb output codes need to map onto that system's actual shape
key names, not yet defined.
