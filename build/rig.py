"""
Layer 2 of the character pipeline: RIG.

Builds a biped deform skeleton fitted to the base body and skins it with real vertex
weights (heat-map / automatic weights), then renders a rest-vs-posed comparison to prove
the mesh actually deforms.

Two decisions worth stating, because they are the reason this file exists at all:

1. Real skinning, not rigid bone-parenting. The v2 rig (rig_test.py) parented each loose
   primitive to one bone, because heat-map weights bleed between nearby unrelated primitives
   and collapsed the mesh. That is no longer a constraint: base_body.py produces ONE
   continuous manifold surface, which is exactly what heat-map skinning needs. Rigid
   parenting could never bend an elbow; this can.

2. Same bone names and hierarchy for every character, different bone LENGTHS. Milo is
   built much shorter than Zayn, but as long as the skeletons share a structure, one motion
   clip plays on both and humanoid motion sources retarget onto either. Giving the two
   characters structurally different skeletons would mean authoring every animation twice.

Bone names follow the common humanoid convention (hips/spine/chest/neck/head, upper_arm,
forearm, hand, thigh, shin, foot) so external humanoid motion maps on with minimal fuss.

Run headless:
    blender --background --python rig.py
"""
import bpy
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import base_body  # noqa: E402

# (bone, head joint, tail joint, parent, connected-to-parent)
# Sided bones are expanded per side by build_skeleton().
BIPED_BONES = [
    ("hips",      "pelvis",    "spine",     None,      False),
    ("spine",     "spine",     "chest",     "hips",     True),
    ("chest",     "chest",     "neck_base", "spine",    True),
    ("neck",      "neck_base", "head_base", "chest",    True),
    ("head",      "head_base", "head_top",  "neck",     True),
]
SIDED_BONES = [
    ("upper_arm", "shoulder", "elbow",    "chest", False),
    ("forearm",   "elbow",    "wrist",    "upper_arm", True),
    ("hand",      "wrist",    "hand_end", "forearm",   True),
    ("thigh",     "hip",      "knee",     "hips",  False),
    ("shin",      "knee",     "ankle",    "thigh",     True),
    ("foot",      "ankle",    "toe",      "shin",      True),
]


def build_skeleton(name, joints_module=base_body):
    """Create the armature and its edit bones, fitted to the shared joint table."""
    arm_data = bpy.data.armatures.new(f"{name}_Data")
    arm_obj = bpy.data.objects.new(name, arm_data)
    bpy.context.scene.collection.objects.link(arm_obj)

    bpy.ops.object.select_all(action='DESELECT')
    arm_obj.select_set(True)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='EDIT')

    eb = arm_data.edit_bones
    made = {}

    def add(bone_name, head_j, tail_j, parent, connect, side=1):
        b = eb.new(bone_name)
        b.head = joints_module.joint(head_j, side)
        b.tail = joints_module.joint(tail_j, side)
        if parent:
            b.parent = made[parent]
            b.use_connect = connect
        made[bone_name] = b
        return b

    for bone_name, head_j, tail_j, parent, connect in BIPED_BONES:
        add(bone_name, head_j, tail_j, parent, connect)

    for bone_name, head_j, tail_j, parent, connect in SIDED_BONES:
        for suffix, side in (("L", 1), ("R", -1)):
            parent_name = parent if parent in made else f"{parent}.{suffix}"
            add(f"{bone_name}.{suffix}", head_j, tail_j, parent_name, connect, side)

    bpy.ops.object.mode_set(mode='OBJECT')
    return arm_obj


def skin(body, arm_obj):
    """Bind the mesh to the armature with heat-map automatic weights."""
    bpy.ops.object.select_all(action='DESELECT')
    body.select_set(True)
    arm_obj.select_set(True)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')
    return len(body.vertex_groups)


def pose(arm_obj, poses):
    """Apply euler rotations (degrees) to named pose bones."""
    bpy.ops.object.select_all(action='DESELECT')
    arm_obj.select_set(True)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='POSE')
    for bone_name, degrees in poses.items():
        pb = arm_obj.pose.bones[bone_name]
        pb.rotation_mode = 'XYZ'
        pb.rotation_euler = tuple(math.radians(d) for d in degrees)
    bpy.ops.object.mode_set(mode='OBJECT')


# A wave plus a head turn and a knee bend. Deliberately includes an ELBOW bend, because
# that is the motion rigid bone-parenting could never produce — if the forearm bends
# smoothly here, real skinning is working.
#
# Axis note for the head and neck: a pose bone's local Y runs ALONG the bone, so on the
# upright neck/head chain X nods, Y turns, and Z tilts sideways. Getting this wrong is easy
# and looks like broken weights rather than a bad pose — a nod+tilt on a long-muzzled head
# drives the muzzle straight into the chest.
WAVE_POSE = {
    "upper_arm.L": (0, 0, -115),
    "forearm.L": (0, 0, -45),
    "hand.L": (0, 0, -15),
    "head": (-10, 25, 0),
    "neck": (-5, 10, 0),
    "thigh.R": (18, 0, 0),
    "shin.R": (-25, 0, 0),
    "spine": (0, 0, -5),
}


def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene

    body = base_body.build_zayn_base()
    arm_obj = build_skeleton("Zayn_Rig")
    groups = skin(body, arm_obj)
    print(f"VERTEX_GROUPS:{groups} BONES:{len(arm_obj.data.bones)}")

    clay = bpy.data.materials.new("Clay")
    clay.use_nodes = True
    bsdf = clay.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.72, 0.70, 0.68, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.65
    body.data.materials.append(clay)

    # duplicate the whole rigged character so rest and posed sit side by side in one frame
    bpy.ops.object.select_all(action='DESELECT')
    body.select_set(True)
    arm_obj.select_set(True)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.duplicate()
    posed_arm = bpy.context.active_object

    arm_obj.location = (-1.15, 0, 0)
    posed_arm.location = (1.15, 0, 0)
    pose(posed_arm, WAVE_POSE)

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
    bpy.ops.object.camera_add(location=(0, -7.5, 1.6))
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
    scene.render.resolution_x = 1400
    scene.render.resolution_y = 800
    scene.render.image_settings.file_format = 'PNG'
    return body, arm_obj


if __name__ == "__main__":
    build()
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "zayn_rig.png")
    bpy.context.scene.render.filepath = out_path
    bpy.ops.render.render(write_still=True)
    print(f"RENDERED_TO:{out_path}")
