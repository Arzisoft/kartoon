"""
Cycles + real Subsurface Scattering + HDRI soft-studio lighting -- the Cocomelon-adjacent
direction (soft/glowing/glossy PBR), as opposed to toon_shader.py's flat-cel Dora direction.
Uses a free CC0 HDRI from Poly Haven (build/hdri/) instead of hand-placed area lights, since
Cocomelon's shadow-less soft look comes from a large/soft light source, not point lighting.

Materials go through color_layer.advanced_material() -- pointiness-driven AO/roughness,
optional fabric-weave bump, and a soft Fresnel rim light -- instead of flat single-colour
Principled BSDFs, per chibi-proportion-theory.md's texture notes.

Run standalone: blender --background --python cycles_sss_test.py
"""
import bpy
import math
import os
import sys
from mathutils import Vector, Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import base_body  # noqa: E402
import color_layer  # noqa: E402
import procedural_hand  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RETOPO = os.path.join(HERE, "retopo")
HDRI = os.path.join(HERE, "hdri", "studio_small_08_1k.hdr")


def add_wrinkle_displace(objs, strength=0.02, noise_scale=0.35, subsurf_levels=2):
    """Same technique as the skin/finger organic-noise displacement (see the top of this file
    and procedural_hand.py) applied to clothing -- the shirt/shorts extremity_cap spheres are
    otherwise perfectly smooth primitives too, same "too geometric" problem as the bare skin
    had. Coarser noise_scale than skin (0.35 vs skin's 0.05) since cloth folds/wrinkles are a
    larger-scale feature than skin micro-texture, not a fine grain.
    """
    for obj in objs:
        sub = obj.modifiers.get("Subsurf")
        if sub is None:
            sub = obj.modifiers.new("Subsurf", 'SUBSURF')
        sub.levels = subsurf_levels
        tex = bpy.data.textures.new(f"{obj.name}_Wrinkle", type='CLOUDS')
        tex.noise_scale = noise_scale
        disp = obj.modifiers.new("Wrinkle", 'DISPLACE')
        disp.texture = tex
        disp.strength = strength


def add_fur_patch(obj, z_min, z_max, color, density=9000.0, distance_min=0.006,
                   strand_radius=0.0015, strand_length=0.012, roughness=0.75):
    """Procedural fur via Geometry Nodes -- validated standalone in fur_test.py first. Scatters
    thin cone "strand" instances (Distribute Points on Faces, POISSON) aligned to the face
    normal (Align Rotation to Vector) with random scale/tilt jitter, restricted to a world-Z
    height band via a Position+Compare selection so it only grows on a specific exposed patch
    of skin rather than the whole body (most of the body is already covered by the shirt/
    shorts/collar, which would just swallow fur the same way it swallowed the first fur-tuft
    attempt). This is Blender's built-in scriptable hair system -- no interactive combing
    needed, since fur direction here legitimately comes from the surface normal (a short,
    coarse coat), not from hand-groomed flow.
    """
    bpy.ops.mesh.primitive_cone_add(radius1=strand_radius, radius2=strand_radius * 0.07,
                                     depth=strand_length, location=(50, 50, 50))
    strand = bpy.context.active_object
    strand.name = f"{obj.name}_FurStrand"
    fur_mat = bpy.data.materials.new(f"{obj.name}_FurColor")
    fur_mat.use_nodes = True
    fbsdf = fur_mat.node_tree.nodes["Principled BSDF"]
    fbsdf.inputs["Base Color"].default_value = (*color, 1.0)
    fbsdf.inputs["Roughness"].default_value = roughness
    strand.data.materials.append(fur_mat)
    bpy.context.scene.collection.objects.unlink(strand)  # template only, not itself visible

    ng = bpy.data.node_groups.new(f"{obj.name}_FurGen", "GeometryNodeTree")
    ng.interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    nt = ng
    gin = nt.nodes.new("NodeGroupInput")
    gout = nt.nodes.new("NodeGroupOutput")

    # Position-based selection -- Distribute Points on Faces evaluates the "Selection" input
    # as a boolean field on the face domain, so a plain world-space Z-band test picked at the
    # group-input geometry (which for a modifier is the object's own LOCAL space, pre-transform)
    # is enough to isolate one patch without needing an authored vertex group.
    pos = nt.nodes.new("GeometryNodeInputPosition")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(pos.outputs["Position"], sep.inputs["Vector"])
    gt = nt.nodes.new("FunctionNodeCompare")
    gt.data_type = 'FLOAT'
    gt.operation = 'GREATER_THAN'
    gt.inputs["B"].default_value = z_min
    nt.links.new(sep.outputs["Z"], gt.inputs["A"])
    lt = nt.nodes.new("FunctionNodeCompare")
    lt.data_type = 'FLOAT'
    lt.operation = 'LESS_THAN'
    lt.inputs["B"].default_value = z_max
    nt.links.new(sep.outputs["Z"], lt.inputs["A"])
    band = nt.nodes.new("FunctionNodeBooleanMath")
    band.operation = 'AND'
    nt.links.new(gt.outputs["Result"], band.inputs[0])
    nt.links.new(lt.outputs["Result"], band.inputs[1])

    distribute = nt.nodes.new("GeometryNodeDistributePointsOnFaces")
    distribute.distribute_method = 'POISSON'
    distribute.inputs["Distance Min"].default_value = distance_min
    distribute.inputs["Density Max"].default_value = density
    nt.links.new(gin.outputs["Geometry"], distribute.inputs["Mesh"])
    nt.links.new(band.outputs["Boolean"], distribute.inputs["Selection"])

    rand_scale = nt.nodes.new("FunctionNodeRandomValue")
    rand_scale.data_type = 'FLOAT'
    rand_scale.inputs["Min"].default_value = 0.7
    rand_scale.inputs["Max"].default_value = 1.3

    rand_tilt = nt.nodes.new("FunctionNodeRandomValue")
    rand_tilt.data_type = 'FLOAT_VECTOR'
    rand_tilt.inputs["Min"].default_value = (-0.3, -0.3, 0.0)
    rand_tilt.inputs["Max"].default_value = (0.3, 0.3, 0.0)

    align = nt.nodes.new("FunctionNodeAlignRotationToVector")
    align.axis = 'Z'
    nt.links.new(distribute.outputs["Normal"], align.inputs["Vector"])

    combine_rot = nt.nodes.new("ShaderNodeVectorMath")
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

    # Join the fur strands back onto the original passthrough geometry -- without this the
    # modifier's output would be ONLY the fur strands, deleting the body mesh underneath.
    join = nt.nodes.new("GeometryNodeJoinGeometry")
    nt.links.new(gin.outputs["Geometry"], join.inputs["Geometry"])
    nt.links.new(realize.outputs["Geometry"], join.inputs["Geometry"])
    nt.links.new(join.outputs["Geometry"], gout.inputs["Geometry"])

    mod = obj.modifiers.new("Fur", 'NODES')
    mod.node_group = ng


bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

bpy.ops.wm.obj_import(filepath=os.path.join(RETOPO, "kamel_retopo.obj"), forward_axis='Y', up_axis='Z')
kamel = bpy.context.selected_objects[0]
kamel.name = "Kamel_SSS"
kamel.modifiers.new("Subsurf", 'SUBSURF').levels = 2  # higher -- Cycles SSS reads better on denser geo

# Subtle procedural surface noise -- the single biggest reason the character has read as
# "generated from primitives" rather than "designed": smooth shading + Subsurf make it LOOK
# soft, but there's zero actual surface variation underneath. A real Blender workflow guide
# is blunt about this exact trap: "avoid fake smoothing effects... they give a wrong
# impression of your geometry, instead build actual detail into your mesh." A Displace
# modifier driven by a noise texture is the scriptable stand-in for that hand-sculpted detail
# -- applied AFTER Subsurf so it has enough geometry resolution to displace against, at a very
# low strength so it reads as organic skin texture, not a visibly bumpy/distorted surface.
skin_noise_tex = bpy.data.textures.new("KamelSkinNoise", type='CLOUDS')
skin_noise_tex.noise_scale = 0.05  # finer-grained than the first attempt (was 0.12)
skin_disp = kamel.modifiers.new("SkinDetail", 'DISPLACE')
skin_disp.texture = skin_noise_tex
skin_disp.strength = 0.018  # first attempt (0.006) was invisible at render distance -- 3x'd

skin_mat = color_layer.advanced_material(
    # Was a fairly saturated cartoon orange (0.95, 0.58, 0.18) -- the reference photos read as
    # a warmer, more muted sandy tan/camel-brown, less "orange soda." Shifted toward that.
    "Kamel_SSS_Skin", (0.85, 0.56, 0.30), roughness=0.28, subsurface=0.8,
    radius=(0.9, 0.45, 0.2), ao_strength=0.30, rim_strength=0.28, rim_color=(1.0, 0.85, 0.65),
    coat_weight=0.6, coat_roughness=0.08,
)
kamel.data.materials.append(skin_mat)
bpy.ops.object.select_all(action='DESELECT'); kamel.select_set(True)
bpy.context.view_layer.objects.active = kamel
bpy.ops.object.shade_smooth()

dark_brown = color_layer.advanced_material(
    "Kamel_SSS_Dark", (0.26, 0.15, 0.07), roughness=0.32, ao_strength=0.25, rim_strength=0.15,
)

# Feet: procedural continuous-tube toes (build/procedural_hand.py's build_foot(), reusing the
# same tapered-tube-with-curl generator the hands use) instead of the old overlapping-sphere
# split-hoof -- one smooth padded toe each instead of two blobs stacked next to a pad sphere.
for side in (1, -1):
    # Foot must overlap the ankle joint (0.180, 0.00, 0.16) -- it was centred 0.09 below
    # the joint before, leaving a visible gap between the leg and the foot blob.
    foot_center = (0.180 * side, -0.015, 0.115)
    # Wrapped in an empty (same pattern as the hand's hand_root below) so the foot can be
    # bone-parented to the new Rigify leg rig's DEF-foot bone instead of being a rigid child
    # of kamel's own object transform -- previously feet had no leg bones to follow at all.
    foot_root = bpy.data.objects.new(f"Kamel_FootRoot_{side}", None)
    scene.collection.objects.link(foot_root)
    foot_root.parent = kamel
    procedural_hand.build_foot(f"Kamel_Foot_{side}", foot_center, side=side,
                                material=dark_brown, parent=foot_root)

