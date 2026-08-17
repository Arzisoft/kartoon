"""
Layer 1 of the character pipeline: BASE BODY only.

This produces ONE continuous, watertight mesh per character — no colours, no outfit,
no face. It is the only geometry that ever gets skinned to the rig; everything above it
(materials, outfits, props, face shape keys) attaches on top in later layers.

Why one joined mesh instead of loose primitives:
the v2 blockout (characters.py) built each character from many separate primitive objects,
which can only be rigidly bone-parented — parts follow a bone but never deform. That is fine
for a still blockout and a dead end for animation. Here the primitives are a *construction
scaffold*: they get joined and voxel-remeshed into a single manifold surface that can take
real vertex weights.

Body plan is upright/bipedal (not the v2 quadruped) so the characters can hold, point, hug
and wear things, and so humanoid motion sources retarget onto them.

Run standalone to render a silhouette turnaround:
    blender --background --python base_body.py
"""
import bpy
import math
import os
from mathutils import Vector

# ---------------------------------------------------------------- proportions
# Heights are the one thing that must differ per character. Zayn reads as the big,
# calm one; Milo (later) is built to roughly 0.6x this so the two-shot silhouette
# contrast survives. Head is deliberately ~1/3 of total height (baby schema).
ZAYN_HEIGHT = 2.20
MILO_HEIGHT = 1.36  # ~0.62x Zayn: big/calm vs. small/quick has to read instantly in a two-shot

# Remesh/smoothing settings are a species-read tradeoff, not just a quality dial: too coarse a
# voxel or too much smoothing melts the neck, ears and muzzle into the body mass and the
# character stops reading as a camel at all.
# Voxel size is ABSOLUTE, so a smaller character needs a smaller voxel to keep the same level
# of detail — Milo's beak is roughly a third the size of Zayn's muzzle and dissolves at Zayn's
# setting.
VOXEL_SIZE = 0.022
MILO_VOXEL_SIZE = 0.013
SMOOTH_FACTOR = 0.35
SMOOTH_ITERATIONS = 2


def _scaffold(name):
    """Container for the throwaway primitives that get fused into the base mesh."""
    return {"name": name, "parts": []}


def _track(scaffold, obj):
    # Bake each primitive's location/rotation/scale straight into its mesh data. Without this,
    # join() adopts the *first* part's transform as the joined origin and silently offsets the
    # whole character (an early version of this sank Zayn 2.2m through the floor). With every
    # part at an identity transform, the joined mesh's local coordinates are exactly the
    # construction coordinates and the origin lands on world (0,0,0).
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    scaffold["parts"].append(obj)
    return obj


def add_ball(scaffold, radius, location, scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=location, segments=24, ring_count=12)
    obj = bpy.context.active_object
    obj.scale = scale
    return _track(scaffold, obj)


def add_capsule(scaffold, p1, p2, radius):
    """A limb segment from p1 to p2, with rounded caps so joints fuse cleanly."""
    p1, p2 = Vector(p1), Vector(p2)
    delta = p2 - p1
    length = delta.length
    rot = delta.to_track_quat('Z', 'Y').to_euler()
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=length, location=(p1 + p2) / 2,
                                        rotation=rot, vertices=16)
    _track(scaffold, bpy.context.active_object)
    add_ball(scaffold, radius, p1)
    add_ball(scaffold, radius, p2)
    return scaffold


def fuse(scaffold, voxel_size=VOXEL_SIZE):
    """Join every scaffold part, then voxel-remesh into one continuous manifold surface."""
    parts = scaffold["parts"]
    bpy.ops.object.select_all(action='DESELECT')
    for p in parts:
        p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()

    body = bpy.context.active_object
    body.name = scaffold["name"]

    remesh = body.modifiers.new("Remesh", 'REMESH')
    remesh.mode = 'VOXEL'
    remesh.voxel_size = voxel_size
    bpy.ops.object.modifier_apply(modifier=remesh.name)

    smooth = body.modifiers.new("Smooth", 'SMOOTH')
    smooth.factor = SMOOTH_FACTOR
    smooth.iterations = SMOOTH_ITERATIONS
    bpy.ops.object.modifier_apply(modifier=smooth.name)

    bpy.ops.object.shade_smooth()
    bpy.context.view_layer.update()
    return body


