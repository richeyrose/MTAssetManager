import os
import bpy
from .raycast import mouse_raycast, floor_raycast
from .utils import material_is_unique, find_vertex_group_of_face, assign_mat_to_vert_group, get_material_index


def spawn_object(self, context, asset, x, y, op):
    coords = (x, y)
    obj = append_object(context, asset, op)

    if not obj:
        op.report({'WARNING'}, "Asset not found!")
        return False

    # check if there is an object under the mouse.
    hit, location, normal, rotation, face_index, hit_obj, matrix = mouse_raycast(context, coords)

    # if we've not hit an object we'll spawn on an imaginary plane at z = 0
    if not hit:
        hit, location, normal, rotation, face_index, hit_obj, matrix = floor_raycast(context, coords)

    # set object location and rotation to hit point
    obj.location = location
    obj.rotation_euler = rotation

    # deselect any currently selected objects
    for obj in context.selected_objects:
        obj.select_set(False)

    # select and activate spawned object
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    # push an undo action to the stack
    bpy.ops.ed.undo_push()


def spawn_collection(self, context, asset, x, y, op):
    coords = (x, y)
    collection, root_object = append_collection(context, asset, op)

    if not collection:
        op.report({'WARNING'}, "Asset not found!")
        return False

    # check if there is an object under the mouse.
    hit, location, normal, rotation, face_index, hit_obj, matrix = mouse_raycast(context, coords)

    # if we've not hit an object we'll spawn on an imaginary plane at z = 0
    if not hit:
        hit, location, normal, rotation, face_index, hit_obj, matrix = floor_raycast(context, coords)

    # deselect any currently selected objects
    for obj in context.selected_objects:
        obj.select_set(False)

    # select the root object
    bpy.context.view_layer.objects.active = root_object
    root_object.select_set(True)

    # set root object location and rotation to hit point
    root_object.location = location
    root_object.rotation_euler = rotation

    # push an undo action to the stack
    bpy.ops.ed.undo_push()


def spawn_material(self, context, asset, x, y, op):
    coords = (x, y)
    mat = append_material(context, asset, op)

    if not mat:
        op.report({'WARNING'}, "Asset not found!")
        return False

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


def append_material(context, asset, op, link=False):
    """Append material to scene.
    Checks if material is unique before appending and if not returns original material

    Args:
        context (bpy.context): context
        asset (dict): asset description
        link (bool, optional): Link or append material. Defaults to False.

    Returns:
        bpy.types.Material: Material
    """
    filepath = asset['FilePath']

    if os.path.exists(filepath) and os.path.isfile(filepath):
        asset_found = False
        # load asset
        with bpy.data.libraries.load(filepath) as (data_from, data_to):
            if asset['Slug'] in data_from.materials:
                data_to.materials = [asset['Slug']]
                asset_found = True

        imported_mat = data_to.materials[0]
        imported_mat.name = asset["Name"]  # rename material to use pretty name

        if asset_found:
            # check if material is unique
            materials = [material for material in bpy.data.materials if material != imported_mat]
            unique, matched_material = material_is_unique(imported_mat, materials)

            # if not unique remove newly added material and return original material
            if not unique:
                bpy.data.materials.remove(imported_mat)
                return matched_material

            return imported_mat

    return False

def append_object(context, asset, op, link=False):
    filepath = asset["FilePath"]

    # used to ensure we only add unique materials
    existing_mats = bpy.data.materials.keys()

    # used to ensure we set add a fake user on secondary objects, like those referred
    # to in modifiers, if they are added to the scene. If we don't do this then when
    # we resave an object it won't save the associated objects (as of 2.82a)
    existing_obs = bpy.data.objects.keys()

    if os.path.exists(filepath) and os.path.isfile(filepath):
        asset_found = False
        # load asset
        with bpy.data.libraries.load(filepath, link=link) as (data_from, data_to):
            if asset['Slug'] in data_from.objects:
                data_to.objects = [asset['Slug']]
                asset_found = True

        if asset_found:
            # the object that corresponds to the asset['Slug']
            obj = data_to.objects[0]

            # link our imported object to current collection
            context.collection.objects.link(obj)

            # we now need to find what OTHER objects have been added as a side effect
            updated_obs = bpy.data.objects.keys()
            new_obs = (set(existing_obs) | set(updated_obs)) - (set(existing_obs) & set(updated_obs))

            # set a fake user for our secondary objects
            for ob_name in new_obs:
                ob = bpy.data.objects[ob_name]
                # TODO We can probably get rid of this check and just make sure every new object
                # has a fake user
                if ob != obj:
                    ob.use_fake_user = True

            # get a set of new materials that were added on import
            updated_mats = bpy.data.materials.keys()
            new_mats = (set(existing_mats) | set(updated_mats)) - (set(existing_mats) & set(updated_mats))

            # check if newly added materials are unique
            for mat in new_mats:
                materials = [material for material in bpy.data.materials if mat != material]
                unique, matched_material = material_is_unique(bpy.data.materials[mat], materials)

                # if not unique replace with matched material
                if not unique:
                    for slot in obj.material_slots:
                        if slot.material.name == mat:
                            slot.material = matched_material

                    # remove duplicate material
                    bpy.data.materials.remove(bpy.data.materials[mat])

            # rename object to pretty name
            obj.name = asset["Name"]

            op.report({'INFO'}, obj.name + ' added to scene.')

            return obj

    return False


def append_collection(context, asset, op, link=False):
    filepath = asset["FilePath"]
    # used to ensure we only add unique materials
    existing_mats = bpy.data.materials.keys()

    # used to ensure we set add a fake user on secondary objects, like those referred
    # to in modifiers, if they are added to the scene. If we don't do this then when
    # we resave an object it won't save the associated objects (as of 2.82a)
    existing_obs = bpy.data.objects.keys()

    if os.path.exists(filepath) and os.path.isfile(filepath):
        asset_found = False

        # load asset
        with bpy.data.libraries.load(filepath, link=link) as (data_from, data_to):
            if asset['Slug'] in data_from.collections:
                data_to.collections = [asset['Slug']]
                if asset['RootObject'] in data_from.objects:
                    data_to.objects = [asset['RootObject']]
                asset_found = True

        if asset_found:
            # the collection that corresponds to the asset['Slug']
            collection = data_to.collections[0]
            root_object = data_to.objects[0]

            # link collection to scene
            context.scene.collection.children.link(collection)

            # we need to ensure that any other objects that have been added as a side
            # effect have a fake user set otherwise things start breaking when we resave
            # objects and collection
            updated_obs = bpy.data.objects.keys()

            new_obs = (set(existing_obs) | set(updated_obs)) - (set(existing_obs) & set(updated_obs))
            for ob_name in new_obs:
                ob = bpy.data.objects[ob_name]
                ob.use_fake_user = True

            # get a set of new materials that were added on import
            updated_mats = bpy.data.materials.keys()
            new_mats = (set(existing_mats) | set(updated_mats)) - (set(existing_mats) & set(updated_mats))

            # check if newly added materials are unique
            for mat in new_mats:
                materials = [material for material in bpy.data.materials if mat != material]
                unique, matched_material = material_is_unique(bpy.data.materials[mat], materials)

                # if not unique replace with matched material
                if not unique:
                    for obj in new_obs:
                        for slot in obj.material_slots:
                            if slot.material.name == mat:
                                slot.material = matched_material

                    # remove duplicate material
                    bpy.data.materials.remove(bpy.data.materials[mat])

            # rename collection to pretty name
            collection.name = asset["Name"]
            op.report({'INFO'}, collection.name + ' added to scene.')
            return collection, root_object
    return





