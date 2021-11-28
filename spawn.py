import bpy
from .raycast import mouse_raycast, floor_raycast
from .utils import find_vertex_group_of_face, assign_mat_to_vert_group, material_is_unique

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

# TODO spawn_material this is a bit inelegent as we could check if material is in scene earlier.
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

    # fuck knows why this works while make_local on the original doesn't.
    if mat.library:
        mat = mat.copy()
        mat = mat.make_local()
    
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
                    hit_obj.data.materials.append(mat)
        # push an undo action to the stack
        bpy.ops.ed.undo_push()
    return mat


def append_material(context, filepath, asset_name):
    """Append material. Checks to see if material already exists in scene.

    Args:
        context (bpy.context): context
        filepath (str): filepath to library file containing material
        asset_name (str): name of material

    Returns:
        bpy.types.Material: material
    """
    with bpy.data.libraries.load(filepath) as (data_from, data_to):
        data_to.materials = [asset_name]

    imported_mat = data_to.materials[0]

    # check if material is unique
    materials = [material for material in bpy.data.materials if material != imported_mat]
    unique, matched_material = material_is_unique(imported_mat, materials)

    # if not unique remove newly added material and return original material
    if not unique:
        bpy.data.materials.remove(imported_mat)
        context.scene.mt_am_props.assets_updated = True
        return matched_material
    
    context.scene.mt_am_props.assets_updated = True
    return imported_mat

def append_asset(context, asset, asset_type='object', link=False):
    """Append asset to the scene.

    Args:
        context (bpy.context): context
        asset (dict): MakeTile asset
        asset_type (str): string in ['object', 'collection', 'material']. Defaults to 'object'
        link (bool, optional): Whether to link or append asset. Defaults to False.

    Returns:
        bpy.types.Object, Collection or Material: asset
    """
    asset = asset.asset

    if not link:
        lib = asset.library
        filepath = lib.filepath
        name = asset.name

        # unlink existing library file so we can relink in append mode
        bpy.data.libraries.remove(lib)

        if asset_type == 'material':
            return append_material(context, filepath, name)

        # used to ensure we only append unique materials
        existing_mats = [m.name for m in bpy.data.materials if not m.library]

        # used to ensure we set add a fake user on secondary objects, like those referred
        # to in modifiers, if they are added to the scene. If we don't do this then when
        # we resave an object it won't save the associated objects (as of 2.82a)
        existing_obs = bpy.data.objects.keys()

        if asset_type == 'object':
            with bpy.data.libraries.load(filepath, assets_only=True, link=False) as (data_from, data_to):
                data_to.objects = [name]
            asset = data_to.objects[0]
            context.collection.objects.link(asset)

        elif asset_type == 'collection':
            with bpy.data.libraries.load(filepath, assets_only=True, link=False) as (data_from, data_to):
                data_to.collections = [name]
            asset = data_to.collections[0]
            context.scene.collection.children.link(asset)

        # we now need to find what OTHER objects have been added as a side effect
        updated_obs = bpy.data.objects.keys()

        new_obs = (set(existing_obs) | set(updated_obs)) - (set(existing_obs) & set(updated_obs))

        # set a fake user for our secondary objects
        for ob_name in new_obs:
            ob = bpy.data.objects[ob_name]
            ob.use_fake_user = True

        # get a set of new materials that were added on import
        updated_mats = [m.name for m in bpy.data.materials if not m.library]
        new_mats = (set(existing_mats) | set(updated_mats)) - (set(existing_mats) & set(updated_mats))

        # check if newly added materials are unique
        for mat in new_mats:
            materials = [m for m in bpy.data.materials if mat != m.name and not m.library]
            unique, matched_material = material_is_unique(bpy.data.materials[mat], materials)
            if not unique:
                for ob_name in new_obs:
                    for slot in bpy.data.objects[ob_name].material_slots:
                        #TODO Work out why this fails sometimes on Rectangular floors
                        try:
                            if slot.material.name == mat:
                                slot.material = matched_material
                        except AttributeError:
                            pass

                # remove duplicate material
                bpy.data.materials.remove(bpy.data.materials[mat])

        # reinitialise asset bar
        context.scene.mt_am_props.assets_updated = True
        return asset
    return None