# Hands: procedural continuous-tube fingers (build/procedural_hand.py) instead of the
# overlapping-sphere-stack extremity_cap hands -- one smooth tapered digit per finger, built
# in its own local "fingers point along -Y" space then placed at the wrist and rotated 90 deg
# about X so -Y maps to -Z (fingers hang downward, matching the arm's resting angle).
for side in (1, -1):
    hand_root = bpy.data.objects.new(f"Kamel_HandRoot_{side}", None)
    scene.collection.objects.link(hand_root)
    hand_root.parent = kamel
    # Wrist joint is (0.420, -0.06, 0.71) after the arm was shortened along with the legs --
    # offset -0.045 below the joint so the palm overlaps the forearm end, same as before.
    hand_root.location = (0.420 * side, -0.060, 0.665)
    hand_root.rotation_euler = (math.radians(90), 0, 0)
    procedural_hand.build_hand(f"Kamel_Hand_{side}", (0, 0, 0), side=side,
                                material=dark_brown, parent=hand_root)

# Water-canteen cap -- Kamel's a camel, he stores water, so the cap references a canteen: a
# rounded dome + a small spout/cap nub on top, like a water bottle lid.
cap_mat = color_layer.advanced_material(
    "Kamel_SSS_Cap", (0.15, 0.55, 0.75), roughness=0.3, fabric=True,
    ao_strength=0.3, rim_strength=0.2, coat_weight=0.4, coat_roughness=0.12,
)
# Baseball cap: rounded dome + a flat forward brim, plus a couple of bright drinking straws
# poking out the top -- the "he stores water" joke read as "juice box straws" instead of a
# plain canteen spout, which didn't land visually.
color_layer.extremity_cap(
    "Kamel_Cap", [(0.155, (0, -0.02, 2.07), (1.05, 1.05, 0.55))], cap_mat, parent=kamel,
)
# brim: flattened, pushed forward and down off the front of the dome
color_layer.extremity_cap(
    "Kamel_Cap_Brim", [(0.11, (0, -0.20, 1.98), (1.3, 0.75, 0.16))], cap_mat, parent=kamel,
)
# button on top, like a real baseball cap
color_layer.extremity_cap(
    "Kamel_Cap_Button", [(0.025, (0, -0.02, 2.20), (1.0, 1.0, 0.7))], cap_mat, parent=kamel,
)
straw_colors = [(0.85, 0.15, 0.15), (0.15, 0.55, 0.85)]
for i, side in enumerate((1, -1)):
    straw_mat = color_layer.advanced_material(
        f"Kamel_Straw_{i}", straw_colors[i], roughness=0.3, ao_strength=0.2, rim_strength=0.15,
    )
    p1 = Vector((0.05 * side, -0.05, 2.11))
    p2 = Vector((0.13 * side, -0.15, 2.40))
    mid = (p1 + p2) / 2
    length = (p2 - p1).length
    bpy.ops.mesh.primitive_cylinder_add(radius=0.02, depth=length, location=mid, vertices=16)
    straw = bpy.context.active_object
    straw.name = f"Kamel_Straw_{i}"
    # orient the cylinder's local Z axis along p1->p2
    straw.rotation_mode = 'QUATERNION'
    straw.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(p2 - p1)
    straw.data.materials.append(straw_mat)
    bpy.ops.object.select_all(action='DESELECT')
    straw.select_set(True)
    bpy.context.view_layer.objects.active = straw
    bpy.ops.object.shade_smooth()
    straw.parent = kamel

# T-shirt + shorts -- original playful outfit, bright contrasting colours, simple circle
# "badge" graphic on the chest for a funny touch. Same shrinkwrap-drape technique as the
# earlier blanket (proven to drape cleanly over the torso from multiple angles).
shirt_mat = color_layer.advanced_material(
    "Kamel_SSS_Shirt", (0.85, 0.18, 0.15), roughness=0.55, fabric=True,
    ao_strength=0.35, rim_strength=0.18,
)
# Real t-shirt: torso coverage from belly up through the chest/shoulder line, plus cap-sleeve
# bumps at the shoulders. Sized OVERSIZED (per chibi-proportion-theory.md rule #5: baggy
# clothing relative to the body amplifies the toy/toddler read) -- bigger radius, taller so it
# hangs lower past the hip, and puffier sleeves that visibly balloon past the arm underneath
# instead of hugging it.
# Y (front-back depth) pulled in from 1.05 to 0.80 -- it was nearly as deep as it was wide,
# so the torso read as a circular/round cross-section and looked just as "fat" from the side
# as from the front. A real torso (and the shirt draped over it) is flatter front-to-back than
# it is wide side-to-side. X bumped slightly to keep the front-view width read unchanged.
shirt_parts = []
shirt_parts += color_layer.extremity_cap(
    "Kamel_Shirt", [(0.34, (0, -0.01, 1.09), (1.05, 0.80, 1.62))], shirt_mat, parent=kamel,
)
for side in (1, -1):
    shirt_parts += color_layer.extremity_cap(
        f"Kamel_Sleeve_{side}", [(0.125, (0.235 * side, 0.02, 1.25), (1.0, 1.0, 0.9))],
        shirt_mat, parent=kamel,
    )
