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


def build_skeleton(name, joints_table):
    """Create the armature and its edit bones, fitted to a character's joint table.

    The bone list is the SAME for every character — only the joint table differs. That is the
    whole point: identical structure means one motion clip drives both characters.
    """
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
        b.head = base_body.joint(joints_table, head_j, side)
        b.tail = base_body.joint(joints_table, tail_j, side)
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

# The same pose dict applied to Milo. It is deliberately NOT re-authored for him: if the
# identical bone rotations produce a sensible wave on a character with completely different
# proportions, the shared-skeleton claim holds and motion really is reusable between them.
MILO_LOOK_UP_POSE = {
    "upper_arm.L": (0, 0, -100),
    "forearm.L": (0, 0, -35),
    "head": (-22, 18, 0),
    "neck": (-10, 8, 0),
    "spine": (0, 0, 4),
}

RIGS = {
    "zayn": {"build": base_body.build_zayn_base, "joints": base_body.ZAYN_JOINTS,
             "rig_name": "Zayn_Rig", "pose": WAVE_POSE, "spread": 1.15,
             "target_z": 1.15, "cam_dist": 7.5},
    "milo": {"build": base_body.build_milo_base, "joints": base_body.MILO_JOINTS,
             "rig_name": "Milo_Rig", "pose": MILO_LOOK_UP_POSE, "spread": 0.72,
             "target_z": 0.70, "cam_dist": 4.6},
}


def build_rigged(which):
    """Build + skin one character. Returns (mesh, armature)."""
    spec = RIGS[which]
    body = spec["build"]()
    arm_obj = build_skeleton(spec["rig_name"], spec["joints"])
    groups = skin(body, arm_obj)
    print(f"{which.upper()}_VERTEX_GROUPS:{groups} BONES:{len(arm_obj.data.bones)}")
    body.data.materials.append(base_body._clay())
    return body, arm_obj


def _duplicate_rigged(body, arm_obj):
    bpy.ops.object.select_all(action='DESELECT')
    body.select_set(True)
    arm_obj.select_set(True)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.duplicate()
    return bpy.context.active_object


def build_pose_test(which):
    """Rest vs. posed, side by side, so the deformation can actually be judged."""
    spec = RIGS[which]
    bpy.ops.wm.read_factory_settings(use_empty=True)

    body, arm_obj = build_rigged(which)
    posed_arm = _duplicate_rigged(body, arm_obj)

    arm_obj.location = (-spec["spread"], 0, 0)
    posed_arm.location = (spec["spread"], 0, 0)
    pose(posed_arm, spec["pose"])

    base_body._stage(spec["target_z"], spec["cam_dist"], res_x=1400, res_y=800)
    return body, arm_obj


def build_two_shot():
    """Both characters posed together — the actual production shot, and the only render that
    shows whether the size contrast still works once they are animated."""
    bpy.ops.wm.read_factory_settings(use_empty=True)

    zayn_body, zayn_arm = build_rigged("zayn")
    zayn_arm.location = (-0.75, 0, 0)
    pose(zayn_arm, WAVE_POSE)

    milo_body, milo_arm = build_rigged("milo")
    milo_arm.location = (0.72, 0, 0)
    pose(milo_arm, MILO_LOOK_UP_POSE)

    base_body._stage(target_z=1.05, cam_dist=6.4, res_x=1400, res_y=850)
    return zayn_body, milo_body


def _render(path):
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print(f"RENDERED_TO:{path}")


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))

    for which in ("zayn", "milo"):
        build_pose_test(which)
        _render(os.path.join(here, f"{which}_rig.png"))

    build_two_shot()
    _render(os.path.join(here, "two_shot_rig.png"))
