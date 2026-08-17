# Archive

Superseded character versions, kept so the current `build/` folder only ever contains the
live pipeline. Nothing in here is imported by the working scripts.

Each folder holds the scripts and/or the renders exactly as they were when that version was
replaced, so a direction can be revisited without digging through git history.

## v2-quadruped

The original pass. Both characters built as **four-legged animals** from many separate
primitive objects, each rigidly parented to a single bone.

Replaced because:

- **No hands.** Most of the show's target episode topics — first day of school, trying new
  food, a doctor visit, sharing a toy — need holding, pointing, hugging and wearing things.
  A quadruped camel can do none of it.
- **The stack assumes a biped.** Hunyuan Motion and every other humanoid motion source emits
  a humanoid skeleton; there is nothing to retarget onto a four-legged rig.
- **Nothing could deform.** Loose primitives rigidly bone-parented can follow a skeleton but
  never bend — no elbow, no squash, no facial movement.

Contains `characters.py`, `rig_test.py` and their renders.

## v3-upright-blob

First upright/bipedal rebuild. The layered pipeline (one continuous mesh, then a shared biped
skeleton) was established here and is still what the live scripts use — that part carried
forward. The **proportions** did not.

Replaced because both characters read as insects rather than as a camel and a budgie:

- Giant round ball heads with no necks
- Solid dark bead eyes, small and set low
- Squat blob torsos on stubby stumps
- Species cues (Zayn's hump, Milo's beak) melted into the body mass by the voxel remesh

Renders only — the scripts evolved in place rather than being replaced, so this version lives
in git history on branch `ali/milo-base-body`.