# Turtleneck collar: a separate stretched piece rising from the shirt's top, angled back to
# cover the hump (which sits behind/above the shoulder line) instead of leaving it bare
# above the collar.
shirt_parts += color_layer.extremity_cap(
    "Kamel_Shirt_Collar", [(0.22, (0, 0.08, 1.58), (1.1, 0.85, 0.80))], shirt_mat, parent=kamel,
)
# The collar and torso spheres leave a saddle dip between them right where the hump sits,
# letting bare skin show through. Overlay shirt-coloured spheres directly on the hump's own
# two ball centres (from base_body.py's hump definition), sized larger than the hump itself,
# so the fabric guarantees full coverage regardless of gaps between the other shirt pieces.
shirt_parts += color_layer.extremity_cap(
    "Kamel_Shirt_HumpCover",
    [(0.245, (0, 0.130, 1.41), (1.05, 1.05, 1.15)),
     (0.180, (0, 0.110, 1.55), (0.95, 0.95, 1.05))],
    shirt_mat, parent=kamel,
)
# Wrinkle/fold displacement -- same "too geometric" fix as the skin got, cloth-scale noise.
add_wrinkle_displace(shirt_parts, strength=0.022, noise_scale=0.4)
# Badge: a clean flat circle (was an odd stretched blob before), centred on the chest.
badge_mat = color_layer.advanced_material(
    "Kamel_SSS_Badge", (1.0, 0.95, 0.9), roughness=0.4, ao_strength=0.2, rim_strength=0.2,
)
color_layer.extremity_cap(
    # Was squashed along Z (flat top/bottom), so front camera saw its thin EDGE -- a flat
    # oval instead of a round badge. A coin-shaped badge needs its flat faces pointing
    # front/back (squash along Y), so the front view sees the full round face.
    "Kamel_Badge", [(0.065, (0, -0.27, 1.11), (1.0, 0.28, 1.0))], badge_mat, parent=kamel,
)

shorts_mat = color_layer.advanced_material(
    "Kamel_SSS_Shorts", (0.95, 0.75, 0.10), roughness=0.55, fabric=True,
    ao_strength=0.35, rim_strength=0.18,
)
shorts_parts = color_layer.extremity_cap(
    # Oversized/baggy cut, same theory as the shirt above -- wider than the hips and dropped
    # slightly lower for a loose cargo-short silhouette instead of a snug fit. Y depth pulled
    # in same as the shirt, same reason -- was reading round/fat from the side.
    "Kamel_Shorts", [(0.28, (0, 0.0, 0.78), (1.10, 0.80, 1.05))], shorts_mat, parent=kamel,
)
add_wrinkle_displace(shorts_parts, strength=0.022, noise_scale=0.4)

# Mouth: dropped the dark mouth-line shape entirely -- it read as a floating brown
# mustache/lip-flap disconnected from the teeth rather than a mouth line, per direct feedback.
# The tooth row alone reads as the mouth now, same as it does in the reference photo's smile.
# Nostrils added for a clearer nose read, since the nose was previously just an unmarked bump.
# Teeth: reference photo shows a small ROW of teeth, not 2 big rounded ones -- 4 smaller,
# squarer teeth spread across the mouth opening instead.
teeth_mat = color_layer.advanced_material(
    "Kamel_Teeth", (0.96, 0.94, 0.88), roughness=0.25, ao_strength=0.1, rim_strength=0.05,
)
for i, tx in enumerate((-0.048, -0.016, 0.016, 0.048)):
    color_layer.extremity_cap(
        f"Kamel_Tooth_{i}",
        [(0.022, (tx, -0.510, 1.685), (0.85, 0.65, 1.05))],
        teeth_mat, parent=kamel,
    )
nostril_mat = color_layer.advanced_material(
    "Kamel_Final_Nostril", (0.30, 0.13, 0.10), roughness=0.4, ao_strength=0.15, rim_strength=0.08,
)
for side in (1, -1):
    color_layer.extremity_cap(
        f"Kamel_Nostril_{side}",
        [(0.018, (0.035 * side, -0.505, 1.765), (0.7, 1.3, 0.9))],
        nostril_mat, parent=kamel,
    )

eyes = base_body._preview_eyes("Kamel_Base", kamel)
for e in eyes:
    if "Sclera" in e.name:
        e.data.materials[0].node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.1

# Catchlight: reference photos all have a bright glossy highlight dot on the eye -- relying on
# a physically-lit specular highlight means it only shows up if a light happens to be at the
# right angle for a given camera position (it wasn't visible from most of our turnaround
# angles). A small always-bright Emission dot on the pupil surface guarantees the highlight
# reads from every angle, the same way traditional cartoon eyes are actually painted.
catchlight_mat = bpy.data.materials.new("Kamel_Catchlight")
catchlight_mat.use_nodes = True
cl_nt = catchlight_mat.node_tree
for n in list(cl_nt.nodes):
    cl_nt.nodes.remove(n)
