"""
Zayn, consolidated: full current outfit (shirt+sleeves+badge, shorts, water-canteen cap,
4-finger hands, hoof feet) + Cycles/SSS/HDRI soft lighting + a real hands-on-hips pose via
armature + automatic-weight skinning on the clean retopologized mesh.
"""
import bpy
import math
import os
import sys
from mathutils import Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import base_body  # noqa: E402
import color_layer  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RETOPO = os.path.join(HERE, "retopo")
HDRI = os.path.join(HERE, "hdri", "studio_small_08_1k.hdr")

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene


def sss_material(name, color, roughness=0.28, subsurface=0.8, radius=(0.9, 0.45, 0.2)):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    for weight_key in ("Subsurface Weight", "Subsurface"):
        if weight_key in bsdf.inputs:
            bsdf.inputs[weight_key].default_value = subsurface
            break
    if "Subsurface Radius" in bsdf.inputs:
        bsdf.inputs["Subsurface Radius"].default_value = radius
    return mat


bpy.ops.wm.obj_import(filepath=os.path.join(RETOPO, "zayn_retopo.obj"), forward_axis='Y', up_axis='Z')
zayn = bpy.context.selected_objects[0]
zayn.name = "Zayn_Final"
zayn.modifiers.new("Subsurf", 'SUBSURF').levels = 2

skin_mat = sss_material("Zayn_Final_Skin", (0.95, 0.58, 0.18))
zayn.data.materials.append(skin_mat)
bpy.ops.object.select_all(action='DESELECT'); zayn.select_set(True)
bpy.context.view_layer.objects.active = zayn
bpy.ops.object.shade_smooth()

dark_brown = sss_material("Zayn_Final_Dark", (0.26, 0.15, 0.07), roughness=0.32, subsurface=0.0)
hands, hoofs = {}, {}
for side in (1, -1):
    hoofs[side] = color_layer.extremity_cap(
        f"Zayn_Hoof_{side}", [(0.098, (0.180 * side, -0.035, 0.070), (0.90, 1.25, 0.70))],
        dark_brown, parent=zayn,
    )[0]
    palm = (0.435 * side, -0.070, 0.745)
    finger_offsets = [(-0.030, -0.075, 0.015), (-0.010, -0.085, 0.000),
                       (0.010, -0.080, -0.015), (0.028, -0.065, -0.028)]
    finger_parts = [(0.052, palm, (1.0, 1.0, 1.0))]
    for fx, fy, fz in finger_offsets:
        finger_parts.append((0.024, (palm[0] + fx * side, palm[1] + fy, palm[2] + fz),
                              (0.85, 1.9, 0.85)))
    hands[side] = color_layer.extremity_cap(f"Zayn_Hand_{side}", finger_parts, dark_brown, parent=zayn)[0]

cap_mat = sss_material("Zayn_Final_Cap", (0.15, 0.55, 0.75), roughness=0.3, subsurface=0.0)
spout_mat = sss_material("Zayn_Final_Spout", (0.08, 0.35, 0.48), roughness=0.35, subsurface=0.0)
color_layer.extremity_cap("Zayn_Cap", [(0.155, (0, -0.02, 2.23), (1.05, 1.05, 0.62))], cap_mat, parent=zayn)
color_layer.extremity_cap("Zayn_Cap_Spout", [(0.038, (0, -0.01, 2.33), (1.0, 1.0, 0.9))], spout_mat, parent=zayn)

shirt_mat = sss_material("Zayn_Final_Shirt", (0.85, 0.18, 0.15), roughness=0.55, subsurface=0.0)
color_layer.extremity_cap("Zayn_Shirt", [(0.30, (0, -0.01, 1.24), (0.98, 1.0, 1.55))], shirt_mat, parent=zayn)
for side in (1, -1):
    color_layer.extremity_cap(
        f"Zayn_Sleeve_{side}", [(0.095, (0.235 * side, 0.02, 1.40), (1.0, 1.0, 0.9))],
        shirt_mat, parent=zayn,
    )