# ---------------------------------------------------------------------- Zayn
# Single source of truth for Zayn's joint positions, in construction space (facing -Y, feet
# on z=0). Both the base mesh below and the skeleton in rig.py read these, so the bones can
# never drift out of the limbs they are supposed to deform. Sided joints are given for the
# +X side; the -X side mirrors by negating x.
ZAYN_JOINTS = {
    "hip":       (0.150, 0.02, 0.92),
    "knee":      (0.170, 0.00, 0.52),
    "ankle":     (0.180, 0.00, 0.16),
    "toe":       (0.180, -0.12, 0.06),
    "pelvis":    (0.000, 0.02, 1.00),
    "spine":     (0.000, -0.02, 1.20),
    "chest":     (0.000, 0.04, 1.42),
    "neck_base": (0.000, 0.05, 1.50),
    "head_base": (0.000, -0.08, 1.98),
    "head_top":  (0.000, -0.14, 2.20),
    "shoulder":  (0.240, 0.03, 1.42),
    "elbow":     (0.360, -0.02, 1.14),
    "wrist":     (0.420, -0.06, 0.86),
    "hand_end":  (0.440, -0.07, 0.72),
}


def joint(table, name, side=1):
    """Joint position from a character's joint table, mirrored to -X when side is -1."""
    x, y, z = table[name]
    return (x * side, y, z)


