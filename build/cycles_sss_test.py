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
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import base_body  # noqa: E402
import color_layer  # noqa: E402
import procedural_hand  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RETOPO = os.path.join(HERE, "retopo")
HDRI = os.path.join(HERE, "hdri", "studio_small_08_1k.hdr")

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

bpy.ops.wm.obj_import(filepath=os.path.join(RETOPO, "zayn_retopo.obj"), forward_axis='Y', up_axis='Z')
zayn = bpy.context.selected_objects[0]
zayn.name = "Zayn_SSS"
zayn.modifiers.new("Subsurf", 'SUBSURF').levels = 2  # higher -- Cycles SSS reads better on denser geo

skin_mat = color_layer.advanced_material(
    "Zayn_SSS_Skin", (0.95, 0.58, 0.18), roughness=0.28, subsurface=0.8,
    radius=(0.9, 0.45, 0.2), ao_strength=0.30, rim_strength=0.28, rim_color=(1.0, 0.85, 0.65),
)
zayn.data.materials.append(skin_mat)
bpy.ops.object.select_all(action='DESELECT'); zayn.select_set(True)
bpy.context.view_layer.objects.active = zayn
bpy.ops.object.shade_smooth()

dark_brown = color_layer.advanced_material(
    "Zayn_SSS_Dark", (0.26, 0.15, 0.07), roughness=0.32, ao_strength=0.25, rim_strength=0.15,
)

# Feet: split-toe camel foot (two padded lobes with a gap between, not a single horse-style
# hoof) -- real camel anatomy, and a clearer species cue than a plain round ball.
for side in (1, -1):
    # Foot must overlap the ankle joint (0.180, 0.00, 0.16) -- it was centred 0.09 below
    # the joint before, leaving a visible gap between the leg and the foot blob.
    foot_center = (0.180 * side, -0.015, 0.115)
    toe_gap = 0.052
    color_layer.extremity_cap(
        f"Zayn_Hoof_{side}",
        [(0.066, (foot_center[0] - toe_gap, foot_center[1] - 0.01, foot_center[2]), (0.85, 1.25, 0.70)),
         (0.066, (foot_center[0] + toe_gap, foot_center[1] - 0.01, foot_center[2]), (0.85, 1.25, 0.70)),
         (0.050, (foot_center[0], foot_center[1] + 0.03, foot_center[2] + 0.02), (1.0, 0.9, 0.7))],  # pad blend
        dark_brown, parent=zayn,
    )

# Hands: procedural continuous-tube fingers (build/procedural_hand.py) instead of the
# overlapping-sphere-stack extremity_cap hands -- one smooth tapered digit per finger, built
# in its own local "fingers point along -Y" space then placed at the wrist and rotated 90 deg
# about X so -Y maps to -Z (fingers hang downward, matching the arm's resting angle).
for side in (1, -1):
    hand_root = bpy.data.objects.new(f"Zayn_HandRoot_{side}", None)
    scene.collection.objects.link(hand_root)
    hand_root.parent = zayn
    # Wrist joint is (0.420, -0.06, 0.71) after the arm was shortened along with the legs --
    # offset -0.045 below the joint so the palm overlaps the forearm end, same as before.
    hand_root.location = (0.420 * side, -0.060, 0.665)
    hand_root.rotation_euler = (math.radians(90), 0, 0)
    procedural_hand.build_hand(f"Zayn_Hand_{side}", (0, 0, 0), side=side,
                                material=dark_brown, parent=hand_root)

# Water-canteen cap -- Zayn's a camel, he stores water, so the cap references a canteen: a
# rounded dome + a small spout/cap nub on top, like a water bottle lid.
cap_mat = color_layer.advanced_material(
    "Zayn_SSS_Cap", (0.15, 0.55, 0.75), roughness=0.3, fabric=True,
    ao_strength=0.3, rim_strength=0.2,
)
# Baseball cap: rounded dome + a flat forward brim, plus a couple of bright drinking straws
# poking out the top -- the "he stores water" joke read as "juice box straws" instead of a
# plain canteen spout, which didn't land visually.
color_layer.extremity_cap(
    "Zayn_Cap", [(0.155, (0, -0.02, 2.07), (1.05, 1.05, 0.55))], cap_mat, parent=zayn,
)
# brim: flattened, pushed forward and down off the front of the dome
color_layer.extremity_cap(
    "Zayn_Cap_Brim", [(0.11, (0, -0.20, 1.98), (1.3, 0.75, 0.16))], cap_mat, parent=zayn,
)
# button on top, like a real baseball cap
color_layer.extremity_cap(
    "Zayn_Cap_Button", [(0.025, (0, -0.02, 2.20), (1.0, 1.0, 0.7))], cap_mat, parent=zayn,
)
straw_colors = [(0.85, 0.15, 0.15), (0.15, 0.55, 0.85)]
for i, side in enumerate((1, -1)):
    straw_mat = color_layer.advanced_material(
        f"Zayn_Straw_{i}", straw_colors[i], roughness=0.3, ao_strength=0.2, rim_strength=0.15,
    )
    p1 = Vector((0.05 * side, -0.05, 2.11))
    p2 = Vector((0.13 * side, -0.15, 2.40))
    mid = (p1 + p2) / 2
    length = (p2 - p1).length
    bpy.ops.mesh.primitive_cylinder_add(radius=0.02, depth=length, location=mid, vertices=16)
    straw = bpy.context.active_object
    straw.name = f"Zayn_Straw_{i}"
    # orient the cylinder's local Z axis along p1->p2
    straw.rotation_mode = 'QUATERNION'
    straw.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(p2 - p1)
    straw.data.materials.append(straw_mat)
    bpy.ops.object.select_all(action='DESELECT')
    straw.select_set(True)
    bpy.context.view_layer.objects.active = straw
    bpy.ops.object.shade_smooth()
    straw.parent = zayn

