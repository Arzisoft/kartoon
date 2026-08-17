"""Import the AutoRemesher output and render it to confirm the retopology didn't break anything."""
import bpy
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import base_body  # noqa: E402
import color_layer  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RETOPO = os.path.join(HERE, "retopo")

bpy.ops.wm.read_factory_settings(use_empty=True)

tan = color_layer.matte_material("Zayn_Tan", (0.85, 0.64, 0.40))
yellow = color_layer.matte_material("Milo_Yellow", (0.98, 0.82, 0.10))

bpy.ops.wm.obj_import(filepath=os.path.join(RETOPO, "zayn_retopo.obj"))
zayn = bpy.context.selected_objects[0]
zayn.name = "Zayn_Retopo"
zayn.data.materials.append(tan)
zayn.location = (-0.9, 0, 0)
bpy.ops.object.shade_smooth()

bpy.ops.wm.obj_import(filepath=os.path.join(RETOPO, "milo_retopo.obj"))
milo = bpy.context.selected_objects[0]
milo.name = "Milo_Retopo"
milo.data.materials.append(yellow)
milo.location = (0.85, 0, 0)
bpy.ops.object.shade_smooth()

base_body._preview_eyes("Zayn_Base", zayn)
base_body._preview_eyes("Milo_Base", milo)
base_body._stage(target_z=1.05, cam_dist=6.4, res_x=1600, res_y=900)

out = os.path.join(HERE, "retopo_check.png")
bpy.context.scene.render.filepath = out
bpy.ops.render.render(write_still=True)
print(f"RENDERED_TO:{out}")
