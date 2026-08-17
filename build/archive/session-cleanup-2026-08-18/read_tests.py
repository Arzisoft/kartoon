"""
Two objective read tests recommended in bible/character-detail-pass.md, not yet actually run:

1. Thumbnail silhouette test — flat grey silhouette at small size, 3 angles. If species
   can't be told apart at a glance here, primary forms aren't done, no matter how good
   materials/rig look.
2. Close-up face test — tight framing on just the head. This is a dialogue-driven show;
   the face read at "talking head" distance matters more than the full-body shot every
   other render so far has used.

Run standalone: blender --background --python read_tests.py
"""
import bpy
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import base_body  # noqa: E402
import color_layer  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def silhouette_material():
    mat = bpy.data.materials.new("Silhouette")
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    emission = nt.nodes.new("ShaderNodeEmission")
    emission.inputs["Color"].default_value = (0.05, 0.05, 0.05, 1.0)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(emission.outputs["Emission"], out.inputs["Surface"])
    return mat


def render(path, res_x, res_y):
    scene = bpy.context.scene
    scene.render.resolution_x = res_x
    scene.render.resolution_y = res_y
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print(f"RENDERED_TO:{path}")


def thumbnail_test():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    sil = silhouette_material()

    zayn = base_body.build_zayn_base()
    zayn.data.materials.append(sil)
    zayn.location = (-0.9, 0, 0)
    milo = base_body.build_milo_base()
    milo.data.materials.append(sil)
    milo.location = (0.85, 0, 0)

    world = bpy.data.worlds.new("W")
    scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.95, 0.95, 0.95, 1.0)
    world.node_tree.nodes["Background"].inputs[1].default_value = 1.0

    target = bpy.data.objects.new("T", None)
    target.location = (0, 0, 1.0)
    scene.collection.objects.link(target)
    bpy.ops.object.camera_add(location=(0, -6.4, 1.45))
    cam = bpy.context.active_object
    tr = cam.constraints.new(type='TRACK_TO')
    tr.target = target
    tr.track_axis = 'TRACK_NEGATIVE_Z'
    tr.up_axis = 'UP_Y'
    scene.camera = cam

    try:
        scene.render.engine = 'BLENDER_EEVEE_NEXT'
    except Exception:
        scene.render.engine = 'BLENDER_EEVEE'
    scene.render.image_settings.file_format = 'PNG'
    # Deliberately tiny — this is the actual test. If it doesn't read here, it doesn't read
    # in a real thumbnail.
    render(os.path.join(HERE, "thumbnail_test.png"), 240, 135)


def closeup_face_test(which, target_z, cam_dist):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    zayn, milo = color_layer.build()
    body = zayn if which == "zayn" else milo
    mesh_name = "Zayn_Base" if which == "zayn" else "Milo_Base"
    (milo if which == "zayn" else zayn).location = (100, 0, 0)  # push the other one off-frame
    base_body._preview_eyes(mesh_name, body)
    base_body._stage(target_z=target_z, cam_dist=cam_dist, res_x=1200, res_y=1000)
    render(os.path.join(HERE, f"closeup_{which}.png"), 1200, 1000)


if __name__ == "__main__":
    thumbnail_test()
    closeup_face_test("zayn", target_z=2.05, cam_dist=1.6)
    closeup_face_test("milo", target_z=1.15, cam_dist=1.1)
