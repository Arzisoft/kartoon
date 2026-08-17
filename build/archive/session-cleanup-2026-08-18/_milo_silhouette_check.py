import bpy, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import base_body, color_layer

HERE = os.path.dirname(os.path.abspath(__file__))
RETOPO = os.path.join(HERE, "retopo")

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

bpy.ops.wm.obj_import(filepath=os.path.join(RETOPO, "milo_retopo.obj"), forward_axis='Y', up_axis='Z')
milo = bpy.context.selected_objects[0]
milo.name = "Milo_Sil"
milo.modifiers.new("Subsurf", 'SUBSURF').levels = 1

sil = bpy.data.materials.new("Sil")
sil.use_nodes = True
nt = sil.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
em = nt.nodes.new("ShaderNodeEmission")
em.inputs["Color"].default_value = (0.05, 0.05, 0.05, 1.0)
out = nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
milo.data.materials.append(sil)

color_layer.anchored_protrusion(
    "Milo_Beak", milo,
    base_location=(0, -0.235, 1.045), tip_offset=(0, -0.085, -0.045),
    base_radius=0.045, tip_radius=0.0, material=sil, parent=milo,
)

world = bpy.data.worlds.new("W"); scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.95, 0.95, 0.95, 1.0)

target = bpy.data.objects.new("T", None); target.location = (0, 0, 0.7)
scene.collection.objects.link(target)
bpy.ops.object.camera_add(location=(0, -3.2, 0.95))
cam = bpy.context.active_object
tr = cam.constraints.new(type='TRACK_TO'); tr.target = target
tr.track_axis = 'TRACK_NEGATIVE_Z'; tr.up_axis = 'UP_Y'
scene.camera = cam
try:
    scene.render.engine = 'BLENDER_EEVEE_NEXT'
except Exception:
    scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 200
scene.render.resolution_y = 200
out_path = os.path.join(HERE, "milo_silhouette_check.png")
scene.render.filepath = out_path
bpy.ops.render.render(write_still=True)
print(f"RENDERED_TO:{out_path}")
