"""
Layer 2 of the character pipeline: MATERIALS + small accent geometry.

Reads base_body.py (Layer 1 — geometry only, no colour) and adds:
  - body materials (matte, not glossy — matte reads "plush," glossy reads "toy")
  - Zayn's turquoise saddle-blanket (small separate prop mesh, not fused into the body)
  - Milo's cheek-patch colour (face-selected on the existing fused geometry — the cheek
    patches are already modelled in base_body.py, they just have no second material yet)
  - a light procedural bump on the blanket so it reads as woven fabric rather than a flat
    coloured slab (tertiary-layer detail, per bible/character-detail-pass.md — no geometry,
    just a Noise Texture feeding Roughness/Normal)

Deliberately does NOT touch Milo's beak/cere geometry — that's issue #2, Ali's in progress.

Run standalone: blender --background --python color_layer.py
"""
import bpy
import math
import os
import sys
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import base_body  # noqa: E402


def matte_material(name, color, roughness=0.55):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


def fabric_material(name, color, roughness=0.75):
    """Matte base colour with a light noise-driven roughness variation — cheap tertiary
    detail that reads as woven fabric without any extra geometry."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)

    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 40.0
    noise.inputs["Detail"].default_value = 3.0
    ramp = nt.nodes.new("ShaderNodeMapRange")
    ramp.inputs["To Min"].default_value = roughness - 0.15
    ramp.inputs["To Max"].default_value = roughness + 0.10
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Value"])
    nt.links.new(ramp.outputs["Result"], bsdf.inputs["Roughness"])
    return mat


def select_faces_near(obj, center, radius):
    """Return face indices whose centroid falls within `radius` of `center` (world space)."""
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.faces.ensure_lookup_table()
    hits = []
    for f in bm.faces:
        c = f.calc_center_median()
        world_c = obj.matrix_world @ c
        if (world_c - center).length <= radius:
            hits.append(f.index)
    bm.free()
    return hits


def assign_material_to_faces(obj, mat, face_indices):
    if mat.name not in obj.data.materials:
        obj.data.materials.append(mat)
    mat_index = list(obj.data.materials).index(mat)
    for i in face_indices:
        obj.data.polygons[i].material_index = mat_index


def build():
    zayn = base_body.build_zayn_base()
    milo = base_body.build_milo_base()

    tan = matte_material("Zayn_Tan", (0.85, 0.64, 0.40))
    yellow = matte_material("Milo_Yellow", (0.98, 0.82, 0.10))
    turquoise = matte_material("Turquoise", (0.08, 0.52, 0.53))

    zayn.data.materials.append(tan)
    milo.data.materials.append(yellow)

    # Milo's cheek patches already exist as geometry at (0.155*side, -0.155, 0.995), r~0.078
    # (see build_milo_base) — just needs its own material slot instead of body yellow.
    for side in (1, -1):
        center = Vector((0.155 * side, -0.155, 0.995))
        faces = select_faces_near(milo, center, radius=0.11)
        assign_material_to_faces(milo, turquoise, faces)

    # Zayn's saddle blanket: separate prop mesh draped across the back (chest/spine region),
    # not fused into the body — matches base_body.py's own "outfit/props attach on top" plan.
    blanket_mat = fabric_material("Zayn_Blanket_Fabric", (0.08, 0.52, 0.53))
    # Narrow enough to clear the shoulder joints (x=+-0.24 per ZAYN_JOINTS), sitting high on
    # the back near the hump rather than at mid-torso where it collided with the arms.
    # Shrinkwrap-based: a flat, subdivided plane conforms to Zayn's actual body surface via
    # the modifier, so it drapes correctly regardless of exact body proportions — no more
    # guessing raw coordinates against a mesh whose real dimensions I don't have memorized.
    bpy.ops.mesh.primitive_plane_add(size=0.85, location=(0, 0.05, 1.25),
                                      rotation=(math.radians(35), 0, 0))
    blanket = bpy.context.active_object
    blanket.name = "Zayn_Blanket"
    blanket.scale = (1.0, 0.75, 1.0)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.subdivide(number_cuts=6)
    bpy.ops.object.mode_set(mode='OBJECT')
    blanket.data.materials.append(blanket_mat)

    shrink = blanket.modifiers.new("Shrinkwrap", 'SHRINKWRAP')
    shrink.target = zayn
    shrink.wrap_method = 'NEAREST_SURFACEPOINT'
    shrink.offset = 0.018

    solid = blanket.modifiers.new("Solidify", 'SOLIDIFY')
    solid.thickness = 0.03

    bpy.ops.object.select_all(action='DESELECT')
    blanket.select_set(True)
    bpy.context.view_layer.objects.active = blanket
    bpy.ops.object.shade_smooth()
    blanket.parent = zayn

    return zayn, milo


if __name__ == "__main__":
    bpy.ops.wm.read_factory_settings(use_empty=True)
    zayn, milo = build()
    zayn.location = (-0.9, 0, 0)
    milo.location = (0.85, 0, 0)
    base_body._preview_eyes("Zayn_Base", zayn)
    base_body._preview_eyes("Milo_Base", milo)
    base_body._stage(target_z=1.05, cam_dist=6.4, res_x=1600, res_y=900)

    here = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(here, "color_layer.png")
    bpy.context.scene.render.filepath = out
    bpy.ops.render.render(write_still=True)
    print(f"RENDERED_TO:{out}")
