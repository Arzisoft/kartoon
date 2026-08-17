---
type: bible
status: reference
updated: 2026-08-17
---

# Production Notes

Distilled decisions and reasoning behind the pipeline — written from our own research/testing,
not copied from any course material. For the character/world specifics, see `characters.md`
and `world.md`.

## Character design principles

- **Baby schema** (Konrad Lorenz's "Kindchenschema"): big head relative to body, big eyes set
  low, round cheeks, small chin, soft round body. This is what reads as "cute" to toddlers
  regardless of species — design every character to this formula first.
- **One dominant recognition color per character** (the "Elmo red" trick): pick one hue that's
  applied with total consistency everywhere the character appears, so it reads identically on
  a thumbnail, a toy, or mid-episode.
- **Species-specific silhouette cues matter more than realism.** A stylized, round character
  still needs 1-2 unmistakable species markers (Zayn's neck curve + hump, Milo's hooked beak +
  cheek patch) or it reads as a generic blob instead of "camel" / "budgie."

## Why real 3D instead of AI-video-generation

AI video models (Seedance, Kling, Veo, etc.) generate new pixels on every call — there's no
persistent asset, so character consistency across episodes depends entirely on prompt-matching
and drifts over time. A rigged 3D model is a one-time asset: model + rig once, every episode
reuses the exact same geometry, guaranteeing consistency. This is why the pipeline is
Blender-based rather than built on AI video generation, even though the latter is faster to
start with.

## Pipeline stack (all free/open-source)

- **Blender** — core 3D engine, character modeling.
- **Rigify** (Blender built-in) — auto-rigging.
- **Hunyuan Motion** (Tencent, open-source) — text-to-3D-motion, exports FBX straight into
  Blender. Describe a move in plain English, get an animation clip.
- **Rhubarb Lip Sync** + a Blender integration addon — generates mouth-shape keyframes
  automatically from a voice audio track.

Current build scripts (`build/characters.py`, `build/rig_test.py`) build both characters
procedurally from primitives and rig them with **rigid bone-parenting** (each primitive part
parented to its single best-fit bone) rather than heat-map vertex-weight skinning — the
characters are built from many separate small primitive objects, not one continuous mesh, so
heat-map skinning weight-bleeds between nearby unrelated parts and can collapse the mesh.
Rigid per-part parenting is simpler and reliable for this kind of block-built character.

## Competitor research (informs format decisions)

- **Episode length:** Cocomelon's actual atomic unit is 3-5 minutes — the "hour-long" videos
  are stitched compilations of many short episodes, not native long-form content. Build short,
  compile later.
- **Localization:** the dominant strategy (ChuChu TV, etc.) is one dedicated channel per
  language. Nobody at scale does mixed-language-in-one-video the way this show's bilingual
  code-switching hook does — that's a genuine gap, not a proven pattern, which is exactly why
  it's the bet.
- **Cadence:** weekly is the historical baseline; 3+/week generally outperforms for growth. An
  AI-assisted pipeline makes higher frequency realistic from the start.
- **Thumbnails:** bright primary colors, main character(s) always visible, consistent color
  identity per character (ties back to the "one dominant hue" rule above).

## Workspace methodology

This repo is organized loosely on **ICM (Interpretable Context Methodology)** — folder
structure as routing, not just storage: a small entry point, stage/content folders that state
their own purpose, reference material kept apart from working output. See
`https://github.com/RinDig/icm-architect` (MIT-licensed, public) if you want the full method —
say "ICM this" to that skill if you want it to scaffold or audit a folder structure.
