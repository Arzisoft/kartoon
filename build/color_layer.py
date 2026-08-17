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


def shrinkwrap_accent(name, target, location, rotation, scale, material,
                       size=0.3, subdiv_cuts=4, offset=0.012, thickness=0.012, parent=None):
    """A small flat disc that conforms to `target`'s surface via Shrinkwrap.

    This is the general version of the technique that fixed Zayn's blanket: instead of
    guessing raw coordinates against a mesh whose exact dimensions aren't known ahead of
    time (or hand-selecting faces on the fused mesh, which gives ragged/jagged edges — see
    the first cheek-patch attempt, which read as fangs instead of markings up close), place
    a small clean-edged disc roughly in the right spot and let Shrinkwrap conform it to the
    real surface. Works for any small colour accent: cheek patches, blankets, badges.
    """
    bpy.ops.mesh.primitive_plane_add(size=size, location=location, rotation=rotation)
    disc = bpy.context.active_object
    disc.name = name
    disc.scale = scale
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.subdivide(number_cuts=subdiv_cuts)
    bpy.ops.object.mode_set(mode='OBJECT')
    disc.data.materials.append(material)

    shrink = disc.modifiers.new("Shrinkwrap", 'SHRINKWRAP')
    shrink.target = target
    shrink.wrap_method = 'NEAREST_SURFACEPOINT'
    shrink.offset = offset

    solid = disc.modifiers.new("Solidify", 'SOLIDIFY')
    solid.thickness = thickness

    bpy.ops.object.select_all(action='DESELECT')
    disc.select_set(True)
    bpy.context.view_layer.objects.active = disc
    bpy.ops.object.shade_smooth()
    if parent:
        disc.parent = parent
    return disc


def build():
    zayn = base_body.build_zayn_base()
    milo = base_body.build_milo_base()

    tan = matte_material("Zayn_Tan", (0.85, 0.64, 0.40))
    yellow = matte_material("Milo_Yellow", (0.98, 0.82, 0.10))
    turquoise = matte_material("Turquoise", (0.08, 0.52, 0.53))

    zayn.data.materials.append(tan)
    milo.data.materials.append(yellow)

    # Milo's cheek patches — previously face-selected on the fused mesh, which gave jagged/
    # serrated edges that read as fangs up close (see closeup_milo.png). Small shrinkwrapped
    # discs give clean edges instead, same trick as Zayn's blanket below.
    for side in (1, -1):
        shrinkwrap_accent(
            f"Milo_Cheek_{side}", milo,
            location=(0.155 * side, -0.20, 0.995), rotation=(math.radians(90), 0, 0),
            scale=(0.85, 1.0, 1.0), material=turquoise,
            size=0.10, subdiv_cuts=3, offset=0.010, thickness=0.008, parent=milo,
        )

    # Zayn's saddle blanket — draped near the hump, wide enough to read from the front.
    blanket_mat = fabric_material("Zayn_Blanket_Fabric", (0.08, 0.52, 0.53))
    shrinkwrap_accent(
        "Zayn_Blanket", zayn,
        location=(0, 0.05, 1.25), rotation=(math.radians(35), 0, 0),
        scale=(1.0, 0.75, 1.0), material=blanket_mat,
        size=0.85, subdiv_cuts=6, offset=0.018, thickness=0.03, parent=zayn,
    )

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