cl_em = cl_nt.nodes.new("ShaderNodeEmission")
cl_em.inputs["Color"].default_value = (1.0, 1.0, 1.0, 1.0)
cl_em.inputs["Strength"].default_value = 1.5
cl_out = cl_nt.nodes.new("ShaderNodeOutputMaterial")
cl_nt.links.new(cl_em.outputs["Emission"], cl_out.inputs["Surface"])
pupil_r, (px, py, pz) = base_body.PREVIEW_EYES["Kamel_Base"][2:4]
for side in (1, -1):
    color_layer.extremity_cap(
        f"Kamel_Catchlight_{side}",
        [(pupil_r * 0.28, (px * side + 0.02 * side, py - 0.018, pz + 0.022), (1.0, 1.0, 1.0))],
        catchlight_mat, parent=kamel,
    )

# FIXED: the previous fur pass was invisible -- the head tuft sat entirely inside the cap
# dome's z-range (1.985-2.155) and the hump tuft sat entirely inside the shirt collar's
# z-range (1.404-1.756), so both were fully swallowed by other geometry with nothing showing.
# Dropped the head tuft (nowhere for it to poke out from under a dome cap) and moved the hump
# tuft to the tail tip instead (genuinely uncovered by any clothing). Ear tufts enlarged and
# pushed further up+out so they clearly poke out past the cap's dome silhouette at that offset,
# not just past the ear.
tuft_mat = color_layer.advanced_material(
    "Kamel_Tuft", (0.55, 0.32, 0.14), roughness=0.45, ao_strength=0.2, rim_strength=0.1,
)
for side in (1, -1):
    color_layer.extremity_cap(
        f"Kamel_EarTuft_{side}",
        [(0.040, (0.145 * side, 0.01, 2.14), (0.7, 0.8, 1.0)),
         (0.024, (0.150 * side, -0.01, 2.20), (0.55, 0.65, 1.3))],
        tuft_mat, parent=kamel,
    )
# Tail-tip tuft: darker/textured overlay on the body's own tail-tip ball (base_body.py, at
# local (0, 0.255, 0.625) r=0.062) so it reads as a distinct fuzzy tuft instead of a plain
# skin-coloured lump -- matches the tufted tail visible in every reference photo.
color_layer.extremity_cap(
    "Kamel_TailTuft",
    [(0.058, (0, 0.265, 0.60), (0.8, 0.85, 1.3)),
     (0.036, (0, 0.275, 0.51), (0.6, 0.65, 1.4))],
    tuft_mat, parent=kamel,
)

# Real fur patch on the exposed upper neck -- the neck capsule (base_body.py) runs from
# neck_base z=1.35 up to head_base z=1.83, but the shirt collar covers up to z~1.756, and the
# glasses/cap sit at z~1.9+, so the only genuinely bare skin band left is roughly z=1.76-1.83,
# a narrow ring right where the neck meets the head -- exactly where real camels show a
# visible fur collar/mane starting. Kept to this one band rather than the whole body both for
# render cost and because everywhere else is already covered by clothing (fur under the shirt
# would just be invisible again, the same bug that hid the first tuft attempt).
add_fur_patch(kamel, z_min=1.76, z_max=1.83, color=(0.55, 0.32, 0.14))

# Nerdy glasses, black frames -- two lenses centred on the eyes (sclera at (0.086, -0.248,
# 1.926), sclera radius 0.080). First attempt used lens radius 0.078 -- barely smaller than
# the eye itself, so in the front camera's 2D projection the dark lens was completely hidden
# behind/inside the white sclera's silhouette with no visible rim at all. A frame has to be
# CLEARLY bigger than the eye it surrounds, not matched to it -- radius 0.115 now leaves a
# visible black ring around the white eyeball on all sides. At that size the two lenses'
# inner edges already overlap across the nose bridge, so no separate bridge piece is needed.
glasses_mat = color_layer.advanced_material(
    "Kamel_SSS_Glasses", (0.05, 0.05, 0.06), roughness=0.35, ao_strength=0.15, rim_strength=0.12,
    coat_weight=0.7, coat_roughness=0.05,
)
for side in (1, -1):
    color_layer.extremity_cap(
        f"Kamel_Glasses_Lens_{side}",
        [(0.115, (0.086 * side, -0.248, 1.926), (1.0, 0.30, 1.0))],
        glasses_mat, parent=kamel,
    )
    arm_p1 = Vector((0.205 * side, -0.220, 1.926))
    arm_p2 = Vector((0.190 * side, -0.020, 1.918))
    mid = (arm_p1 + arm_p2) / 2
    length = (arm_p2 - arm_p1).length
    bpy.ops.mesh.primitive_cylinder_add(radius=0.012, depth=length, location=mid, vertices=10)
    temple = bpy.context.active_object
    temple.name = f"Kamel_Glasses_Temple_{side}"
    temple.rotation_mode = 'QUATERNION'
    temple.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(arm_p2 - arm_p1)
    temple.data.materials.append(glasses_mat)
    bpy.ops.object.select_all(action='DESELECT')
    temple.select_set(True)
    bpy.context.view_layer.objects.active = temple
    bpy.ops.object.shade_smooth()
    temple.parent = kamel

