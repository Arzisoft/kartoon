"""
Zayn with a real armature + automatic-weight skinning (works now that the mesh is clean
retopologized quads, unlike the old triangulated voxel-remesh mesh), posed hands-on-hips to
match the reference. Also punches up color saturation toward the reference's vivid orange.
"""
import bpy
import math
import os
import sys
from mathutils import Vector, Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import base_body  # noqa: E402
import color_layer  # noqa: E402
import toon_shader  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RETOPO = os.path.join(HERE, "retopo")

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

bpy.ops.wm.obj_import(filepath=os.path.join(RETOPO, "zayn_retopo.obj"), forward_axis='Y', up_axis='Z')
zayn = bpy.context.selected_objects[0]
zayn.name = "Zayn_Pose"
zayn.modifiers.new("Subsurf", 'SUBSURF').levels = 1

# More saturated/vivid orange, closer to the reference than the earlier muted tan
tan_toon = toon_shader.toon_material("Zayn_Vivid_Skin", (0.95, 0.55, 0.14))
zayn.data.materials.append(tan_toon)
bpy.ops.object.select_all(action='DESELECT'); zayn.select_set(True)
bpy.context.view_layer.objects.active = zayn
bpy.ops.object.shade_smooth()

dark_brown = toon_shader.toon_material("Zayn_Vivid_Dark", (0.28, 0.16, 0.08))
hands, hoofs = {}, {}
for side in (1, -1):
    hoofs[side] = color_layer.extremity_cap(
        f"Zayn_Hoof_{side}", [(0.098, (0.180 * side, -0.035, 0.070), (0.90, 1.25, 0.70))],
        dark_brown, parent=zayn,
    )[0]
    hands[side] = color_layer.extremity_cap(
        f"Zayn_Hand_{side}",
        [(0.072, (0.435 * side, -0.070, 0.745), (0.90, 1.05, 1.10)),
         (0.048, (0.370 * side, -0.108, 0.785), (1.0, 1.0, 1.0))],
        dark_brown, parent=zayn,
    )[0]

turquoise_toon = toon_shader.toon_material("Zayn_Vivid_Turquoise", (0.10, 0.62, 0.64))
color_layer.shrinkwrap_accent(
    "Zayn_Blanket", zayn, location=(0, 0.05, 1.25), rotation=(math.radians(35), 0, 0),
    scale=(1.0, 0.75, 1.0), material=turquoise_toon, size=0.85, subdiv_cuts=6,
    offset=0.02, thickness=0.03, parent=zayn,
)
base_body._preview_eyes("Zayn_Base", zayn)

# ---------------------------------------------------------------- armature
J = base_body.ZAYN_JOINTS

def jp(name, side=1):
    x, y, z = J[name]
    return (x * side, y, z)

arm_data = bpy.data.armatures.new("Zayn_Armature")
arm_obj = bpy.data.objects.new("Zayn_Rig", arm_data)
scene.collection.objects.link(arm_obj)
bpy.context.view_layer.objects.active = arm_obj
bpy.ops.object.mode_set(mode='EDIT')
eb = arm_data.edit_bones

spine_base = eb.new("spine_base"); spine_base.head = jp("pelvis"); spine_base.tail = jp("chest")
neck = eb.new("neck"); neck.head = jp("chest"); neck.tail = jp("neck_base"); neck.parent = spine_base
head = eb.new("head"); head.head = jp("neck_base"); head.tail = jp("head_base"); head.parent = neck

arm_bones = {}
for side in (1, -1):
    tag = "L" if side > 0 else "R"
    up = eb.new(f"upperarm_{tag}"); up.head = jp("shoulder", side); up.tail = jp("elbow", side)
    up.parent = spine_base; up.use_connect = False
    lo = eb.new(f"lowerarm_{tag}"); lo.head = jp("elbow", side); lo.tail = jp("wrist", side)
    lo.parent = up; lo.use_connect = True
    arm_bones[side] = (up.name, lo.name)

bpy.ops.object.mode_set(mode='OBJECT')

# Bind: select mesh + separate extremity objects, then the armature (active), auto weights
# for the main mesh; extremities are simple rigid bone-parents to the wrist (small rigid
# parts, don't need deforming skin weights).
bpy.ops.object.select_all(action='DESELECT')
zayn.select_set(True)
arm_obj.select_set(True)
bpy.context.view_layer.objects.active = arm_obj
bpy.ops.object.parent_set(type='ARMATURE_AUTO')

for side in (1, -1):
    tag = "L" if side > 0 else "R"
    for cap in (hands[side], hoofs[side]):
        desired_world = cap.matrix_world.copy()
        cap.parent = arm_obj
        cap.parent_type = 'BONE'
        cap.parent_bone = f"lowerarm_{tag}" if cap is hands[side] else f"upperarm_{tag}"
        cap.matrix_parent_inverse = Matrix.Identity(4)
        cap.matrix_world = desired_world

# ---------------------------------------------------------------- pose: hands on hips
bpy.context.view_layer.objects.active = arm_obj
bpy.ops.object.mode_set(mode='POSE')
for side in (1, -1):
    tag = "L" if side > 0 else "R"
    up_name, lo_name = arm_bones[side]
    up_pb = arm_obj.pose.bones[up_name]
    lo_pb = arm_obj.pose.bones[lo_name]
    up_pb.rotation_mode = 'XYZ'
    lo_pb.rotation_mode = 'XYZ'
    # Swing upper arm down and slightly forward/inward; bend elbow to bring forearm+hand
    # in toward the hip. Signs mirrored by side for left/right symmetry.
    up_pb.rotation_euler = (math.radians(-25), math.radians(15 * side), math.radians(10 * side))
    lo_pb.rotation_euler = (math.radians(-70), math.radians(25 * side), 0)
bpy.ops.object.mode_set(mode='OBJECT')

base_body._stage(target_z=1.4, cam_dist=5.2, res_x=1400, res_y=1200)
out = os.path.join(HERE, "zayn_pose.png")
scene.render.filepath = out
bpy.ops.render.render(write_still=True)
print(f"RENDERED_TO:{out}")
