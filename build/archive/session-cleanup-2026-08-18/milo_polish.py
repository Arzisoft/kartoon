"""Milo polish pass: same treatment as zayn_polish.py — retopologized mesh + Subsurf + SSS +
shrinkwrapped cheek-patch accents. Run standalone: blender --background --python milo_polish.py
"""
import bpy
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import base_body  # noqa: E402
import color_layer  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RETOPO = os.path.join(HERE, "retopo")

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

bpy.ops.wm.obj_import(filepath=os.path.join(RETOPO, "milo_retopo.obj"), forward_axis='Y', up_axis='Z')
milo = bpy.context.selected_objects[0]
milo.name = "Milo_Polished"

mod = milo.modifiers.new("Subsurf", 'SUBSURF')
mod.levels = 1
mod.render_levels = 2

yellow = color_layer.matte_material("Milo_Yellow_Polished", (0.98, 0.82, 0.10), subsurface=0.4)
milo.data.materials.append(yellow)
bpy.ops.object.select_all(action='DESELECT')
milo.select_set(True)
bpy.context.view_layer.objects.active = milo
bpy.ops.object.shade_smooth()

beak_mat = color_layer.matte_material("Beak_Orange", (0.85, 0.45, 0.12), roughness=0.4)
# Base anchored to the head surface (head centre y=-0.02, z=1.085, radius 0.235 -> front
# surface at y~-0.255); tip protrudes forward and hooks down, independent of exact head
# proportions since only the base ring is shrinkwrapped.
color_layer.anchored_protrusion(
    "Milo_Beak", milo,
    base_location=(0, -0.235, 1.045), tip_offset=(0, -0.085, -0.045),
    base_radius=0.045, tip_radius=0.0, material=beak_mat, parent=milo,
)

turquoise = color_layer.matte_material("Turquoise_Milo_Polished", (0.08, 0.52, 0.53))
for side in (1, -1):
    color_layer.shrinkwrap_accent(
        f"Milo_Cheek_{side}", milo,
        location=(0.155 * side, -0.20, 0.995), rotation=(math.radians(90), 0, 0),
        scale=(0.85, 1.0, 1.0), material=turquoise,
        size=0.10, subdiv_cuts=3, offset=0.012, thickness=0.008, parent=milo,
    )

base_body._preview_eyes("Milo_Base", milo)
base_body._stage(target_z=1.05, cam_dist=4.0, res_x=1400, res_y=1000)

out = os.path.join(HERE, "milo_polish_wide.png")
scene.render.filepath = out
bpy.ops.render.render(write_still=True)
print(f"RENDERED_TO:{out}")

target = bpy.data.objects.get("Target")
target.location = (0, 0, 1.1)
cam = scene.camera
cam.location = (-0.15, -1.1, 1.15)
out2 = os.path.join(HERE, "milo_polish_closeup.png")
scene.render.filepath = out2
bpy.ops.render.render(write_still=True)
print(f"RENDERED_TO:{out2}")
