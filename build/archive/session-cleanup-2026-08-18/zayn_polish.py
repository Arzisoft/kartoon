"""
Zayn polish pass: builds on the AutoRemesher-retopologized mesh (clean quads) instead of the
raw voxel-remesh output, applies SSS + blanket accent, and adds a Subsurf pass on the now-
clean topology (safe to do now — proper quad flow means Subsurf rounds predictably instead of
shrinking unevenly like it did on the old triangulated voxel mesh).

Run standalone: blender --background --python zayn_polish.py
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

bpy.ops.wm.obj_import(filepath=os.path.join(RETOPO, "zayn_retopo.obj"), forward_axis='Y', up_axis='Z')
zayn = bpy.context.selected_objects[0]
zayn.name = "Zayn_Polished"

# Now that topology is clean quads (post-retopo), a light Subsurf pass rounds forms evenly
# instead of shrinking unevenly the way it did on the old triangulated voxel-remesh mesh.
mod = zayn.modifiers.new("Subsurf", 'SUBSURF')
mod.levels = 1
mod.render_levels = 2

tan = color_layer.matte_material("Zayn_Tan_Polished", (0.85, 0.64, 0.40), subsurface=0.4)
zayn.data.materials.append(tan)
bpy.ops.object.select_all(action='DESELECT')
zayn.select_set(True)
bpy.context.view_layer.objects.active = zayn
bpy.ops.object.shade_smooth()

turquoise = color_layer.matte_material("Turquoise_Polished", (0.08, 0.52, 0.53))
color_layer.shrinkwrap_accent(
    "Zayn_Blanket", zayn,
    location=(0, 0.05, 1.25), rotation=(math.radians(35), 0, 0),
    scale=(1.0, 0.75, 1.0), material=turquoise,
    size=0.85, subdiv_cuts=6, offset=0.02, thickness=0.03, parent=zayn,
)

base_body._preview_eyes("Zayn_Base", zayn)
base_body._stage(target_z=1.5, cam_dist=5.5, res_x=1400, res_y=1000)

out = os.path.join(HERE, "zayn_polish_wide.png")
scene.render.filepath = out
bpy.ops.render.render(write_still=True)
print(f"RENDERED_TO:{out}")

# close-up
target = bpy.data.objects.get("Target")
target.location = (0, 0, 2.1)
cam = scene.camera
cam.location = (-0.2, -1.7, 2.15)
out2 = os.path.join(HERE, "zayn_polish_closeup.png")
scene.render.filepath = out2
bpy.ops.render.render(write_still=True)
print(f"RENDERED_TO:{out2}")
