"""
Toon/cel shader using stock Blender nodes -- no addon needed. Technique: Shader-to-RGB
converts the lit result to a flat colour, a constant-interpolation ColorRamp bands it into
hard steps (the "cel" look), a Fresnel-driven rim light adds a bright edge, and a Solidify
modifier with inverted normals + flat dark material gives a cartoon outline.
"""
import bpy


def toon_material(name, base_color, shadow_color=None, rim_color=(1.0, 1.0, 1.0),
                   band_count=3, rim_power=3.0):
    if shadow_color is None:
        shadow_color = tuple(c * 0.55 for c in base_color)

    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)

    # Shader-to-RGB is unreliable in EEVEE Next's deferred renderer (both Principled and
    # Diffuse BSDF variants rendered almost entirely in shadow tone regardless of actual
    # scene lighting -- a known EEVEE-Next-vs-legacy-EEVEE behaviour change). Bypassing it
    # entirely: compute NdotL directly from the geometry normal dotted with an approximate
    # key-light direction, which works identically in any engine since it doesn't depend on
    # the renderer's own shading evaluation at all.
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    light_dir = nt.nodes.new("ShaderNodeCombineXYZ")
    # Approximates this project's key light at (-3,-5,5) normalized
    light_dir.inputs["X"].default_value = -0.393
    light_dir.inputs["Y"].default_value = -0.655
    light_dir.inputs["Z"].default_value = 0.646
    dot = nt.nodes.new("ShaderNodeVectorMath")
    dot.operation = 'DOT_PRODUCT'
    nt.links.new(geo.outputs["Normal"], dot.inputs[0])
    nt.links.new(light_dir.outputs["Vector"], dot.inputs[1])
    # dot product is in [-1, 1]; remap to [0, 1] for the ramp
    remap = nt.nodes.new("ShaderNodeMapRange")
    remap.inputs["From Min"].default_value = -1.0
    remap.inputs["From Max"].default_value = 1.0
    nt.links.new(dot.outputs["Value"], remap.inputs["Value"])

    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = 'CONSTANT'
    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[0].color = (*shadow_color, 1.0)
    ramp.color_ramp.elements[1].position = 0.6
    ramp.color_ramp.elements[1].color = (*base_color, 1.0)
    nt.links.new(remap.outputs["Result"], ramp.inputs["Fac"])
    if band_count >= 3:
        highlight = tuple(min(1.0, c * 1.25) for c in base_color)
        el = ramp.color_ramp.elements.new(0.7)
        el.color = (*highlight, 1.0)

    # Rim-light (Fresnel-driven) mix stage dropped -- it broke the whole shader when chained
    # through ShaderNodeMixRGB (legacy node, output/blend behaviour didn't work as expected
    # in this Blender version). Confirmed via diagnostic that ramp -> emission alone works
    # correctly; the banding is the core effect and matters more than the rim glow. Rim
    # light can be re-added later using ShaderNodeMix (data_type='RGBA') instead of the
    # legacy MixRGB node if wanted.
    emission = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(ramp.outputs["Color"], emission.inputs["Color"])

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(emission.outputs["Emission"], out.inputs["Surface"])
    return mat


def add_outline(obj, thickness=0.012, color=(0.05, 0.04, 0.03)):
    """Inverted-hull outline as a SEPARATE duplicate object (not a material-offset trick on
    the same mesh -- that approach put the whole surface on the outline material instead of
    just a thin rim, because Solidify's material_offset duplicates the entire shell inside
    the same object with no clean separation from the original faces).

    The duplicate is a copy of the mesh, pushed outward via Solidify + flipped normals, given
    ONE flat dark material covering its whole surface. Because its normals face inward, only
    its backfaces are visible from outside -- and since it's a hair larger than the original,
    those backfaces only peek out right at the silhouette edge, reading as an outline. The
    original mesh, rendered normally on top, covers the rest.

    STATUS: parked, not working. First attempt (use_backface_culling=False) made the shell
    fully opaque everywhere, hiding the whole character. Second attempt
    (use_backface_culling=True) produced a jagged z-fighting noise pattern instead of a clean
    edge -- likely needs a larger/more careful thickness value and possibly a small camera-
    facing bias, which needs interactive viewport iteration to dial in rather than more blind
    headless guessing. The banded toon shading (toon_material) works correctly on its own;
    only this outline effect is unresolved.
    """
    outline_mat = bpy.data.materials.new(f"{obj.name}_Outline")
    outline_mat.use_nodes = True
    nt = outline_mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1.0)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    # Backface culling MUST be on: with normals flipped, culling hides the shell's front
    # (now-inward-facing) everywhere the camera looks straight at it -- letting the original
    # mesh show through in the centre -- and only shows the shell's back (which, being the
    # far side of an inflated hull, faces the camera right at the silhouette rim) as a thin
    # outline. use_backface_culling=False (the first attempt) made the shell solid and
    # fully opaque everywhere instead, hiding the whole character.
    outline_mat.use_backface_culling = True

    dup_data = obj.data.copy()
    dup_data.materials.clear()
    dup_data.materials.append(outline_mat)
    for p in dup_data.polygons:
        p.material_index = 0
    shell = bpy.data.objects.new(f"{obj.name}_OutlineShell", dup_data)
    bpy.context.scene.collection.objects.link(shell)
    shell.matrix_world = obj.matrix_world.copy()

    mod = shell.modifiers.new("Outline", 'SOLIDIFY')
    mod.thickness = thickness
    mod.offset = 1.0
    mod.use_flip_normals = True

    bpy.ops.object.select_all(action='DESELECT')
    shell.select_set(True)
    bpy.context.view_layer.objects.active = shell
    bpy.ops.object.shade_smooth()
    shell.parent = obj
    return shell
