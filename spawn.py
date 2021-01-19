import bpy
from .raycast import mouse_raycast, floor_raycast
from .utils import find_vertex_group_of_face, assign_mat_to_vert_group
from .append import append_collection, append_material, append_object

def spawn_object(context, asset, x, y):
    """Spawn an object at the cursor based on the passed in asset description.

    Args:
        context (bpy.context): context
        asset (dict): MakeTile asset description
        x (float): mouse x
        y (float): mouse y

    Returns:
        bpy.types.Object: object
    """
    coords = (x, y)

    # check if there is an object under the mouse.
    hit, location, normal, rotation, face_index, hit_obj, matrix = mouse_raycast(context, coords)

    # if we've not hit an object we'll spawn on an imaginary plane at z = 0
    if not hit:
        hit, location, normal, rotation, face_index, hit_obj, matrix = floor_raycast(context, coords)

    # deselect any currently selected objects
    for obj in context.selected_objects:
        obj.select_set(False)

    obj = append_object(context, asset)

    # set object location and rotation to hit point
    obj.location = location
    obj.rotation_euler = rotation

    # select and activate spawned object
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    # push an undo action to the stack
    bpy.ops.ed.undo_push()

    return obj


def spawn_collection(context, asset, x, y):
    """Spawn a collection at the cursor based on the passed in asset description.

    Args:
        context (bpy.context): context
        asset (dict): MakeTile asset description
        x (float): mouse x
        y (float): mouse y

    Returns:
        bpy.types.Collection: collection
    """
    coords = (x, y)

    # check if there is an object under the mouse.
    hit, location, normal, rotation, face_index, hit_obj, matrix = mouse_raycast(context, coords)

    # if we've not hit an object we'll spawn on an imaginary plane at z = 0
    if not hit:
        hit, location, normal, rotation, face_index, hit_obj, matrix = floor_raycast(context, coords)

    # deselect any currently selected objects
    for obj in context.selected_objects:
        obj.select_set(False)

    collection, root_object = append_collection(context, asset)

    if not collection:
        return None

    # select the root object
    context.view_layer.objects.active = root_object
    root_object.select_set(True)

    context.view_layer.update()

    # set root object location and rotation to hit point
    root_object.location = location
    root_object.rotation_euler = rotation

    # push an undo action to the stack
    bpy.ops.ed.undo_push()

    return collection

def spawn_material(context, asset, x, y):
    """Spawns a material into the scene and adds it to the object under the cursor.

    Args:
        context (bpy.context): context
        asset (dict): MakeTile asset description
        x (float): mouse x
        y (float): mouse y

    Returns:
        bpy.types.Material: material
    """
    coords = (x, y)
    mat = append_material(context, asset)

    if not mat:
        return None

    # check if there is an object under the mouse.
    hit, location, normal, rotation, face_index, hit_obj, matrix = mouse_raycast(context, coords)

    if hit:
        # face_index returned by mouse_raycast is the index of the face of the evaluated object
        depsgraph = context.evaluated_depsgraph_get()
        # get evaluated object
        object_eval = hit_obj.evaluated_get(depsgraph)
        mesh_from_eval = object_eval.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)
        face = mesh_from_eval.polygons[face_index]
        # exclude displacement mod vert group
        try:
            excluded = hit_obj.vertex_groups['disp_mod_vert_group'].index
        except KeyError:
            excluded = None

        vertex_group = find_vertex_group_of_face(face, mesh_from_eval, [excluded])

        if vertex_group:
            # ensure object already has at least one material slot so appended material
            # is only added to vertex group
            if len(hit_obj.material_slots) == 0:
                hit_obj.data.materials.append(None)
            # append material
            hit_obj.data.materials.append(mat)
            # assign material to vertex group
            assign_mat_to_vert_group(vertex_group, hit_obj, mat)
        else:
            # append material
            hit_obj.data.materials.append(mat)

        # push an undo action to the stack
        bpy.ops.ed.undo_push()
    return mat
