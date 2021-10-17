import bpy
from .raycast import mouse_raycast, floor_raycast
from .utils import find_vertex_group_of_face, assign_mat_to_vert_group
from .append import append_asset

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

    obj = append_asset(context, asset)

    # set object location and rotation to hit point
    obj.location = location
    obj.rotation_euler = rotation

    # select and activate spawned object
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    # push an undo action to the stack
    bpy.ops.ed.undo_push()

    return True


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

    #collection, root_object = append_collection(context, asset)
    try:
        #collection = append_collection(context, asset)
        collection = append_asset(context, asset, 'collection')
    except ReferenceError:
        print('Append Collection Failed')
        return None

    # select the root object
    #context.view_layer.objects.active = root_object
    #root_object.select_set(True)

    context.view_layer.update()

    # get objects with no parents in collection
    orphans = [obj for obj in collection.objects if not obj.parent]

    # if there is more than one orphan objects in the collection create a temporary empty and parent the orphans to it
    if len(orphans) > 1:
        empty = bpy.data.objects.new(collection.name + '_root', None)
        collection.objects.link(empty)

        # parent orphans to root_obj
        for orphan in orphans:
            orphan.parent = empty
            orphan.matrix_parent_inverse = empty.matrix_world.inverted

        # set root location and rotation
        empty.location = location
        empty.rotation_euler = rotation

        # update view_layer to ensure changes are registered
        context.view_layer.update()

        # apply transformation
        for orphan in orphans:
            matrixcopy = orphan.matrix_world.copy()
            orphan.parent = None
            orphan.matrix_world = matrixcopy

        # remove temporary empty
        bpy.data.objects.remove(empty)

    # otherwise set the root object loc and rot
    else:
        for orphan in orphans:
            orphan.location = location
            orphan.rotation_euler = rotation

    # push an undo action to the stack
    bpy.ops.ed.undo_push()

    return collection

#TODO change so replaces material where there is no vertex group rather than just add it to list
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
    mat = append_asset(context, asset, 'material')

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
            if mat.name not in hit_obj.data.materials:
                # if there is 1 material slot fill it with our appended material and add a new mat slot with old material
                if len(hit_obj.material_slots) == 1:
                    old_mat = hit_obj.material_slots[0].material
                    hit_obj.material_slots[0].material = mat
                    hit_obj.data.materials.append(old_mat)
                else:
                    # just append material
                    hit_obj.data.materials.append(mat)
        # push an undo action to the stack
        bpy.ops.ed.undo_push()
    return mat
