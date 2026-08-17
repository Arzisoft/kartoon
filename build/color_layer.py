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


def matte_material(name, color, roughness=0.55, subsurface=0.35):
    """Matte base + a soft subsurface-scattering pass — this is most of what separates
    "Cocomelon-soft plush toy" from "flat-shaded plastic." SSS input names differ across
    Blender versions, so this sets whichever set exists and no-ops otherwise."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    for weight_key in ("Subsurface Weight", "Subsurface"):
        if weight_key in bsdf.inputs:
            bsdf.inputs[weight_key].default_value = subsurface
            break
    if "Subsurface Radius" in bsdf.inputs:
        bsdf.inputs["Subsurface Radius"].default_value = (0.4, 0.2, 0.12)
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


def advanced_material(name, color, roughness=0.3, subsurface=0.0, radius=(0.9, 0.45, 0.2),
                       fabric=False, ao_strength=0.35, rim_strength=0.22, rim_color=None):
    """A flat Principled BSDF only gets you "flat toy plastic" -- this adds the three cheap,
    UV-free procedural passes that separate that from a polished soft-PBR render, learned from
    a cute-character-design tutorial's fabric technique and standard PBR practice (see
    .claude/skills/blender-character-pipeline/references/chibi-proportion-theory.md):

      1. Pointiness-driven AO: creases (low Geometry Pointiness) get mixed toward a darker
         shade of the same colour; convex/flat areas keep the authored colour. Reads as soft
         contact shadowing without baking anything or touching the mesh.
      2. Pointiness-driven roughness: creases read more matte, convex high points read
         slightly glossier -- flat single-roughness materials read uniformly "plasticky."
      3. A soft Fresnel-driven rim light (added on top of the BSDF via Add Shader) --
         separates the silhouette from the backdrop the way a photography rim light does,
         instead of relying on the HDRI alone.

    fabric=True additionally runs a Magic Texture -> Bump -> Normal chain (Object texture
    coordinates, no UV unwrap needed) for a woven-cloth surface, for shirt/shorts/cap-style
    materials -- skip it for skin/hooves/plastic props.
    """
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    out = nt.nodes["Material Output"]
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    for weight_key in ("Subsurface Weight", "Subsurface"):
        if weight_key in bsdf.inputs:
            bsdf.inputs[weight_key].default_value = subsurface
            break
    if subsurface and "Subsurface Radius" in bsdf.inputs:
        bsdf.inputs["Subsurface Radius"].default_value = radius

    geo = nt.nodes.new("ShaderNodeNewGeometry")

    # --- 1. pointiness-driven AO (darken creases only, leave convex/flat areas as authored)
    ao_ramp = nt.nodes.new("ShaderNodeMapRange")
    ao_ramp.inputs["From Min"].default_value = 0.35
    ao_ramp.inputs["From Max"].default_value = 0.55
    nt.links.new(geo.outputs["Pointiness"], ao_ramp.inputs["Value"])
    dark_color = tuple(c * (1.0 - ao_strength) for c in color)
    ao_mix = nt.nodes.new("ShaderNodeMixRGB")
    ao_mix.inputs["Color1"].default_value = (*dark_color, 1.0)   # Fac=0 -> deep crease
    ao_mix.inputs["Color2"].default_value = (*color, 1.0)        # Fac=1 -> convex/flat
    nt.links.new(ao_ramp.outputs["Result"], ao_mix.inputs["Fac"])
    nt.links.new(ao_mix.outputs["Color"], bsdf.inputs["Base Color"])

    # --- 2. pointiness-driven roughness (matte in creases, glossier at high points)
    rough_ramp = nt.nodes.new("ShaderNodeMapRange")
    rough_ramp.inputs["From Min"].default_value = 0.45
    rough_ramp.inputs["From Max"].default_value = 0.65
    rough_ramp.inputs["To Min"].default_value = min(1.0, roughness + 0.18)
    rough_ramp.inputs["To Max"].default_value = max(0.04, roughness - 0.08)
    nt.links.new(geo.outputs["Pointiness"], rough_ramp.inputs["Value"])
    nt.links.new(rough_ramp.outputs["Result"], bsdf.inputs["Roughness"])

    # --- 3. fabric weave bump (fabric=True only) -- Magic Texture, no UVs needed
    if fabric:
        coord = nt.nodes.new("ShaderNodeTexCoord")
        magic = nt.nodes.new("ShaderNodeTexMagic")
        magic.turbulence_depth = 6
        magic.inputs["Scale"].default_value = 60.0
        magic.inputs["Distortion"].default_value = 1.4
        nt.links.new(coord.outputs["Object"], magic.inputs["Vector"])
        bump = nt.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.12
        bump.inputs["Distance"].default_value = 0.01
        nt.links.new(magic.outputs["Fac"], bump.inputs["Height"])
        nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

    # --- 4. soft Fresnel rim light, added on top of the BSDF
    fresnel = nt.nodes.new("ShaderNodeFresnel")
    fresnel.inputs["IOR"].default_value = 1.3
    rim_ramp = nt.nodes.new("ShaderNodeMapRange")
    rim_ramp.inputs["From Min"].default_value = 0.55
    rim_ramp.inputs["From Max"].default_value = 1.0
    rim_ramp.inputs["To Min"].default_value = 0.0
    rim_ramp.inputs["To Max"].default_value = rim_strength
    nt.links.new(fresnel.outputs["Fac"], rim_ramp.inputs["Value"])
    emission = nt.nodes.new("ShaderNodeEmission")
    emission.inputs["Color"].default_value = (*(rim_color or (1.0, 1.0, 1.0)), 1.0)
    nt.links.new(rim_ramp.outputs["Result"], emission.inputs["Strength"])
    add_shader = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(bsdf.outputs["BSDF"], add_shader.inputs[0])
    nt.links.new(emission.outputs["Emission"], add_shader.inputs[1])
    nt.links.new(add_shader.outputs["Shader"], out.inputs["Surface"])

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


def anchored_protrusion(name, target, base_location, tip_offset, base_radius, tip_radius,
                         material, segments=32, subsurf=2, parent=None):
    """A cone whose BASE ring is shrinkwrapped to `target`'s surface (so it's always
    correctly anchored regardless of exact body proportions) while the TIP is left out of
    the shrinkwrap vertex group and keeps its authored protrusion — solving the class of bug
    where small beak/horn/protrusion geometry gets dissolved by fuse()'s voxel remesh when
    it's fused directly into the body. `tip_offset` is a (dx, dy, dz) vector from base_location.
    """
    bpy.ops.mesh.primitive_cone_add(radius1=base_radius, radius2=tip_radius, depth=1.0,
                                     location=base_location, vertices=segments)
    obj = bpy.context.active_object
    obj.name = name

    # Reshape by hand: base ring stays at z=-0.5 (local), tip ring moves to the authored
    # offset instead of straight up +Z, so the cone can point in any direction.
    import bmesh
    from mathutils import Vector
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    base_verts, tip_verts = [], []
    for v in bm.verts:
        (base_verts if v.co.z < 0 else tip_verts).append(v)
    tip_vec = Vector(tip_offset)
    for v in tip_verts:
        radial = Vector((v.co.x, v.co.y, 0))
        v.co = radial + tip_vec
    for v in base_verts:
        v.co.z = 0
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.materials.append(material)

    vg = obj.vertex_groups.new(name="BaseRing")
    base_indices = [v.index for v in obj.data.vertices if v.co.z == 0]
    vg.add(base_indices, 1.0, 'REPLACE')

    shrink = obj.modifiers.new("Shrinkwrap", 'SHRINKWRAP')
    shrink.target = target
    shrink.wrap_method = 'NEAREST_SURFACEPOINT'
    shrink.offset = 0.006
    shrink.vertex_group = "BaseRing"

    if subsurf:
        sub = obj.modifiers.new("Subsurf", 'SUBSURF')
        sub.levels = subsurf
        sub.render_levels = subsurf

    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.shade_smooth()
    if parent:
        obj.parent = parent
    return obj


def extremity_cap(name, parts, material, parent=None):
    """One or more small spheres forming a solid-colour hand/foot cap -- a separate object,
    not fused into the body mesh, so it can have its own dark colour cleanly (the fused-mesh
    face-selection approach gave jagged edges; fusing it in at all meant it inherited the
    body's single material). `parts` is a list of (radius, location, scale) tuples; the
    caller supplies the same radius/location/scale that used to be fused into the body, so
    the extremity keeps its original shape and just moves to its own coloured object.
    """
    made = []
    for i, (radius, location, scale) in enumerate(parts):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=location, segments=20, ring_count=10)
        obj = bpy.context.active_object
        obj.name = f"{name}_{i}" if len(parts) > 1 else name
        obj.scale = scale
        obj.data.materials.append(material)
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.shade_smooth()
        sub = obj.modifiers.new("Subsurf", 'SUBSURF')
        sub.levels = 1
        if parent:
            obj.parent = parent
        made.append(obj)
    return made


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