# ---------------------------------------------------------------- Rigify armature + hands-on-hips pose
# Replaced the old hand-built 6-bone arm-only armature with a real Rigify-generated rig (full
# spine, arms AND legs -- the old rig never had leg bones at all, feet were static) built from
# Blender's built-in "basic human" metarig template repositioned to Kamel's own joint
# coordinates (base_body.KAMEL_JOINTS). This is the same auto-rig generator professional
# Blender animators use (proper IK/FK deform hierarchy) instead of a hand-typed rotation-only
# rig. Bone positions/pose values were derived via a diagnostic script (rigify_diag.py, not
# part of this pipeline) that swept candidate rotations and printed resulting world-space bone
# tips -- Rigify's generated FK bones have different local axis/roll conventions than the old
# hand-built bones (X here is the shoulder's out/in swing, not the elbow bend), so the
# previously-tuned rotation numbers did NOT carry over and had to be re-derived from scratch.
J = base_body.KAMEL_JOINTS


def jp(name, side=1):
    x, y, z = J[name]
    return (x * side, y, z)


def lerp3(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


bpy.ops.preferences.addon_enable(module='rigify')
bpy.ops.object.armature_basic_human_metarig_add()
metarig = bpy.context.active_object
metarig.name = "Kamel_Metarig"
bpy.ops.object.mode_set(mode='EDIT')
eb = metarig.data.edit_bones
for n in ("breast.L", "breast.R"):  # no equivalent feature on Kamel
    eb.remove(eb[n])

eb["spine"].head = jp("pelvis"); eb["spine"].tail = jp("spine")
eb["spine.001"].head = jp("spine"); eb["spine.001"].tail = lerp3(jp("spine"), jp("chest"), 0.6)
eb["spine.002"].head = eb["spine.001"].tail; eb["spine.002"].tail = jp("chest")
eb["spine.003"].head = jp("chest"); eb["spine.003"].tail = jp("neck_base")
eb["spine.004"].head = jp("neck_base"); eb["spine.004"].tail = lerp3(jp("neck_base"), jp("head_base"), 0.55)
eb["spine.005"].head = eb["spine.004"].tail; eb["spine.005"].tail = jp("head_base")
# spine.006 (becomes the "head" control) runs FORWARD along the snout (head_base -> head_top)
# rather than up through a skull -- matches KAMEL_JOINTS' own documented reasoning for a
# long-snouted animal's head bone (a vertical head bone leaves the snout closer to the neck
# bone than the head bone, so automatic weights mangle the muzzle when the head turns).
eb["spine.006"].head = jp("head_base"); eb["spine.006"].tail = jp("head_top")

for side in (1, -1):
    tag = "L" if side > 0 else "R"
    eb[f"pelvis.{tag}"].head = jp("pelvis")
    eb[f"pelvis.{tag}"].tail = (jp("hip", side)[0], jp("pelvis")[1], jp("pelvis")[2] + 0.05)
    eb[f"shoulder.{tag}"].head = (0.02 * side, jp("neck_base")[1], jp("chest")[2] + 0.02)
    eb[f"shoulder.{tag}"].tail = jp("shoulder", side)
    eb[f"upper_arm.{tag}"].head = jp("shoulder", side); eb[f"upper_arm.{tag}"].tail = jp("elbow", side)
    eb[f"forearm.{tag}"].head = jp("elbow", side); eb[f"forearm.{tag}"].tail = jp("wrist", side)
    eb[f"hand.{tag}"].head = jp("wrist", side); eb[f"hand.{tag}"].tail = jp("hand_end", side)
    eb[f"thigh.{tag}"].head = jp("hip", side); eb[f"thigh.{tag}"].tail = jp("knee", side)
    eb[f"shin.{tag}"].head = jp("knee", side); eb[f"shin.{tag}"].tail = jp("ankle", side)
    eb[f"foot.{tag}"].head = jp("ankle", side); eb[f"foot.{tag}"].tail = jp("toe", side)
    tx, ty, tz = jp("toe", side)
    eb[f"toe.{tag}"].head = jp("toe", side); eb[f"toe.{tag}"].tail = (tx, ty - 0.08, tz)
    ax, ay, az = jp("ankle", side)
    eb[f"heel.02.{tag}"].head = (ax - 0.05 * side, ay + 0.06, 0.02)
    eb[f"heel.02.{tag}"].tail = (ax + 0.05 * side, ay + 0.06, 0.02)

bpy.ops.object.mode_set(mode='OBJECT')
bpy.context.view_layer.objects.active = metarig
bpy.ops.pose.rigify_generate()
rig = bpy.context.active_object
rig.name = "Kamel_Rig"
metarig.hide_set(True)  # keep it (Rigify keeps a live link to it) but out of the render

bpy.ops.object.select_all(action='DESELECT')
kamel.select_set(True)
rig.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.parent_set(type='ARMATURE_AUTO')


# Rigid accessories (hands, sleeves, feet -- not part of kamel's own vertex-weighted mesh)
# bone-parent directly to the rig's DEF- deform bones, same capture-matrix_world / BONE-parent
# pattern as the old armature used, just pointed at Rigify's bone names. Feet are newly
# bone-parented here too (via the Kamel_FootRoot_{side} wrapper empty added above) -- the old
# rig had no leg bones at all, so feet were rigid children of kamel with nothing to follow.
for side in (1, -1):
    tag = "L" if side > 0 else "R"
    hand_root_obj = bpy.data.objects[f"Kamel_HandRoot_{side}"]
    sleeve_obj = bpy.data.objects[f"Kamel_Sleeve_{side}"]
    foot_root_obj = bpy.data.objects[f"Kamel_FootRoot_{side}"]
    for obj, bone_name in (
        (hand_root_obj, f"DEF-hand.{tag}"),
        (sleeve_obj, f"DEF-upper_arm.{tag}"),
        (foot_root_obj, f"DEF-foot.{tag}"),
    ):
        desired_world = obj.matrix_world.copy()
        obj.parent = rig
        obj.parent_type = 'BONE'
        obj.parent_bone = bone_name
        obj.matrix_parent_inverse = Matrix.Identity(4)
        obj.matrix_world = desired_world

bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='POSE')
# Posed via the IK hand target, not the FK bones. A standalone diagnostic (since deleted) found
# the FK -> DEF chain is gated by driver-controlled constraint influence/mute values that, in
# this Blender/Rigify version, don't refresh from a plain headless property write (confirmed:
# forcing IK_FK=0 and manually re-tagging the depsgraph still left the mesh following the IK
# chain) -- but the IK chain itself is unconditionally live, so directly placing the hand_ik
# control at the target world position and letting the solver reach it is the reliable path
# (confirmed: DEF-forearm's tail lands exactly on the given target). Elbow bend direction isn't
# independently steerable here (pole_target/pole_angle had no measurable effect either -- same
# driver-refresh issue), so the elbow lands wherever the solver's default bend plane puts it.
# Target chosen by render-and-look, not just coordinates: a bigger swing (closer to the old
# hand-built rig's numeric hip target) put visible stress on the bare underarm skin -- a flat
# stretched "web" between the stationary torso weights and the swung-out arm weights, since
# Blender's automatic weights don't handle a big pose delta on this mesh's shoulder topology
# cleanly (tried smoothing AND cleaning the vertex groups -- both made the stretch worse, not
# better). This smaller, closer-to-rest target keeps the hands-on-hips read without provoking
# that stretch; a real fix (manual weight painting or reworking the shoulder topology) is
# GUI/interactive work, flagged as a follow-up rather than solved here.
for side in (1, -1):
    tag = "L" if side > 0 else "R"
    hand_ik = rig.pose.bones[f"hand_ik.{tag}"]
    m = hand_ik.matrix.copy()
    m.translation = Vector((0.36 * side, -0.06, 0.80))
    hand_ik.matrix = m