def build_zayn_base():
    """Upright camel base body, A-pose, facing -Y. Returns the single joined mesh object.

    Built to the cartoon-camel reference direction, which overrides the bible's original
    "big round head, big low-set eyes" baby-schema note for this character. Those two are in
    direct conflict: a big round head on a short neck with small low eyes produced something
    that read as an insect, not a camel. Softness now comes from rounded forms and large eyes
    rather than from skull size.

    Four proportions carry the whole species read, in order of importance:
      1. A LONG sweeping neck — roughly a quarter of total height. This is the camel's
         defining line and the single biggest thing the previous version got wrong.
      2. A SMALL head with a long tapering snout, not a ball.
      3. One clear hump peak behind the shoulders, rising above the back line.
      4. Lanky legs under a pear-shaped body — belly low and forward, chest narrow.
    """
    s = _scaffold("Zayn_Base")

    def J(name, side=1):
        return joint(ZAYN_JOINTS, name, side)

    # --- legs: long and thin, knobbly knee, hoof at the bottom
    for side in (1, -1):
        add_capsule(s, J("hip", side), J("knee", side), 0.082)
        add_ball(s, 0.088, J("knee", side), scale=(0.9, 0.95, 1.05))   # knee joint
        add_capsule(s, J("knee", side), J("ankle", side), 0.060)
        # hoof: chunky and split-looking, planted slightly forward
        add_ball(s, 0.098, (0.180 * side, -0.035, 0.070), scale=(0.90, 1.25, 0.70))

    # --- body: PEAR. Belly low and pushed forward (-Y), chest narrow, so the back line runs
    # up into the hump instead of the torso being one round blob.
    add_ball(s, 0.245, J("pelvis"), scale=(1.02, 1.00, 0.95))
    add_ball(s, 0.278, (0, -0.012, 1.10), scale=(1.01, 1.02, 1.00))     # pelvis-to-belly blend
    add_ball(s, 0.300, (0, -0.030, 1.20), scale=(1.00, 1.05, 1.05))     # belly
    add_ball(s, 0.284, (0, -0.008, 1.28), scale=(1.01, 1.00, 0.98))     # belly-to-chest blend
    add_ball(s, 0.262, (0, 0.020, 1.36), scale=(1.02, 0.95, 0.92))      # lower chest
    add_ball(s, 0.240, J("chest"), scale=(1.05, 0.90, 0.85))            # upper chest/shoulders

    # --- HUMP: one clear peak sitting behind and above the shoulders, taller than it is wide
    # so it reads as a peak rather than a ball bolted on. It has to break the back line
    # decisively — a shy hump just looks like a hunch.
    add_ball(s, 0.230, (0, 0.145, 1.58), scale=(0.95, 0.95, 1.10))
    add_ball(s, 0.165, (0, 0.120, 1.75), scale=(0.85, 0.85, 0.95))      # peak of the hump

    # --- NECK: the defining camel line. Long, thick at the base, tapering upward, and swept
    # forward so the head ends up well ahead of the hump.
    add_capsule(s, (0, 0.050, 1.48), (0, -0.010, 1.72), 0.125)
    add_capsule(s, (0, -0.010, 1.72), (0, -0.070, 1.94), 0.105)

    # --- head: SMALL. Roughly a third the radius the previous version used.
    add_ball(s, 0.170, (0, -0.115, 2.020), scale=(1.00, 1.10, 1.00))

    # --- snout: long and tapering forward and slightly down, ending in a soft nose. Length
    # and taper are what say "camel"; a short blunt muzzle just reads as a nose.
    add_ball(s, 0.135, (0, -0.270, 1.985), scale=(0.92, 1.15, 0.92))
    add_ball(s, 0.110, (0, -0.390, 1.945), scale=(0.95, 1.05, 0.90))
    add_ball(s, 0.092, (0, -0.470, 1.910), scale=(1.00, 0.95, 0.92))    # nose
    add_ball(s, 0.070, (0, -0.455, 1.845), scale=(1.05, 0.90, 0.75))    # soft lower lip

    # --- brow ridges: give the big eyes something to sit on, and stop the head reading as a
    # bare sphere. This is what makes eyes look set INTO a face rather than stuck on it.
    for side in (1, -1):
        add_ball(s, 0.080, (0.082 * side, -0.212, 2.078), scale=(0.95, 0.85, 0.80))

    # --- ears: small and pointed, set back on top of the skull
    for side in (1, -1):
        add_ball(s, 0.055, (0.125 * side, 0.010, 2.160), scale=(0.55, 0.70, 1.55))

    # --- arms: long and thin like the legs, ending in a rounded hoof-mitten
    for side in (1, -1):
        add_capsule(s, J("shoulder", side), J("elbow", side), 0.086)
        add_ball(s, 0.082, J("elbow", side))                            # elbow joint
        add_capsule(s, J("elbow", side), J("wrist", side), 0.070)
        add_ball(s, 0.096, (0.435 * side, -0.070, 0.745), scale=(0.90, 1.05, 1.10))
        add_ball(s, 0.048, (0.370 * side, -0.108, 0.785))               # thumb nub

    # --- tail: thin, hanging off the rump with a tuft at the end
    add_capsule(s, (0, 0.190, 1.06), (0, 0.245, 0.82), 0.032)
    add_ball(s, 0.062, (0, 0.255, 0.775), scale=(0.75, 0.85, 1.25))

    return fuse(s, voxel_size=0.017)


# ---------------------------------------------------------------------- Milo
# Same joint NAMES as Zayn — that is what lets one motion clip play on both and what lets
# humanoid motion retarget onto either. Only the positions differ: Milo is ~0.62x Zayn's
# height with a proportionally bigger head, a much shorter neck, and wings where the arms go.
MILO_JOINTS = {
    "hip":       (0.095, 0.00, 0.395),
    "knee":      (0.105, 0.00, 0.255),
    "ankle":     (0.110, 0.00, 0.090),
    "toe":       (0.110, -0.135, 0.045),
    "pelvis":    (0.000, 0.00, 0.445),
    "spine":     (0.000, 0.01, 0.600),
    "chest":     (0.000, 0.01, 0.775),
    "neck_base": (0.000, 0.02, 0.855),
    "head_base": (0.000, -0.01, 0.945),
    "head_top":  (0.000, -0.02, 1.310),
    "shoulder":  (0.215, 0.045, 0.815),
    "elbow":     (0.300, 0.020, 0.590),
    "wrist":     (0.335, -0.015, 0.370),
    "hand_end":  (0.350, -0.035, 0.245),
}


