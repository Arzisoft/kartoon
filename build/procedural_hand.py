"""
Procedural hand builder -- continuous quad-topology tapered-tube fingers with a natural
relaxed curl baked into the rest geometry, replacing color_layer.extremity_cap()'s sphere-stack
fingers (which read as separate blobs rather than one continuous digit).

Deliberately NOT using the raw Geometry-Nodes bend-math from
.claude/skills/blender-character-pipeline/references/procedural-hand-geometry-nodes.md --
that source's own author described their joint-0 drift-correction as "trial and error," which
means getting it right needs live interactive preview. We can't do that headlessly. Instead:
build the finger SHAPE procedurally via bmesh (fully scriptable, no manual steps, same as
everything else in this pipeline) with the curl already baked into the rest pose, and pose it
with bones if/when we need it posed differently -- bone transforms are Blender's own proven,
already-correct system, not hand-derived pivot math.

Run standalone: blender --background --python procedural_hand.py
"""
import bpy
import bmesh
import math
import os
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))


def _ring(bm, center, radius, direction, up, segments=10):
    """A ring of verts around `center`, in the plane perpendicular to `direction`."""
    direction = direction.normalized()
    tangent = up - up.dot(direction) * direction
    if tangent.length < 1e-6:
        tangent = Vector((1, 0, 0)) - direction * direction.x
    tangent.normalize()
    bitangent = direction.cross(tangent)
    return [
        bm.verts.new(center + tangent * math.cos(a) * radius + bitangent * math.sin(a) * radius)
        for a in (2 * math.pi * i / segments for i in range(segments))
    ]


def build_finger(name, base_pos, direction, length, base_radius, tip_radius,
                  curl_deg=0, curl_start=0.4, rings_count=7, segments=10,
                  material=None, parent=None):
    """A continuous tapered tube: `rings_count` rings bridged into quads, radius interpolated
    smoothly from base to tip. `curl_deg` is a total bend angle distributed gradually across
    the rings past `curl_start` (fraction of the finger's length), not applied as one sharp
    kink at a single ring.

    Two earlier attempts bent the finger at ONE joint ring and both pinched visibly --
    confirmed by direct test renders, not a guess. That's a real geometry problem, not a bug:
    bending a tube sharply at a single ring is like kinking a garden hose, the inside of the
    bend collapses. The fix is standard for procedural tube bending -- spread the same total
    angle across several rings instead of concentrating it at one, so each individual ring-to-
    ring step turns only a few degrees and the surface stays smooth. The bend axis (`right`) is
    computed once from the REST direction so the whole curl stays in one consistent plane
    instead of drifting as cur_dir rotates.
    """
    bm = bmesh.new()
    direction = Vector(direction).normalized()
    up = Vector((0, 0, 1))
    if abs(direction.dot(up)) > 0.98:
        up = Vector((0, 1, 0))
    right = direction.cross(up).normalized()

    step_len = length / (rings_count - 1)
    bend_start_ring = max(1, round(curl_start * (rings_count - 1)))
    bend_ring_count = (rings_count - 1) - bend_start_ring
    per_ring_angle = (curl_deg / bend_ring_count) if bend_ring_count > 0 else 0
    bend_rot = Matrix.Rotation(math.radians(per_ring_angle), 4, right)

    cur_pos = Vector(base_pos)
    cur_dir = direction.copy()
    rings = [_ring(bm, cur_pos, base_radius, cur_dir, up, segments)]
    for i in range(1, rings_count):
        if i > bend_start_ring:
            cur_dir = (bend_rot @ cur_dir).normalized()
        cur_pos = cur_pos + cur_dir * step_len
        t = i / (rings_count - 1)
        radius = base_radius * (1 - t) + tip_radius * t
        rings.append(_ring(bm, cur_pos, radius, cur_dir, up, segments))

    for r1, r2 in zip(rings, rings[1:]):
        for i in range(segments):
            j = (i + 1) % segments
            bm.faces.new((r1[i], r1[j], r2[j], r2[i]))
    bm.faces.new(rings[0][::-1])
    tip_center = bm.verts.new(cur_pos + cur_dir * (tip_radius * 0.6))
    for i in range(segments):
        j = (i + 1) % segments
        bm.faces.new((rings[-1][i], rings[-1][j], tip_center))

    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    if material:
        obj.data.materials.append(material)
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.shade_smooth()
    sub = obj.modifiers.new("Subsurf", 'SUBSURF')
    sub.levels = 1
    if parent:
        obj.parent = parent
    return obj


