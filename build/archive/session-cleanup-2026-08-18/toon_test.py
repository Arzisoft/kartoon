import bpy, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import base_body, color_layer, toon_shader

HERE = os.path.dirname(os.path.abspath(__file__))
RETOPO = os.path.join(HERE, "retopo")

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

bpy.ops.wm.obj_import(filepath=os.path.join(RETOPO, "zayn_retopo.obj"), forward_axis='Y', up_axis='Z')
zayn = bpy.context.selected_objects[0]
zayn.name = "Zayn_Toon"
zayn.modifiers.new("Subsurf", 'SUBSURF').levels = 1

tan_toon = toon_shader.toon_material("Zayn_Toon_Skin", (0.90, 0.62, 0.30))
zayn.data.materials.append(tan_toon)
bpy.ops.object.select_all(action='DESELECT'); zayn.select_set(True)
bpy.context.view_layer.objects.active = zayn
bpy.ops.object.shade_smooth()

dark_brown = toon_shader.toon_material("Zayn_Toon_Dark", (0.30, 0.18, 0.09), band_count=2)
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

#toon_shader.add_outline(zayn, thickness=0.012)  # parked -- see toon_shader.py docstring note

base_body._preview_eyes("Zayn_Base", zayn)
base_body._stage(target_z=1.5, cam_dist=5.5, res_x=1400, res_y=1000)

out = os.path.join(HERE, "toon_test.png")
scene.render.filepath = out
bpy.ops.render.render(write_still=True)
print(f"RENDERED_TO:{out}")