def build_milo_base():
    """Upright budgie base body, A-pose, facing -Y. Returns the single joined mesh object.

    Milo needs almost no re-thinking of the body plan — birds are already bipedal — but two
    things do change relative to a literal budgie:

      * The wings double as arms. A real budgie's wing cannot hold a spoon or point at
        something, and most of the target episode topics need exactly that. So each wing is
        built along the arm chain and ends in a small mitten hand at the tip.
      * The beak has to be able to open. Rhubarb lip-sync drives mouth shapes, and a solid
        cone has no mouth to shape, so the beak is built as an upper and a lower half with a
        seam between them for the face layer to work with later.

    Species cues (production-notes names these as Milo's required markers):
      * the hooked beak
      * cheek patches — carried here as a slight raised form so the colour layer has
        geometry to sit on rather than being a flat decal
    """
    s = _scaffold("Milo_Base")

    def J(name, side=1):
        return joint(MILO_JOINTS, name, side)

    # --- legs: short, thin, set close together (bird stance)
    for side in (1, -1):
        add_capsule(s, J("hip", side), J("knee", side), 0.048)
        add_capsule(s, J("knee", side), J("ankle", side), 0.040)
        # foot, splayed forward like a perching bird's
        add_ball(s, 0.062, (0.110 * side, -0.055, 0.038), scale=(0.80, 1.70, 0.45))

    # --- body: one continuous egg, widest low down. Budgies have no visible waist or hips.
    add_ball(s, 0.155, J("pelvis"), scale=(1.02, 0.95, 0.90))
    add_ball(s, 0.205, J("spine"), scale=(1.02, 0.98, 1.05))
    add_ball(s, 0.195, J("chest"), scale=(1.05, 0.95, 0.95))

    # --- neck: barely there. A budgie's head sits almost straight on the body, and this is
    # a big part of what separates the small/quick read from Zayn's long-necked calm.
    add_capsule(s, J("neck_base"), J("head_base"), 0.105)

    # --- head: proportionally larger than Zayn's (baby schema pushed further on the small one)
    add_ball(s, 0.235, (0, -0.02, 1.085), scale=(1.0, 1.0, 0.98))

    # --- BEAK: primary budgie cue. Short, deep and hooked DOWNWARD — the hook is the whole
    # difference between "budgie" and "generic bird". Upper and lower halves are separated so
    # the face layer has a seam to open for lip sync.
    # These MUST sit forward of the head's front surface (head centre y-0.02, radius 0.235,
    # so the face is at about y-0.255); tucked any further back the beak is simply inside the
    # skull and the character reads as an eyeball with no face at all.
    # Kept NARROW across X. A beak as wide as it is tall merges into the cheeks and reads as
    # a bulbous nose; the narrow cross-section plus the downward hook is what says "budgie".
    # Short and tucked, not long and protruding: a beak that reaches far forward reads as a
    # nose no matter how narrow it is. A budgie's beak barely clears the face and drops almost
    # straight down from under the cere.
    add_ball(s, 0.072, (0, -0.240, 1.030), scale=(0.72, 1.00, 1.10))       # upper beak base
    add_ball(s, 0.050, (0, -0.268, 0.955), scale=(0.70, 0.90, 1.35))       # hooked tip, curling down
    add_ball(s, 0.046, (0, -0.232, 0.918), scale=(0.85, 0.95, 0.60))       # lower beak
    # cere (the fleshy band above a budgie's beak) — small but very recognisable
    add_ball(s, 0.062, (0, -0.220, 1.125), scale=(1.10, 0.75, 0.50))

    # --- cheek patches: raised slightly so the colour layer sits on real form
    for side in (1, -1):
        add_ball(s, 0.078, (0.155 * side, -0.155, 0.995), scale=(0.55, 0.85, 0.85))

    # --- wings-as-arms: a flattened plate running along each arm chain, plus a mitten hand
    # at the tip so Milo can actually hold and point.
    for side in (1, -1):
        add_capsule(s, J("shoulder", side), J("elbow", side), 0.058)
        add_capsule(s, J("elbow", side), J("wrist", side), 0.048)
        # the wing plate: thin across X, broad in Z, so it reads as a folded wing in profile
        add_ball(s, 0.150, (0.280 * side, 0.010, 0.590), scale=(0.34, 0.70, 1.45))
        # mitten hand at the wing tip
        add_ball(s, 0.058, (0.350 * side, -0.035, 0.255), scale=(0.85, 1.05, 1.0))
        add_ball(s, 0.030, (0.300 * side, -0.065, 0.275))

    # --- tail: long and sweeping down-back off the rump, the budgie's other big silhouette cue.
    # Built from capsules rather than spaced balls: separate balls left gaps the voxel remesh
    # turned into a detached blob floating behind him.
    add_capsule(s, (0, 0.090, 0.520), (0, 0.230, 0.360), 0.080)
    add_capsule(s, (0, 0.230, 0.360), (0, 0.330, 0.235), 0.055)
    add_capsule(s, (0, 0.330, 0.235), (0, 0.395, 0.140), 0.036)

    return fuse(s, voxel_size=MILO_VOXEL_SIZE)


