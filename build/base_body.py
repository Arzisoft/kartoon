"""
Layer 1 of the character pipeline: BASE BODY only.

This produces ONE continuous, watertight mesh per character — no colours, no outfit,
no face. It is the only geometry that ever gets skinned to the rig; everything above it
(materials, outfits, props, face shape keys) attaches on top in later layers.

Why one joined mesh instead of loose primitives:
the v2 blockout (characters.py) built each character from many separate primitive objects,
which can only be rigidly bone-parented — parts follow a bone but never deform. That is fine
for a still blockout and a dead end for animation. Here the primitives are a *construction
scaffold*: they get joined and voxel-remeshed into a single manifold surface that can take
real vertex weights.

Body plan is upright/bipedal (not the v2 quadruped) so the characters can hold, point, hug
and wear things, and so humanoid motion sources retarget onto them.

Run standalone to render a silhouette turnaround:
    blender --background --python base_body.py
"""
import bpy
import math
import os
from mathutils import Vector

# ---------------------------------------------------------------- proportions
# Heights are the one thing that must differ per character. Zayn reads as the big,
# calm one; Milo (later) is built to roughly 0.6x this so the two-shot silhouette
# contrast survives. Head is deliberately ~1/3 of total height (baby schema).
ZAYN_HEIGHT = 2.20

# Remesh/smoothing settings are a species-read tradeoff, not just a quality dial: too coarse a
# voxel or too much smoothing melts the neck, ears and muzzle into the body mass and the
# character stops reading as a camel at all.
VOXEL_SIZE = 0.022
SMOOTH_FACTOR = 0.35
SMOOTH_ITERATIONS = 2


def _scaffold(name):
    """Container for the throwaway primitives that get fused into the base mesh."""
    return {"name": name, "parts": []}


def _track(scaffold, obj):
    # Bake each primitive's location/rotation/scale straight into its mesh data. Without this,
    # join() adopts the *first* part's transform as the joined origin and silently offsets the
    # whole character (an early version of this sank Zayn 2.2m through the floor). With every
    # part at an identity transform, the joined mesh's local coordinates are exactly the
    # construction coordinates and the origin lands on world (0,0,0).
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    scaffold["parts"].append(obj)
    return obj


def add_ball(scaffold, radius, location, scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=location, segments=24, ring_count=12)
    obj = bpy.context.active_object
    obj.scale = scale
    return _track(scaffold, obj)


def add_capsule(scaffold, p1, p2, radius):
    """A limb segment from p1 to p2, with rounded caps so joints fuse cleanly."""
    p1, p2 = Vector(p1), Vector(p2)
    delta = p2 - p1
    length = delta.length
    rot = delta.to_track_quat('Z', 'Y').to_euler()
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=length, location=(p1 + p2) / 2,
                                        rotation=rot, vertices=16)
    _track(scaffold, bpy.context.active_object)
    add_ball(scaffold, radius, p1)
    add_ball(scaffold, radius, p2)
    return scaffold


def fuse(scaffold):
    """Join every scaffold part, then voxel-remesh into one continuous manifold surface."""
    parts = scaffold["parts"]
    bpy.ops.object.select_all(action='DESELECT')
    for p in parts:
        p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()

    body = bpy.context.active_object
    body.name = scaffold["name"]

    remesh = body.modifiers.new("Remesh", 'REMESH')
    remesh.mode = 'VOXEL'
    remesh.voxel_size = VOXEL_SIZE
    bpy.ops.object.modifier_apply(modifier=remesh.name)

    smooth = body.modifiers.new("Smooth", 'SMOOTH')
    smooth.factor = SMOOTH_FACTOR
    smooth.iterations = SMOOTH_ITERATIONS
    bpy.ops.object.modifier_apply(modifier=smooth.name)

    bpy.ops.object.shade_smooth()
    bpy.context.view_layer.update()
    return body


