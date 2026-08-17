"""
Armature test for Zayn and Milo — rigid bone-parenting (not heat-map skinning).
Each character is built from separate primitive objects (not one continuous mesh), so every
part is parented rigidly to its single best-fit bone. This avoids heat-map weight-bleed, which
is what collapsed Milo's mesh in the first rig attempt.
Run headless: blender --background --python rig_test.py
"""
import bpy
import math
import os
import sys
from mathutils import Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import characters  # noqa: E402

zayn_root, milo_root = characters.build_scene()
scene = bpy.context.scene

try:
    bpy.ops.preferences.addon_enable(module='rigify')
except Exception as e:
    print(f"rigify addon enable failed (continuing with plain armature): {e}")


def new_armature(name, location=(0, 0, 0)):
    data = bpy.data.armatures.new(f"{name}_Data")
    obj = bpy.data.objects.new(name, data)
    obj.location = location
    scene.collection.objects.link(obj)
    return obj


def build_bones(arm_obj, bone_defs):
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='EDIT')
    eb = arm_obj.data.edit_bones
    made = {}
    for name, head, tail, parent_name in bone_defs:
        b = eb.new(name)
        b.head = head
        b.tail = tail
        if parent_name:
            b.parent = made[parent_name]
            b.use_connect = False
        made[name] = b
    bpy.ops.object.mode_set(mode='OBJECT')


def bone_parent(obj, arm_obj, bone_name):
    """Rigid-parent obj to a single bone, preserving its current world transform."""
    desired_world = obj.matrix_world.copy()
    obj.parent = arm_obj
    obj.parent_type = 'BONE'
    obj.parent_bone = bone_name
    obj.matrix_parent_inverse = Matrix.Identity(4)
    obj.matrix_world = desired_world


def rig_rigid(arm_obj, mesh_root, bone_defs, part_to_bone):
    build_bones(arm_obj, bone_defs)
    for obj in list(mesh_root.children):
        if obj.type != 'MESH':
            continue
        bone_name = part_to_bone.get(obj.name)
        if bone_name is None:
            print(f"WARNING: no bone mapping for {obj.name}, leaving under empty parent")
            continue
        bone_parent(obj, arm_obj, bone_name)


# ---------- ZAYN rig ----------
zx, zy, zz = zayn_root.location
zayn_arm = new_armature("Zayn_Rig")
zayn_bones = [
    ("spine_base", (zx, zy, 0.15), (zx, zy, 0.55), None),
    ("spine_mid", (zx, zy, 0.55), (zx - 0.15, zy, 1.5), "spine_base"),
    ("neck", (zx + 0.34, zy, 1.57), (zx + 1.56, zy, 2.13), "spine_mid"),
    ("head", (zx + 1.56, zy, 2.13), (zx + 2.28, zy, 2.10), "neck"),
    ("leg_fr", (zx + 0.5, zy + 0.5, 0.55), (zx + 0.5, zy + 0.5, 0.0), "spine_base"),
    ("leg_fl", (zx + 0.5, zy - 0.5, 0.55), (zx + 0.5, zy - 0.5, 0.0), "spine_base"),
    ("leg_br", (zx - 0.55, zy + 0.5, 0.55), (zx - 0.55, zy + 0.5, 0.0), "spine_base"),
    ("leg_bl", (zx - 0.55, zy - 0.5, 0.55), (zx - 0.55, zy - 0.5, 0.0), "spine_base"),
]
zayn_part_to_bone = {
    "Zayn_Body": "spine_mid",
    "Zayn_Hump": "spine_mid",
    "Zayn_Blanket": "spine_mid",
    "Zayn_Neck": "neck",
    "Zayn_Head": "head",
    "Zayn_Muzzle": "head",
    "Zayn_Lip": "head",
    "Zayn_Eye_L": "head",
    "Zayn_Eye_R": "head",
    "Zayn_Ear_L": "head",
    "Zayn_Ear_R": "head",
    "Zayn_Leg_0": "leg_fr",
    "Zayn_Leg_1": "leg_fl",
    "Zayn_Leg_2": "leg_br",
    "Zayn_Leg_3": "leg_bl",
}
rig_rigid(zayn_arm, zayn_root, zayn_bones, zayn_part_to_bone)

# ---------- MILO rig ----------
mx, my, mz = milo_root.location
milo_arm = new_armature("Milo_Rig")
milo_bones = [
    ("body_base", (mx, my, mz - 0.5), (mx, my, mz), None),
    ("neck", (mx, my, mz), (mx + 0.02, my, mz + 0.75), "body_base"),
    ("head", (mx + 0.02, my, mz + 0.75), (mx + 0.56, my, mz + 0.60), "neck"),
    ("wing_l", (mx, my + 0.05, mz + 0.02), (mx - 0.15, my + 0.46, mz + 0.02), "body_base"),
    ("wing_r", (mx, my - 0.05, mz + 0.02), (mx - 0.15, my - 0.46, mz + 0.02), "body_base"),
    ("tail", (mx, my, mz - 0.05), (mx - 0.62, my, mz - 0.05), "body_base"),
    ("leg_l", (mx + 0.02, my + 0.14, mz + 0.3), (mx + 0.02, my + 0.14, mz - 0.04), "body_base"),
    ("leg_r", (mx + 0.02, my - 0.14, mz + 0.3), (mx + 0.02, my - 0.14, mz - 0.04), "body_base"),
]
milo_part_to_bone = {
    "Milo_Body": "body_base",
    "Milo_Head": "head",
    "Milo_Cere": "head",
    "Milo_Beak": "head",
    "Milo_Beak_Hook": "head",
    "Milo_Eye_L": "head",
    "Milo_Eye_R": "head",
    "Milo_Cheek_L": "head",
    "Milo_Cheek_R": "head",
    "Milo_Wing_L": "wing_l",
    "Milo_Wing_R": "wing_r",
    "Milo_Tail": "tail",
    "Milo_Leg_0": "leg_l",
    "Milo_Leg_1": "leg_r",
}
rig_rigid(milo_arm, milo_root, milo_bones, milo_part_to_bone)

# ---------- pose test: prove the rig deforms the mesh ----------
for arm_obj, poses in [
    (zayn_arm, {"neck": (math.radians(-25), 0, 0), "leg_fr": (0, math.radians(20), 0)}),
    (milo_arm, {"wing_l": (0, 0, math.radians(45)), "wing_r": (0, 0, math.radians(-45)),
                "head": (0, math.radians(20), 0)}),
]:
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='POSE')
    for bone_name, euler in poses.items():
        pb = arm_obj.pose.bones[bone_name]
        pb.rotation_mode = 'XYZ'
        pb.rotation_euler = euler
    bpy.ops.object.mode_set(mode='OBJECT')

out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rig_test.png")
scene.render.filepath = out_path
bpy.ops.render.render(write_still=True)
print(f"RENDERED_TO:{out_path}")