# ------------------------------------------------------------ preview scene
# Temporary eyes for judging the silhouette read. NOT part of the base mesh — the face is a
# later layer (shape keys for expression + lip sync). Radius and position per character.
#   sclera radius, sclera centre, pupil radius, pupil centre
# The eyes get a WHITE sclera with a dark pupil rather than a solid dark bead. On a stylised
# animal head that difference is not a detail: two solid dark dots read as insect eyes, and
# every cartoon-camel reference has visible whites. It is the cheapest single fix for making
# the head read as a face.
PREVIEW_EYES = {
    "Zayn_Base": (0.063, (0.086, -0.248, 2.076), 0.032, (0.098, -0.294, 2.072)),
    "Milo_Base": (0.062, (0.150, -0.170, 1.112), 0.032, (0.166, -0.218, 1.108)),
}

CHARACTERS = {
    "zayn": {"build": build_zayn_base, "mesh": "Zayn_Base", "spread": 1.30,
             "target_z": 1.20, "cam_dist": 8.0},
    "milo": {"build": build_milo_base, "mesh": "Milo_Base", "spread": 0.95,
             "target_z": 0.70, "cam_dist": 5.2},
}


def _clay():
    mat = bpy.data.materials.get("Clay") or bpy.data.materials.new("Clay")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.72, 0.70, 0.68, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.65
    return mat


def _eye_material(name, colour):
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        bsdf.inputs["Base Color"].default_value = (*colour, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.25
    return mat


def _preview_eyes(mesh_name, parent):
    sclera_r, (sx, sy, sz), pupil_r, (px, py, pz) = PREVIEW_EYES[mesh_name]
    white = _eye_material("PreviewSclera", (0.97, 0.96, 0.94))
    dark = _eye_material("PreviewPupil", (0.03, 0.03, 0.04))

    for side in (1, -1):
        tag = "L" if side > 0 else "R"
        for label, radius, loc, mat in (
            ("Sclera", sclera_r, (sx * side, sy, sz), white),
            ("Pupil", pupil_r, (px * side, py, pz), dark),
        ):
            bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=loc,
                                                 segments=20, ring_count=10)
            eye = bpy.context.active_object
            eye.name = f"{mesh_name}_Preview{label}_{tag}"
            eye.data.materials.append(mat)
            bpy.ops.object.shade_smooth()
            eye.parent = parent