# ---------------------------------------------------------------------- Zayn
# Single source of truth for Zayn's joint positions, in construction space (facing -Y, feet
# on z=0). Both the base mesh below and the skeleton in rig.py read these, so the bones can
# never drift out of the limbs they are supposed to deform. Sided joints are given for the
# +X side; the -X side mirrors by negating x.
ZAYN_JOINTS = {
    "hip":       (0.16, 0.00, 0.58),
    "knee":      (0.18, 0.00, 0.32),
    "ankle":     (0.19, 0.00, 0.10),
    "toe":       (0.19, -0.17, 0.055),
    "pelvis":    (0.00, 0.00, 0.66),
    "spine":     (0.00, 0.01, 0.93),
    "chest":     (0.00, 0.02, 1.19),
    "neck_base": (0.00, 0.04, 1.30),
    "head_base": (0.00, -0.11, 1.79),
    "head_top":  (0.00, -0.13, 2.12),
    "shoulder":  (0.32, 0.02, 1.26),
    "elbow":     (0.50, -0.02, 0.96),
    "wrist":     (0.60, -0.06, 0.66),
    "hand_end":  (0.65, -0.07, 0.50),
}


def joint(name, side=1):
    """Joint position, mirrored to the -X side when side is -1."""
    x, y, z = ZAYN_JOINTS[name]
    return (x * side, y, z)


def build_zayn_base():
    """Upright camel base body, A-pose, facing -Y. Returns the single joined mesh object.

    Species cues carried deliberately (production-notes: a stylised round character needs
    1-2 unmistakable species markers or it reads as a generic blob):
      * a large hump sitting high on the BACK, clearly separated from the head
      * a long muzzle with a drooping split lip
    The v2 quadruped failed this test — its short hump and long neck read as a llama.
    """
    s = _scaffold("Zayn_Base")

    # --- legs: short and stubby, toddler proportion (feet on z=0)
    for side in (1, -1):
        add_capsule(s, joint("hip", side), joint("knee", side), 0.112)
        add_capsule(s, joint("knee", side), joint("ankle", side), 0.095)
        # foot, pushed forward (-Y) so he doesn't look like he's on stilts
        add_ball(s, 0.125, (0.19 * side, -0.06, 0.075), scale=(0.85, 1.40, 0.55))

    # --- pelvis + belly: round, no waist (baby schema)
    add_ball(s, 0.28, joint("pelvis"), scale=(1.05, 0.92, 0.85))
    add_ball(s, 0.38, joint("spine"), scale=(1.05, 0.95, 0.95))
    # blend ball between belly and chest — without it the two masses leave a visible ridge
    # now that smoothing is dialled down to protect the muzzle and ears
    add_ball(s, 0.355, (0, 0.015, 1.07), scale=(1.08, 0.92, 0.90))

    # --- chest/shoulders, kept narrow front-to-back so the hump behind it stays legible
    add_ball(s, 0.33, joint("chest"), scale=(1.12, 0.88, 0.80))

    # --- HUMP: primary camel cue. Sits high on the back and overlaps the shoulder mass
    # enough to grow out of it — pushed too far back it reads as a ball stuck on, too far
    # forward and it disappears into a hunch.
    add_ball(s, 0.275, (0, 0.175, 1.53), scale=(1.05, 0.90, 0.85))

    # --- neck: long and clearly narrower than head and chest, leaning forward so the head
    # sits ahead of the hump and a notch opens up between the two masses in profile.
    add_capsule(s, joint("neck_base"), joint("head_base"), 0.108)

    # --- head: big (baby schema) but smaller than v3 to make room for a visible neck
    add_ball(s, 0.285, (0, -0.13, 1.96), scale=(1.0, 1.02, 0.95))

    # --- muzzle: long and dropping away from the head — the second camel cue.
    # Length is what separates "camel" from "beak", so it runs well forward of the skull.
    add_ball(s, 0.165, (0, -0.36, 1.87), scale=(0.88, 1.30, 0.82))
    add_ball(s, 0.125, (0, -0.52, 1.81), scale=(0.92, 1.05, 0.80))
    # drooping split lower lip
    add_ball(s, 0.078, (0, -0.56, 1.73), scale=(1.10, 0.85, 0.80))

    # --- ears: small, set wide and high enough to break the head silhouette
    for side in (1, -1):
        add_ball(s, 0.075, (0.235 * side, 0.0, 2.13), scale=(0.55, 0.75, 1.30))

    # --- arms in A-pose (~35 deg out from vertical), ending in mitten hands.
    # Longer than v3 so the hands clear the belly and can actually hold a prop.
    for side in (1, -1):
        add_capsule(s, joint("shoulder", side), joint("elbow", side), 0.100)
        add_capsule(s, joint("elbow", side), joint("wrist", side), 0.086)
        # mitten hand: one mass + a thumb, enough to hold props and read as a hand
        add_ball(s, 0.110, (0.635 * side, -0.07, 0.57), scale=(0.85, 1.05, 1.0))
        add_ball(s, 0.052, (0.545 * side, -0.11, 0.59))

    return fuse(s)


