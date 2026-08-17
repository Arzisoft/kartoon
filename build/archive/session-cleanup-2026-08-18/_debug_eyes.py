import bpy, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import base_body

HERE = os.path.dirname(os.path.abspath(__file__))
RETOPO = os.path.join(HERE, "retopo")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=os.path.join(RETOPO, "zayn_retopo.obj"), forward_axis='Y', up_axis='Z')
zayn = bpy.context.selected_objects[0]
zayn.name = "Zayn_Debug"

print("ZAYN location:", tuple(zayn.location))
print("ZAYN dimensions:", tuple(zayn.dimensions))
print("ZAYN bound_box world corners:")
for c in zayn.bound_box:
    world_c = zayn.matrix_world @ __import__("mathutils").Vector(c)
    print("  ", tuple(round(v, 3) for v in world_c))

eyes = base_body._preview_eyes("Zayn_Base", zayn)
print(f"Created {len(eyes)} eye objects")
for e in eyes:
    print(f"  {e.name}: location={tuple(e.location)} world={tuple(round(v,3) for v in e.matrix_world.translation)} parent={e.parent}")