bpy.context.view_layer.update()
bpy.ops.object.mode_set(mode='OBJECT')

# Overall size down ~15% -- was reading too large/bulky
kamel.scale = (0.85, 0.85, 0.85)

# ---------------------------------------------------------------- HDRI world lighting
world = bpy.data.worlds.new("HDRI_World")
scene.world = world
world.use_nodes = True
wnt = world.node_tree
for n in list(wnt.nodes):
    wnt.nodes.remove(n)
env_tex = wnt.nodes.new("ShaderNodeTexEnvironment")
env_tex.image = bpy.data.images.load(HDRI)
bg_light = wnt.nodes.new("ShaderNodeBackground")
bg_light.inputs["Strength"].default_value = 1.2
wnt.links.new(env_tex.outputs["Color"], bg_light.inputs["Color"])

# The HDRI drove BOTH lighting and the literal camera-visible background, which reads fine
# from the front but shows an ugly blurry softbox panel / dark doorway from side/back angles.
# Split them: Light Path "Is Camera Ray" selects a flat neutral backdrop for rays that hit the
# world directly from the camera, while the HDRI still lights the character via bounce/diffuse
# rays (Is Camera Ray == 0 for those).
backdrop = wnt.nodes.new("ShaderNodeBackground")
backdrop.inputs["Color"].default_value = (0.82, 0.83, 0.85, 1.0)
backdrop.inputs["Strength"].default_value = 1.0
light_path = wnt.nodes.new("ShaderNodeLightPath")
mix = wnt.nodes.new("ShaderNodeMixShader")
wnt.links.new(light_path.outputs["Is Camera Ray"], mix.inputs["Fac"])
wnt.links.new(bg_light.outputs["Background"], mix.inputs[1])
wnt.links.new(backdrop.outputs["Background"], mix.inputs[2])
wout = wnt.nodes.new("ShaderNodeOutputWorld")
wnt.links.new(mix.outputs["Shader"], wout.inputs["Surface"])