# ------------------------------------------------------------ preview scene
def _preview_eyes(body, parent):
    """Temporary eyes for judging the silhouette read. NOT part of the base mesh —
    the face is a later layer (shape keys for expression + lip sync)."""
    mat = bpy.data.materials.new("PreviewEyeDark")
    mat.use_nodes = True
    mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.02, 0.02, 0.02, 1)
    for side in (1, -1):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.068, location=(0.138 * side, -0.32, 1.93),
                                             segments=16, ring_count=8)
        eye = bpy.context.active_object
        eye.name = f"Zayn_PreviewEye_{'L' if side > 0 else 'R'}"
        eye.data.materials.append(mat)
        bpy.ops.object.shade_smooth()
        eye.parent = parent


def build_preview():
    """Front / three-quarter / side turnaround so the silhouette can be judged."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene

    body = build_zayn_base()

    clay = bpy.data.materials.new("Clay")
    clay.use_nodes = True
    bsdf = clay.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.72, 0.70, 0.68, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.65
    body.data.materials.append(clay)

    # three copies at different rotations, spread along X
    views = [(-1.55, 0), (0.0, 45), (1.55, 90)]
    for i, (x, deg) in enumerate(views):
        if i == 0:
            obj = body
        else:
            obj = body.copy()
            obj.data = body.data  # linked duplicate: same mesh, no extra memory
            scene.collection.objects.link(obj)
        obj.location = (x, 0, 0)
        obj.rotation_euler = (0, 0, math.radians(deg))
        _preview_eyes(body, obj)

    backdrop = bpy.data.materials.new("Backdrop")
    backdrop.use_nodes = True
    backdrop.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.88, 0.90, 0.92, 1)
    bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
    bpy.context.active_object.data.materials.append(backdrop)
    bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 5, 5), rotation=(math.radians(90), 0, 0))
    bpy.context.active_object.data.materials.append(backdrop)

    world = bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.85, 0.88, 0.91, 1.0)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.7

    target = bpy.data.objects.new("Target", None)
    target.location = (0, 0, 1.15)
    scene.collection.objects.link(target)
    bpy.ops.object.camera_add(location=(0, -8.5, 1.6))
    cam = bpy.context.active_object
    cam.data.lens = 50
    track = cam.constraints.new(type='TRACK_TO')
    track.target = target
    track.track_axis = 'TRACK_NEGATIVE_Z'
    track.up_axis = 'UP_Y'
    scene.camera = cam

    for loc, energy, size in [((-4, -5, 5), 900, 4), ((4, -4, 3), 350, 4), ((0, 5, 4), 300, 3)]:
        bpy.ops.object.light_add(type='AREA', location=loc)
        bpy.context.active_object.data.energy = energy
        bpy.context.active_object.data.size = size

    try:
        scene.render.engine = 'BLENDER_EEVEE_NEXT'
    except Exception:
        scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 800
    scene.render.image_settings.file_format = 'PNG'
    return body


if __name__ == "__main__":
    body = build_preview()
    print(f"BASE_MESH_VERTS:{len(body.data.vertices)} POLYS:{len(body.data.polygons)}")
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "zayn_base.png")
    bpy.context.scene.render.filepath = out_path
    bpy.ops.render.render(write_still=True)
    print(f"RENDERED_TO:{out_path}")
