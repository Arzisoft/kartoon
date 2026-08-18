"""Both polished characters side by side, current state."""
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
zayn.name = "Zayn_Final"
zayn.modifiers.new("Subsurf", 'SUBSURF').levels = 1
tan = color_layer.matte_material("Zayn_Tan_F", (0.85, 0.64, 0.40), subsurface=0.4)
zayn.data.materials.append(tan)
bpy.ops.object.select_all(action='DESELECT'); zayn.select_set(True)
bpy.context.view_layer.objects.active = zayn
bpy.ops.object.shade_smooth()
turquoise = color_layer.matte_material("Turquoise_F", (0.08, 0.52, 0.53))
color_layer.shrinkwrap_accent(
    "Zayn_Blanket", zayn, location=(0, 0.05, 1.25), rotation=(math.radians(35), 0, 0),
    scale=(1.0, 0.75, 1.0), material=turquoise, size=0.85, subdiv_cuts=6,
    offset=0.02, thickness=0.03, parent=zayn,
)
dark_brown = color_layer.matte_material("Dark_Brown_Zayn", (0.22, 0.14, 0.08), roughness=0.4)
for side in (1, -1):
    color_layer.extremity_cap(
        f"Zayn_Hoof_{side}", [(0.098, (0.180 * side, -0.035, 0.070), (0.90, 1.25, 0.70))],
        dark_brown, parent=zayn,
    )
    color_layer.extremity_cap(
        f"Zayn_Hand_{side}",
        [(0.072, (0.435 * side, -0.070, 0.745), (0.90, 1.05, 1.10)),
         (0.048, (0.370 * side, -0.108, 0.785), (1.0, 1.0, 1.0))],
        dark_brown, parent=zayn,
    )
zayn.location = (-1.1, 0, 0)
base_body._preview_eyes("Zayn_Base", zayn)

bpy.ops.wm.obj_import(filepath=os.path.join(RETOPO, "milo_retopo.obj"), forward_axis='Y', up_axis='Z')
milo = bpy.context.selected_objects[0]
milo.name = "Milo_Final"
milo.modifiers.new("Subsurf", 'SUBSURF').levels = 1
yellow = color_layer.matte_material("Milo_Yellow_F", (0.98, 0.82, 0.10), subsurface=0.4)
milo.data.materials.append(yellow)
bpy.ops.object.select_all(action='DESELECT'); milo.select_set(True)
bpy.context.view_layer.objects.active = milo
bpy.ops.object.shade_smooth()
beak_mat = color_layer.matte_material("Beak_Orange_F", (0.85, 0.45, 0.12), roughness=0.4)
color_layer.anchored_protrusion(
    "Milo_Beak", milo, base_location=(0, -0.235, 1.045), tip_offset=(0, -0.085, -0.045),
    base_radius=0.045, tip_radius=0.0, material=beak_mat, parent=milo,
)
cheek_mat = color_layer.matte_material("Turquoise_Milo_F", (0.08, 0.52, 0.53))
for side in (1, -1):
    color_layer.shrinkwrap_accent(
        f"Milo_Cheek_{side}", milo, location=(0.155 * side, -0.20, 0.995),
        rotation=(math.radians(90), 0, 0), scale=(0.85, 1.0, 1.0), material=cheek_mat,
        size=0.10, subdiv_cuts=3, offset=0.012, thickness=0.008, parent=milo,
    )
dark_brown_m = color_layer.matte_material("Dark_Brown_Milo", (0.22, 0.14, 0.08), roughness=0.4)
for side in (1, -1):
    color_layer.extremity_cap(
        f"Milo_Foot_{side}", [(0.062, (0.110 * side, -0.055, 0.038), (0.80, 1.70, 0.45))],
        dark_brown_m, parent=milo,
    )
    color_layer.extremity_cap(
        f"Milo_Hand_{side}",
        [(0.050, (0.350 * side, -0.035, 0.255), (0.85, 1.05, 1.0)),
         (0.026, (0.300 * side, -0.065, 0.275), (1.0, 1.0, 1.0))],
        dark_brown_m, parent=milo,
    )
milo.location = (0.75, 0, 0)
base_body._preview_eyes("Milo_Base", milo)

base_body._stage(target_z=1.05, cam_dist=5.2, res_x=1600, res_y=1000)
out = os.path.join(HERE, "lineup_polish.png")
scene.render.filepath = out
bpy.ops.render.render(write_still=True)
print(f"RENDERED_TO:{out}")