def build_hand(name, palm_center, side, material, parent=None,
               palm_radius=0.048, palm_scale=(0.9, 0.95, 1.05)):
    """Palm (simple squashed sphere -- palms are static/simple, no need to build them
    procedurally) plus a thumb and four fanned fingers, each curled naturally. `side` is
    +1 (left) or -1 (right); finger offsets mirror the same layout used previously in
    cycles_sss_test.py's extremity_cap-based hand.
    """
    bpy.ops.mesh.primitive_uv_sphere_add(radius=palm_radius, location=palm_center, segments=16, ring_count=8)
    palm = bpy.context.active_object
    palm.name = f"{name}_Palm"
    palm.scale = palm_scale
    palm.data.materials.append(material)
    bpy.ops.object.shade_smooth()
    if parent:
        palm.parent = parent

    # (base_offset_from_palm_center, direction_xyz, length, base_radius, tip_radius) -- each
    # finger needs its OWN base point spread across the palm's edge, not all sprouting from
    # the palm's exact centre (an early attempt fanned out from one point and looked like a
    # knot of sausages, not a hand). X spacing between adjacent finger bases (~0.034) is kept
    # clear of 2x finger radius (~0.032) so they don't overlap at the base. Only 3 fingers +
    # thumb (no pinky) -- a deliberate reduced digit count for chunky toy-proportions, matching
    # the design already used for the sphere-stack fingers.
    # Radii thickened ~1.35x from the first working version -- an isolated close-up test
    # looked fine, but at Zayn's actual on-character scale/camera distance thin capsule
    # fingers read as spindly matchsticks, thinner and less "chunky toy" than even the old
    # sphere-stack version despite being cleaner topology. Chunkiness matters more than
    # anatomical slenderness for this style (chibi-proportion-theory.md).
    # curl_deg is now spread across several rings (see build_finger), not one sharp joint --
    # safe to bring back a natural relaxed curl this time.
    # Index pushed out slightly (0.036 -> 0.044) and Index/Middle curl eased back a touch --
    # curling brought their tips into contact; widening the base gap and curling a little less
    # keeps them from converging while still reading as a relaxed hand.
    digit_specs = [
        ("Thumb", (0.046 * side, -0.004, 0.008), (0.75 * side, -0.55, 0.42), 0.070, 0.023, 0.017, 16),
        ("Index", (0.044 * side, -0.040, 0.008), (-0.16 * side, -0.97, 0.16), 0.125, 0.022, 0.016, 24),
        ("Middle", (0.002 * side, -0.046, 0.002), (-0.03 * side, -0.99, -0.02), 0.135, 0.023, 0.016, 28),
        ("Ring", (-0.032 * side, -0.040, -0.006), (0.10 * side, -0.97, -0.20), 0.120, 0.022, 0.015, 34),
    ]
    parts = [palm]
    for tag, offset, direction, length, base_r, tip_r, curl in digit_specs:
        base_pos = Vector(palm_center) + Vector(offset)
        parts.append(build_finger(
            f"{name}_{tag}", base_pos, direction, length, base_r, tip_r, curl_deg=curl,
            material=material, parent=parent or palm,
        ))
    return parts


if __name__ == "__main__":
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene

    mat = bpy.data.materials.new("HandTest")
    mat.use_nodes = True
    mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.26, 0.15, 0.07, 1.0)
    mat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.32

    build_hand("TestHand", (0, 0, 0), side=-1, material=mat, palm_scale=(0.9, 1.0, 1.15))

    world = bpy.data.worlds.new("W")
    scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.85, 0.87, 0.9, 1.0)
    world.node_tree.nodes["Background"].inputs[1].default_value = 1.0

    # Hand extent is small -- palm radius ~0.05, fingers only ~0.1-0.13 long -- the first
    # attempt's camera/target were sized for a hand ~10x this big and looked at empty space.
    # Widened generously (wider lens, camera pulled back) vs. the previous attempt -- the hand
    # is now visibly wider (fingers spread further apart to fix overlap) so framing needs more
    # margin than a tight guess would give.
    target = bpy.data.objects.new("T", None)
    target.location = (0, -0.07, 0.0)
    scene.collection.objects.link(target)
    bpy.ops.object.camera_add(location=(0.02, -0.40, 0.20))
    cam = bpy.context.active_object
    cam.data.lens = 35
    tr = cam.constraints.new(type='TRACK_TO')
    tr.target = target
    tr.track_axis = 'TRACK_NEGATIVE_Z'
    tr.up_axis = 'UP_Y'
    scene.camera = cam

    # Area light energy (Watts) needs to scale down hugely for a ~0.15-unit object -- the
    # first attempt used values tuned for the full ~1.5-unit character and blew out the
    # highlights so badly the dark brown material read as near-white.
    for loc, energy in [((-0.3, -0.4, 0.3), 0.6), ((0.3, -0.25, 0.2), 0.3)]:
        bpy.ops.object.light_add(type='AREA', location=loc)
        bpy.context.active_object.data.energy = energy
        bpy.context.active_object.data.size = 0.3

    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 120
    scene.render.resolution_x = 900
    scene.render.resolution_y = 700
    out = os.path.join(HERE, "hand_test.png")
    scene.render.filepath = out
    bpy.ops.render.render(write_still=True)
    print(f"RENDERED_TO:{out}")
