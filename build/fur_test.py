"""
Isolated test for procedural fur via Geometry Nodes -- scatter small oriented strand
instances across a surface using Distribute Points on Faces + Instance on Points +
Align Rotation to Vector (face normal), with random length/tilt jitter. This is the
"scriptable, no manual combing" answer researched: fur direction comes from the
surface normal (a short bristly coat), not from interactive grooming.

Run standalone: blender --background --python fur_test.py
"""
import bpy
import os

HERE = os.path.dirname(os.path.abspath(__file__))

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# simple test surface -- a bumpy-ish half sphere stands in for a patch of skin
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.3, location=(0, 0, 0), segments=24, ring_count=12)
surface = bpy.context.active_object
surface.name = "FurTestSurface"
skin_mat = bpy.data.materials.new("TestSkin")
skin_mat.use_nodes = True
skin_mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.85, 0.56, 0.30, 1.0)
surface.data.materials.append(skin_mat)

# fur strand instance object -- much thinner/shorter than the first attempt, which read as
# porcupine quills, not soft coat. Also darkened + matte (roughness up) for a coarse-hair look.
bpy.ops.mesh.primitive_cone_add(radius1=0.0015, radius2=0.0001, depth=0.012, location=(10, 10, 10))
strand = bpy.context.active_object
strand.name = "FurStrand"
fur_mat = bpy.data.materials.new("FurColor")
fur_mat.use_nodes = True
fur_mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.35, 0.20, 0.09, 1.0)
fur_mat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.75
strand.data.materials.append(fur_mat)
scene.collection.objects.unlink(strand)  # hide the template strand itself from the scene

# ---------------------------------------------------------------- geometry nodes fur setup
node_group = bpy.data.node_groups.new("FurGen", "GeometryNodeTree")
node_group.interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
node_group.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

nt = node_group
group_in = nt.nodes.new("NodeGroupInput")
group_out = nt.nodes.new("NodeGroupOutput")

distribute = nt.nodes.new("GeometryNodeDistributePointsOnFaces")
distribute.distribute_method = 'POISSON'
distribute.inputs["Distance Min"].default_value = 0.006
distribute.inputs["Density Max"].default_value = 15000.0
nt.links.new(group_in.outputs["Geometry"], distribute.inputs["Mesh"])

# random per-point scale/rotation jitter so fur doesn't look perfectly uniform
rand_scale = nt.nodes.new("FunctionNodeRandomValue")
rand_scale.data_type = 'FLOAT'
rand_scale.inputs["Min"].default_value = 0.7
rand_scale.inputs["Max"].default_value = 1.4

rand_tilt = nt.nodes.new("FunctionNodeRandomValue")
rand_tilt.data_type = 'FLOAT_VECTOR'
rand_tilt.inputs["Min"].default_value = (-0.35, -0.35, 0.0)
rand_tilt.inputs["Max"].default_value = (0.35, 0.35, 0.0)

align = nt.nodes.new("FunctionNodeAlignRotationToVector")
align.axis = 'Z'
nt.links.new(distribute.outputs["Normal"], align.inputs["Vector"])

combine_rot = nt.nodes.new("ShaderNodeVectorMath")  # add tilt jitter to the aligned rotation
combine_rot.operation = 'ADD'
nt.links.new(align.outputs["Rotation"], combine_rot.inputs[0])
nt.links.new(rand_tilt.outputs["Value"], combine_rot.inputs[1])

strand_info = nt.nodes.new("GeometryNodeObjectInfo")
strand_info.inputs["Object"].default_value = strand

instance = nt.nodes.new("GeometryNodeInstanceOnPoints")
nt.links.new(distribute.outputs["Points"], instance.inputs["Points"])
nt.links.new(strand_info.outputs["Geometry"], instance.inputs["Instance"])
nt.links.new(combine_rot.outputs["Vector"], instance.inputs["Rotation"])
nt.links.new(rand_scale.outputs["Value"], instance.inputs["Scale"])

realize = nt.nodes.new("GeometryNodeRealizeInstances")
nt.links.new(instance.outputs["Instances"], realize.inputs["Geometry"])
nt.links.new(realize.outputs["Geometry"], group_out.inputs["Geometry"])

mod = surface.modifiers.new("Fur", 'NODES')
mod.node_group = node_group

# ---------------------------------------------------------------- render
world = bpy.data.worlds.new("W")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.85, 0.87, 0.9, 1.0)
world.node_tree.nodes["Background"].inputs[1].default_value = 1.0

target = bpy.data.objects.new("T", None)
target.location = (0, 0, 0.05)
scene.collection.objects.link(target)
bpy.ops.object.camera_add(location=(0.15, -0.9, 0.25))
cam = bpy.context.active_object
cam.data.lens = 60
tr = cam.constraints.new(type='TRACK_TO')
tr.target = target
tr.track_axis = 'TRACK_NEGATIVE_Z'
tr.up_axis = 'UP_Y'
scene.camera = cam

for loc, energy in [((-0.5, -0.8, 0.6), 3.0), ((0.5, -0.5, 0.4), 1.5)]:
    bpy.ops.object.light_add(type='AREA', location=loc)
    bpy.context.active_object.data.energy = energy
    bpy.context.active_object.data.size = 0.5

scene.render.engine = 'CYCLES'
scene.cycles.samples = 96
scene.render.resolution_x = 900
scene.render.resolution_y = 700
out = os.path.join(HERE, "fur_test.png")
scene.render.filepath = out
bpy.ops.render.render(write_still=True)
print(f"RENDERED_TO:{out}")