badge_mat = sss_material("Zayn_Final_Badge", (1.0, 0.95, 0.9), roughness=0.4, subsurface=0.0)
color_layer.extremity_cap("Zayn_Badge", [(0.065, (0, -0.27, 1.26), (1.0, 1.0, 0.28))], badge_mat, parent=zayn)

shorts_mat = sss_material("Zayn_Final_Shorts", (0.95, 0.75, 0.10), roughness=0.55, subsurface=0.0)
color_layer.extremity_cap("Zayn_Shorts", [(0.24, (0, 0.0, 0.97), (1.0, 1.0, 0.9))], shorts_mat, parent=zayn)

eyes = base_body._preview_eyes("Zayn_Base", zayn)
for e in eyes:
    if "Sclera" in e.name:
        e.data.materials[0].node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.1

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

bpy.ops.object.select_all(action='DESELECT')
zayn.select_set(True)
arm_obj.select_set(True)
bpy.context.view_layer.objects.active = arm_obj
bpy.ops.object.parent_set(type='ARMATURE_AUTO')

for side in (1, -1):
    tag = "L" if side > 0 else "R"
    desired_world = hands[side].matrix_world.copy()
    hands[side].parent = arm_obj
    hands[side].parent_type = 'BONE'
    hands[side].parent_bone = f"lowerarm_{tag}"
    hands[side].matrix_parent_inverse = Matrix.Identity(4)
    hands[side].matrix_world = desired_world

# ---------------------------------------------------------------- pose: hands on hips
bpy.context.view_layer.objects.active = arm_obj
bpy.ops.object.mode_set(mode='POSE')
for side in (1, -1):
    up_name, lo_name = arm_bones[side]
    up_pb = arm_obj.pose.bones[up_name]
    lo_pb = arm_obj.pose.bones[lo_name]
    up_pb.rotation_mode = 'XYZ'
    lo_pb.rotation_mode = 'XYZ'
    up_pb.rotation_euler = (math.radians(-25), math.radians(15 * side), math.radians(10 * side))
    lo_pb.rotation_euler = (math.radians(-70), math.radians(25 * side), 0)
bpy.ops.object.mode_set(mode='OBJECT')

# ---------------------------------------------------------------- HDRI + camera
world = bpy.data.worlds.new("HDRI_World")
scene.world = world
world.use_nodes = True
wnt = world.node_tree
for n in list(wnt.nodes):
    wnt.nodes.remove(n)
env_tex = wnt.nodes.new("ShaderNodeTexEnvironment")
env_tex.image = bpy.data.images.load(HDRI)
bg = wnt.nodes.new("ShaderNodeBackground")
bg.inputs["Strength"].default_value = 1.2
wnt.links.new(env_tex.outputs["Color"], bg.inputs["Color"])
wout = wnt.nodes.new("ShaderNodeOutputWorld")
wnt.links.new(bg.outputs["Background"], wout.inputs["Surface"])

ground_mat = bpy.data.materials.new("Ground")
ground_mat.use_nodes = True
ground_mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.9, 0.9, 0.9, 1)
ground_mat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.5
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
bpy.context.active_object.data.materials.append(ground_mat)

target = bpy.data.objects.new("T", None); target.location = (0, 0, 1.25)
scene.collection.objects.link(target)
bpy.ops.object.camera_add(location=(-0.2, -5.6, 1.7))
cam = bpy.context.active_object
cam.data.lens = 55
tr = cam.constraints.new(type='TRACK_TO'); tr.target = target
tr.track_axis = 'TRACK_NEGATIVE_Z'; tr.up_axis = 'UP_Y'
scene.camera = cam

scene.render.engine = 'CYCLES'
scene.cycles.samples = 160
scene.cycles.use_denoising = True
try:
    scene.cycles.device = 'GPU'
except Exception:
    pass
scene.render.resolution_x = 1200
scene.render.resolution_y = 1500

out = os.path.join(HERE, "zayn_final.png")
scene.render.filepath = out
bpy.ops.render.render(write_still=True)
print(f"RENDERED_TO:{out}")
