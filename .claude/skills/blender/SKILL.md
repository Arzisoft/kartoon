---
name: blender
description: General-purpose reference for Blender itself — the Python API (bpy), headless/command-line usage, and the core data model (scenes, objects, meshes, materials). Use for any Blender scripting task, not just character-building. For this project's specific character pipeline (base body, retopology, rigging, materials), see the blender-character-pipeline skill instead — that one builds on this one.
---

# Blender

General Blender reference, distilled from the official Blender 5.2 LTS Manual and Python API
docs (docs.blender.org). For this project's character-pipeline-specific techniques (shrinkwrap
accents, voxel-remesh gotchas, rigid bone-parenting), see the sibling
`blender-character-pipeline` skill — that's the specialized one; this is the general one it
builds on.

## The three-part mental model

Every bpy script works with three things:

- **`bpy.data`** — the actual project data: objects, meshes, materials, scenes, etc. Query
  and modify this directly for automation/scripting, since it doesn't depend on what a human
  user currently has selected or which area of the UI is focused.
- **`bpy.context`** — the current state: active object, selected objects, active scene, which
  screen area is under the mouse. UI-driven tools read this; scripts should generally prefer
  `bpy.data` for anything that needs to work regardless of what's "currently selected."
- **`bpy.ops`** — operators: the same actions a human triggers via the UI (add a cube, apply
  a modifier, render). Many operators require specific context to be valid (e.g. an object
  must be selected and active) — this is the most common source of `RuntimeError` in headless
  scripts. When an operator fails mysteriously, check `bpy.context.active_object` and
  `.selected_objects` are what the operator expects first.

## Headless / command-line usage

```
blender --background --python script.py
```

- `--background` (or `-b`) — run without the GUI ("headless mode"). This project always uses
  this for automated builds/renders.
- `--python script.py` (or `-P`) — run a Python script. Can be given multiple times to chain
  scripts in one invocation.
- `--python-expression "<code>"` — inject a single line of Python directly from the CLI,
  without a script file.
- **Argument order matters.** Blender processes arguments left to right; e.g. a render-frame
  argument placed before the output-path argument executes before the path is set. When
  passing your own arguments to a script (not to Blender itself), put them after a bare `--`
  — Blender stops parsing its own arguments there and hands the rest to `sys.argv` for the
  script to read.
- Rendering-specific flags: `-o <path>` (output), `-s`/`-e` (start/end frame), `-a` (render
  full animation), `-f <frame>` (render one frame).

This project's convention: every build script guards its own render/execution behind
`if __name__ == "__main__":` so the same file can be imported by another script (to reuse its
`build_*()` functions) without triggering a render as a side effect. See
`build/base_body.py` for the pattern.

## Core data model (what you're actually manipulating)

- **Scene** → contains a **Collection** hierarchy → contains **Objects**.
- **Object** — a "thing in the scene": has a transform (location/rotation/scale) and a
  `.data` pointer to the actual content (mesh, armature, light, camera, etc.). Multiple
  objects can share the same `.data` (a "linked duplicate") — cheap for repeated geometry.
- **Mesh data** (`object.data` when `object.type == 'MESH'`) — vertices, edges, faces,
  independent of the object's transform. Editing mesh data (e.g. via `bmesh`) is separate
  from moving/rotating the object that references it.
- **Material** — assigned via `object.data.materials`, referenced by index per-face
  (`polygon.material_index`) for multi-material meshes.
- **Modifiers** — live on the object (`object.modifiers`), applied in stack order, non-
  destructive until explicitly applied. See `blender-character-pipeline`'s
  `bpy-modifiers.md` for the specific modifiers this project uses.
- **Armature / Bones** — a special object type for rigging; `edit_bones` (edit mode) define
  rest pose/hierarchy, `pose.bones` (pose mode) hold runtime transforms for animation/posing.

## Common headless-scripting gotchas (from this project's experience)

- Always start a build function with `bpy.ops.wm.read_factory_settings(use_empty=True)` if
  the script might run standalone — guarantees a clean scene regardless of prior state.
- `'BLENDER_EEVEE_NEXT'` isn't registered in every Blender build/context — wrap engine
  assignment in `try/except`, falling back to `'BLENDER_EEVEE'`.
- Many `bpy.ops.object.*` operators need `bpy.context.view_layer.objects.active` set AND the
  object selected (`obj.select_set(True)`) — don't assume the just-created object is
  automatically both.
- Assigning `obj.parent = X` directly (not via the `Ctrl+P` / `parent_set()` operator) does
  NOT preserve the object's current world-space transform — it leaves `matrix_parent_inverse`
  as whatever it already was, so the object can visually jump. Capture `matrix_world` first
  and reassign it after reparenting if you need the visual position preserved.
