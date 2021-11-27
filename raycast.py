import bpy
import math
import random
from mathutils import Vector, Quaternion, geometry, kdtree
from bpy_extras import view3d_utils

def mouse_raycast(context, coord):
    """Raycast for object under mouse cursor.

    Parameters
    context : bpy.Context
    coord : [x, y]

    Returns
    has_hit : bool
    snapped_location : ?
    snapped_normal : ?
    snapped_rotation : ?
    face_index : int
        Face index of the evaluated mesh that the ray hit
    obj : bpy.types.Object
    matrix : ?
    """
    r = context.region
    rv3d = context.region_data

    # get the ray from the viewport and mouse
    view_vector = view3d_utils.region_2d_to_vector_3d(r, rv3d, coord)
    ray_origin = view3d_utils.region_2d_to_origin_3d(r, rv3d, coord)
    ray_target = ray_origin + (view_vector * 1000000000)

    vec = ray_target - ray_origin
    depsgraph = context.evaluated_depsgraph_get()

    has_hit, snapped_location, snapped_normal, face_index, obj, matrix = bpy.context.scene.ray_cast(
        depsgraph, ray_origin, vec)

    # rote = mathutils.Euler((0, 0, math.pi))
    randoffset = math.pi
    if has_hit:
        snapped_rotation = snapped_normal.to_track_quat('Z', 'Y').to_euler()
        up = Vector((0, 0, 1))
        props = bpy.context.scene.mt_am_spawn_props
        if props.snap_to_face:
            # if props.randomize_rotation and snapped_normal.angle(up) < math.radians(10.0):
            randoffset = props.offset_rotation_amount + math.pi + (
                random.random() - 0.5) * props.randomize_rotation_amount
            # else:
            #     randoffset = props.offset_rotation_amount  # we don't rotate this way on walls and ceilings. + math.pi
        else:
            snapped_rotation = Quaternion((0, 0, 0, 0)).to_euler()
            randoffset = props.offset_rotation_amount + math.pi + (
                random.random() - 0.5) * props.randomize_rotation_amount
        # snapped_rotation.z += math.pi + (random.random() - 0.5) * .2

    else:
        snapped_rotation = Quaternion((0, 0, 0, 0)).to_euler()

    snapped_rotation.rotate_axis('Z', randoffset)

    return has_hit, snapped_location, snapped_normal, snapped_rotation, face_index, obj, matrix


def floor_raycast(context, coord):
    """Raycast for 'floor' i.e. imaginary plane at z=0."""
    r = context.region
    rv3d = context.region_data

    # get the ray from the viewport and mouse
    view_vector = view3d_utils.region_2d_to_vector_3d(r, rv3d, coord)
    ray_origin = view3d_utils.region_2d_to_origin_3d(r, rv3d, coord)
    ray_target = ray_origin + (view_vector * 1000)

    # various intersection plane normals are needed for corner cases that might actually happen quite often - in front and side view.
    # default plane normal is scene floor.
    plane_normal = (0, 0, 1)
    if math.isclose(view_vector.x, 0, abs_tol=1e-4) and math.isclose(view_vector.z, 0, abs_tol=1e-4):
        plane_normal = (0, 1, 0)
    elif math.isclose(view_vector.z, 0, abs_tol=1e-4):
        plane_normal = (1, 0, 0)

    snapped_location = geometry.intersect_line_plane(
        ray_origin,
        ray_target,
        (0, 0, 0),
        plane_normal,
        False)

    if snapped_location is not None:
        has_hit = True
        snapped_normal = Vector((0, 0, 1))
        face_index = None
        obj = None
        matrix = None
        snapped_rotation = snapped_normal.to_track_quat('Z', 'Y').to_euler()
        props = bpy.context.scene.mt_am_spawn_props
        if props.randomize_rotation:
            randoffset = props.offset_rotation_amount + math.pi + (
                random.random() - 0.5) * props.randomize_rotation_amount
        else:
            randoffset = props.offset_rotation_amount + math.pi
        snapped_rotation.rotate_axis('Z', randoffset)

    return has_hit, snapped_location, snapped_normal, snapped_rotation, face_index, obj, matrix