def _stage(target_z, cam_dist, res_x=1600, res_y=800):
    """Backdrop, camera and three-point lighting, shared by every preview render."""
    scene = bpy.context.scene

    backdrop = bpy.data.materials.get("Backdrop") or bpy.data.materials.new("Backdrop")
    backdrop.use_nodes = True
    backdrop.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.88, 0.90, 0.92, 1)
    bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
    bpy.context.active_object.data.materials.append(backdrop)
    bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 5, 5), rotation=(math.radians(90), 0, 0))
    bpy.context.active_object.data.materials.append(backdrop)

    world = bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.85, 0.88, 0.91, 1.0)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.7

    target = bpy.data.objects.new("Target", None)
    target.location = (0, 0, target_z)
    scene.collection.objects.link(target)
    bpy.ops.object.camera_add(location=(0, -cam_dist, target_z + 0.45))
    cam = bpy.context.active_object
    cam.data.lens = 50
    track = cam.constraints.new(type='TRACK_TO')
    track.target = target
    track.track_axis = 'TRACK_NEGATIVE_Z'
    track.up_axis = 'UP_Y'
    scene.camera = cam

    for loc, energy, size in [((-4, -5, 5), 900, 4), ((4, -4, 3), 350, 4), ((0, 5, 4), 300, 3)]:
        bpy.ops.object.light_add(type='AREA', location=loc)
        bpy.context.active_object.data.energy = energy
        bpy.context.active_object.data.size = size

    try:
        scene.render.engine = 'BLENDER_EEVEE_NEXT'
    except Exception:
        scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = res_x
    scene.render.resolution_y = res_y
    scene.render.image_settings.file_format = 'PNG'


def build_turnaround(which):
    """Front / three-quarter / side turnaround so one character's silhouette can be judged."""
    spec = CHARACTERS[which]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene

    body = spec["build"]()
    body.data.materials.append(_clay())

    spread = spec["spread"]
    for i, (x, deg) in enumerate([(-spread, 0), (0.0, 45), (spread, 90)]):
        if i == 0:
            obj = body
        else:
            obj = body.copy()
            obj.data = body.data  # linked duplicate: same mesh, no extra memory
            scene.collection.objects.link(obj)
        obj.location = (x, 0, 0)
        obj.rotation_euler = (0, 0, math.radians(deg))
        _preview_eyes(spec["mesh"], obj)

    _stage(spec["target_z"], spec["cam_dist"])
    return body


def build_lineup():
    """Both characters side by side — the only render that actually tests the size contrast,
    which is the show's core visual engine (big/calm/outdoor vs. small/quick/indoor)."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    clay = _clay()

    zayn = build_zayn_base()
    zayn.data.materials.append(clay)
    zayn.location = (-0.75, 0, 0)
    _preview_eyes("Zayn_Base", zayn)

    milo = build_milo_base()
    milo.data.materials.append(clay)
    milo.location = (0.72, 0, 0)
    _preview_eyes("Milo_Base", milo)

    _stage(target_z=1.05, cam_dist=6.4, res_x=1400, res_y=850)
    return zayn, milo


def _render(path):
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print(f"RENDERED_TO:{path}")


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))

    for which in ("zayn", "milo"):
        body = build_turnaround(which)
        print(f"{which.upper()}_VERTS:{len(body.data.vertices)} "
              f"HEIGHT:{round(body.dimensions.z, 3)}")
        _render(os.path.join(here, f"{which}_base.png"))

    zayn, milo = build_lineup()
    print(f"HEIGHT_RATIO:{round(milo.dimensions.z / zayn.dimensions.z, 3)}")
    _render(os.path.join(here, "lineup_base.png"))
