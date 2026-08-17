"""
Procedural build for Zayn (camel) and Milo (budgie) — v2 blockout.
build_scene() does everything up through camera/lighting and returns (zayn_root, milo_root)
so other scripts (e.g. rig_test.py) can import this module and build on top of the meshes.
Run standalone: blender --background --python characters.py
"""
import bpy
import math
import os


def make_material(name, color, roughness=0.55):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


def smooth_round(obj, subdiv=2):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.shade_smooth()
    mod = obj.modifiers.new("Subsurf", 'SUBSURF')
    mod.levels = subdiv
    mod.render_levels = subdiv


def add_sphere(name, radius, location, scale=(1, 1, 1), mat=None, parent=None, subdiv=2):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=location, segments=32, ring_count=16)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = scale
    if mat:
        obj.data.materials.append(mat)
    if parent:
        obj.parent = parent
    smooth_round(obj, subdiv)
    return obj


def add_cube(name, size, location, scale=(1, 1, 1), rotation=(0, 0, 0), mat=None, parent=None, subdiv=1):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location, rotation=rotation)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = scale
    if mat:
        obj.data.materials.append(mat)
    if parent:
        obj.parent = parent
    smooth_round(obj, subdiv)
    return obj


def add_cylinder(name, radius, depth, location, rotation=(0, 0, 0), mat=None, parent=None, subdiv=1):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location, rotation=rotation, vertices=24)
    obj = bpy.context.active_object
    obj.name = name
    if mat:
        obj.data.materials.append(mat)
    if parent:
        obj.parent = parent
    smooth_round(obj, subdiv)
    return obj


def add_cone(name, radius1, depth, location, rotation=(0, 0, 0), mat=None, parent=None, subdiv=1):
    bpy.ops.mesh.primitive_cone_add(radius1=radius1, depth=depth, location=location, rotation=rotation, vertices=24)
    obj = bpy.context.active_object
    obj.name = name
    if mat:
        obj.data.materials.append(mat)
    if parent:
        obj.parent = parent
    smooth_round(obj, subdiv)
    return obj


