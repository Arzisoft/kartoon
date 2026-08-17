"""Export Zayn and Milo's current base meshes as OBJ for AutoRemesher."""
import bpy
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import base_body  # noqa: E402

bpy.ops.wm.read_factory_settings(use_empty=True)
zayn = base_body.build_zayn_base()
milo = base_body.build_milo_base()

here = os.path.dirname(os.path.abspath(__file__))
export_dir = os.path.join(here, "retopo")
os.makedirs(export_dir, exist_ok=True)

for obj, name in [(zayn, "zayn_raw"), (milo, "milo_raw")]:
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    path = os.path.join(export_dir, f"{name}.obj")
    bpy.ops.wm.obj_export(filepath=path, export_selected_objects=True,
                           export_materials=False, export_triangulated_mesh=True)
    print(f"EXPORTED:{path}")
    print(f"{name.upper()}_VERTS:{len(obj.data.vertices)}")