# ground for contact shadow / reflection read
ground_mat = bpy.data.materials.new("Ground")
ground_mat.use_nodes = True
ground_mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.9, 0.9, 0.9, 1)
ground_mat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.5
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
bpy.context.active_object.data.materials.append(ground_mat)

target = bpy.data.objects.new("T", None); target.location = (0, 0, 1.12)
scene.collection.objects.link(target)
bpy.ops.object.camera_add(location=(-0.2, -5.6, 1.57))
cam = bpy.context.active_object
cam.data.lens = 55
tr = cam.constraints.new(type='TRACK_TO'); tr.target = target
tr.track_axis = 'TRACK_NEGATIVE_Z'; tr.up_axis = 'UP_Y'
scene.camera = cam

scene.render.engine = 'CYCLES'
scene.cycles.samples = 160
scene.cycles.use_denoising = True
try:
    scene.cycles.device = 'GPU'
except Exception:
    pass
scene.render.resolution_x = 1000
scene.render.resolution_y = 1300

# Tried AgX (even its punchiest "Medium High Contrast" look) here and reverted: direct
# comparison against the reference showed AgX's photographic color science desaturating/
# muting the palette, which fights the bright, saturated Cocomelon-toy look this project wants
# rather than supporting it -- AgX is built for filmic realism, not vivid cartoon graphics.
# Staying on Standard (the flat, non-filmic response) keeps colors reading as vivid as they're
# authored, which is the correct choice for this style even though AgX is the more
# "professional" default in general-purpose rendering.
scene.view_settings.view_transform = 'Standard'

# ---------------------------------------------------------------- compositor: bloom + grade
# The raw Cycles render (even with the material pass above) still looks like an un-graded
# render, not a finished shot -- professional toy/kids'-show renders get a light post pass.
# Cheap version: a soft glow on bright highlights (Glare), a small S-curve contrast bump, and
# a slight saturation boost. Wrapped defensively since Glare's type enum name has moved
# between Blender versions -- if it fails, we still get an ungraded but correct render rather
# than a hard crash.
scene.use_nodes = True
# Blender 5.x moved the compositor from Scene.node_tree (a special scene-only tree with a
# Composite output node) to Scene.compositing_node_group -- a real node group with its own
# interface, output via NodeGroupOutput instead of a Composite node.
ctree = bpy.data.node_groups.new("Compositing", "CompositorNodeTree")
scene.compositing_node_group = ctree
ctree.interface.new_socket(name="Image", in_out='OUTPUT', socket_type='NodeSocketColor')
rlayers = ctree.nodes.new("CompositorNodeRLayers")
composite = ctree.nodes.new("NodeGroupOutput")
last_output = rlayers.outputs["Image"]

try:
    glare = ctree.nodes.new("CompositorNodeGlare")
    glare.glare_type = 'FOG_GLOW'
    glare.threshold = 0.9
    glare.size = 7
    ctree.links.new(last_output, glare.inputs["Image"])
    last_output = glare.outputs["Image"]
except Exception:
    pass

try:
    huesat = ctree.nodes.new("CompositorNodeHueSat")
    huesat.inputs["Saturation"].default_value = 1.12
    ctree.links.new(last_output, huesat.inputs["Image"])
    last_output = huesat.outputs["Image"]
except Exception:
    pass

try:
    bright = ctree.nodes.new("CompositorNodeBrightContrast")
    bright.inputs["Bright"].default_value = 3.0
    bright.inputs["Contrast"].default_value = 6.0
    ctree.links.new(last_output, bright.inputs["Image"])
    last_output = bright.outputs["Image"]
except Exception:
    pass

ctree.links.new(last_output, composite.inputs["Image"])

# Turnaround: front, right, back, left -- camera orbits at a fixed radius/height around the
# target, TRACK_TO keeps it aimed at the character from every angle.
radius = 5.6
# "quarter" (45 deg) added per muzzle-drawing-technique.md: the 3/4 view is specifically where
# muzzle/snout volume and perspective mistakes are hardest to catch and most likely to show --
# straight front/side/back angles can all look fine while the 3/4 view reveals a flat or
# malformed muzzle.
views = {
    "front": 0, "quarter": 45, "right": 90, "back": 180, "left": 270,
}
for name, deg in views.items():
    rad = math.radians(deg)
    cam.location = (radius * math.sin(rad), -radius * math.cos(rad), 1.57)
    out = os.path.join(HERE, f"kamel_turnaround_{name}.png")
    scene.render.filepath = out
    bpy.ops.render.render(write_still=True)
    print(f"RENDERED_TO:{out}")

# Face close-up: small facial detail (teeth, eye catchlights, head tuft) is invisible at the
# full-body turnaround's distance -- a dedicated tight shot is the only way to actually verify
# it, same lesson as the muzzle-angle QA gap documented in muzzle-drawing-technique.md.
target.location = (0, -0.05, 1.41)
cam.location = (0.02, -1.55, 1.44)
scene.cycles.samples = 160
out = os.path.join(HERE, "kamel_face_closeup.png")
scene.render.filepath = out
bpy.ops.render.render(write_still=True)
print(f"RENDERED_TO:{out}")