def build_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene

    mat_tan = make_material("CamelTan", (0.85, 0.64, 0.40))
    mat_turquoise = make_material("Turquoise", (0.08, 0.52, 0.53))
    mat_yellow = make_material("BudgieYellow", (0.98, 0.82, 0.10))
    mat_bluegreen = make_material("WingBlueGreen", (0.14, 0.55, 0.45))
    mat_dark = make_material("EyeDark", (0.02, 0.02, 0.02), roughness=0.2)
    mat_backdrop = make_material("Backdrop", (0.85, 0.90, 0.93), roughness=1.0)

    # ---------- ZAYN (camel) ----------
    zayn_root = bpy.data.objects.new("Zayn", None)
    scene.collection.objects.link(zayn_root)
    zayn_root.location = (-2.0, 0, 0)

    add_sphere("Zayn_Body", 0.85, (0, 0, 0.95), scale=(1.2, 1.0, 0.95), mat=mat_tan, parent=zayn_root)
    add_sphere("Zayn_Hump", 0.46, (-0.15, 0, 1.68), scale=(0.85, 0.85, 0.75), mat=mat_tan, parent=zayn_root)
    zayn_neck = add_sphere("Zayn_Neck", 0.32, (0.95, 0, 1.85), scale=(1.0, 0.85, 2.1), mat=mat_tan, parent=zayn_root)
    zayn_neck.rotation_euler = (0, math.radians(65), 0)
    add_sphere("Zayn_Head", 0.5, (1.55, 0, 2.35), scale=(1.0, 0.92, 0.82), mat=mat_tan, parent=zayn_root)
    add_sphere("Zayn_Muzzle", 0.26, (2.05, 0, 2.18), scale=(1.4, 0.7, 0.6), mat=mat_tan, parent=zayn_root)
    add_sphere("Zayn_Lip", 0.10, (2.28, 0, 2.10), scale=(1.3, 0.9, 0.7), mat=mat_tan, parent=zayn_root, subdiv=1)
    add_sphere("Zayn_Eye_L", 0.095, (1.85, 0.33, 2.40), mat=mat_dark, parent=zayn_root, subdiv=1)
    add_sphere("Zayn_Eye_R", 0.095, (1.85, -0.33, 2.40), mat=mat_dark, parent=zayn_root, subdiv=1)
    add_sphere("Zayn_Ear_L", 0.15, (1.4, 0.44, 2.78), scale=(0.6, 0.55, 1.15), mat=mat_tan, parent=zayn_root)
    add_sphere("Zayn_Ear_R", 0.15, (1.4, -0.44, 2.78), scale=(0.6, 0.55, 1.15), mat=mat_tan, parent=zayn_root)
    for i, (x, y) in enumerate([(0.5, 0.5), (0.5, -0.5), (-0.55, 0.5), (-0.55, -0.5)]):
        add_cylinder(f"Zayn_Leg_{i}", 0.15, 1.05, (x, y, 0.05), mat=mat_tan, parent=zayn_root)
    add_cube("Zayn_Blanket", 1.0, (0.0, 0, 1.5), scale=(0.68, 1.05, 0.28), mat=mat_turquoise, parent=zayn_root)

    # ---------- MILO (budgie) ----------
    milo_root = bpy.data.objects.new("Milo", None)
    scene.collection.objects.link(milo_root)
    milo_root.location = (1.5, 0, 0.62)

    add_sphere("Milo_Body", 0.5, (0, 0, 0), scale=(1.0, 0.95, 1.15), mat=mat_yellow, parent=milo_root)
    add_sphere("Milo_Head", 0.42, (0.02, 0, 0.75), mat=mat_yellow, parent=milo_root)
    add_sphere("Milo_Cere", 0.09, (0.42, 0, 0.80), scale=(0.9, 0.8, 0.7), mat=mat_bluegreen, parent=milo_root, subdiv=1)
    add_cone("Milo_Beak", 0.10, 0.22, (0.48, 0, 0.68), rotation=(0, math.radians(100), 0), mat=mat_dark, parent=milo_root)
    add_sphere("Milo_Beak_Hook", 0.055, (0.56, 0, 0.60), mat=mat_dark, parent=milo_root, subdiv=1)
    add_sphere("Milo_Eye_L", 0.085, (0.34, 0.20, 0.80), mat=mat_dark, parent=milo_root, subdiv=1)
    add_sphere("Milo_Eye_R", 0.085, (0.34, -0.20, 0.80), mat=mat_dark, parent=milo_root, subdiv=1)
    add_sphere("Milo_Cheek_L", 0.11, (0.10, 0.38, 0.62), scale=(0.6, 1.0, 0.9), mat=mat_turquoise, parent=milo_root, subdiv=1)
    add_sphere("Milo_Cheek_R", 0.11, (0.10, -0.38, 0.62), scale=(0.6, 1.0, 0.9), mat=mat_turquoise, parent=milo_root, subdiv=1)
    add_sphere("Milo_Wing_L", 0.26, (-0.15, 0.46, 0.02), scale=(1.15, 0.35, 0.75), mat=mat_bluegreen, parent=milo_root)
    add_sphere("Milo_Wing_R", 0.26, (-0.15, -0.46, 0.02), scale=(1.15, 0.35, 0.75), mat=mat_bluegreen, parent=milo_root)
    add_cone("Milo_Tail", 0.13, 0.55, (-0.62, 0, -0.05), rotation=(0, math.radians(70), 0), mat=mat_bluegreen, parent=milo_root)
    for i, y in enumerate([0.14, -0.14]):
        add_cylinder(f"Milo_Leg_{i}", 0.045, 0.28, (0.02, y, -0.66), mat=mat_dark, parent=milo_root, subdiv=0)

    # ---------- studio backdrop ----------
    bpy.ops.mesh.primitive_plane_add(size=14, location=(0, 0, 0))
    ground = bpy.context.active_object
    ground.name = "Ground"
    ground.data.materials.append(mat_backdrop)

    bpy.ops.mesh.primitive_plane_add(size=14, location=(0, 3.2, 3.2), rotation=(math.radians(90), 0, 0))
    backwall = bpy.context.active_object
    backwall.name = "Backwall"
    backwall.data.materials.append(mat_backdrop)

    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.82, 0.87, 0.90, 1.0)
        bg.inputs[1].default_value = 0.6

    # ---------- camera + three-point lighting ----------
    target = bpy.data.objects.new("Target", None)
    target.location = (-0.3, 0, 1.4)
    scene.collection.objects.link(target)

    bpy.ops.object.camera_add(location=(-0.3, -9.5, 2.1))
    cam = bpy.context.active_object
    cam.data.lens = 35
    track = cam.constraints.new(type='TRACK_TO')
    track.target = target
    track.track_axis = 'TRACK_NEGATIVE_Z'
    track.up_axis = 'UP_Y'
    scene.camera = cam

    bpy.ops.object.light_add(type='AREA', location=(-3, -5, 5))
    bpy.context.active_object.data.energy = 900
    bpy.context.active_object.data.size = 3

    bpy.ops.object.light_add(type='AREA', location=(3, -4, 3))
    bpy.context.active_object.data.energy = 350
    bpy.context.active_object.data.size = 4

    bpy.ops.object.light_add(type='AREA', location=(0, 5, 4))
    bpy.context.active_object.data.energy = 300
    bpy.context.active_object.data.size = 3

    try:
        scene.render.engine = 'BLENDER_EEVEE_NEXT'
    except Exception:
        scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.image_settings.file_format = 'PNG'

    return zayn_root, milo_root


if __name__ == "__main__":
    build_scene()
    scene = bpy.context.scene
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "preview.png")
    scene.render.filepath = out_path
    bpy.ops.render.render(write_still=True)
    print(f"RENDERED_TO:{out_path}")