# T-shirt + shorts -- original playful outfit, bright contrasting colours, simple circle
# "badge" graphic on the chest for a funny touch. Same shrinkwrap-drape technique as the
# earlier blanket (proven to drape cleanly over the torso from multiple angles).
shirt_mat = color_layer.advanced_material(
    "Zayn_SSS_Shirt", (0.85, 0.18, 0.15), roughness=0.55, fabric=True,
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
color_layer.extremity_cap(
    "Zayn_Shirt", [(0.34, (0, -0.01, 1.09), (1.05, 0.80, 1.62))], shirt_mat, parent=zayn,
)
for side in (1, -1):
    color_layer.extremity_cap(
        f"Zayn_Sleeve_{side}", [(0.125, (0.235 * side, 0.02, 1.25), (1.0, 1.0, 0.9))],
        shirt_mat, parent=zayn,
    )
# Turtleneck collar: a separate stretched piece rising from the shirt's top, angled back to
# cover the hump (which sits behind/above the shoulder line) instead of leaving it bare
# above the collar.
color_layer.extremity_cap(
    "Zayn_Shirt_Collar", [(0.22, (0, 0.08, 1.58), (1.1, 0.85, 0.80))], shirt_mat, parent=zayn,
)
# The collar and torso spheres leave a saddle dip between them right where the hump sits,
# letting bare skin show through. Overlay shirt-coloured spheres directly on the hump's own
# two ball centres (from base_body.py's hump definition), sized larger than the hump itself,
# so the fabric guarantees full coverage regardless of gaps between the other shirt pieces.
color_layer.extremity_cap(
    "Zayn_Shirt_HumpCover",
    [(0.245, (0, 0.130, 1.41), (1.05, 1.05, 1.15)),
     (0.180, (0, 0.110, 1.55), (0.95, 0.95, 1.05))],
    shirt_mat, parent=zayn,
)
# Badge: a clean flat circle (was an odd stretched blob before), centred on the chest.
badge_mat = color_layer.advanced_material(
    "Zayn_SSS_Badge", (1.0, 0.95, 0.9), roughness=0.4, ao_strength=0.2, rim_strength=0.2,
)
color_layer.extremity_cap(
    # Was squashed along Z (flat top/bottom), so front camera saw its thin EDGE -- a flat
    # oval instead of a round badge. A coin-shaped badge needs its flat faces pointing
    # front/back (squash along Y), so the front view sees the full round face.
    "Zayn_Badge", [(0.065, (0, -0.27, 1.11), (1.0, 0.28, 1.0))], badge_mat, parent=zayn,
)

shorts_mat = color_layer.advanced_material(
    "Zayn_SSS_Shorts", (0.95, 0.75, 0.10), roughness=0.55, fabric=True,
    ao_strength=0.35, rim_strength=0.18,
)
color_layer.extremity_cap(
    # Oversized/baggy cut, same theory as the shirt above -- wider than the hips and dropped
    # slightly lower for a loose cargo-short silhouette instead of a snug fit. Y depth pulled
    # in same as the shirt, same reason -- was reading round/fat from the side.
    "Zayn_Shorts", [(0.28, (0, 0.0, 0.78), (1.10, 0.80, 1.05))], shorts_mat, parent=zayn,
)

# Mouth: a thin dark crease between the snout tip and the existing lower-lip bump (which
# had no visible mouth line before -- just a smooth continuation of the snout). Nostrils
# added for a clearer nose read, since the nose was previously just an unmarked bump.
mouth_mat = color_layer.advanced_material(
    "Zayn_Final_Mouth", (0.35, 0.15, 0.13), roughness=0.4, ao_strength=0.15, rim_strength=0.08,
)
color_layer.extremity_cap(
    "Zayn_Mouth", [(0.058, (0, -0.475, 1.725), (1.15, 0.55, 0.35))], mouth_mat, parent=zayn,
)
nostril_mat = color_layer.advanced_material(
    "Zayn_Final_Nostril", (0.30, 0.13, 0.10), roughness=0.4, ao_strength=0.15, rim_strength=0.08,
)
for side in (1, -1):
    color_layer.extremity_cap(
        f"Zayn_Nostril_{side}",
        [(0.018, (0.035 * side, -0.505, 1.765), (0.7, 1.3, 0.9))],
        nostril_mat, parent=zayn,
    )

eyes = base_body._preview_eyes("Zayn_Base", zayn)
for e in eyes:
    if "Sclera" in e.name:
        e.data.materials[0].node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.1

# Overall size down ~15% -- was reading too large/bulky
zayn.scale = (0.85, 0.85, 0.85)

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
    out = os.path.join(HERE, f"zayn_turnaround_{name}.png")
    scene.render.filepath = out
    bpy.ops.render.render(write_still=True)
    print(f"RENDERED_TO:{out}")
