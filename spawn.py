import os
import bpy
from mathutils import kdtree
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

def spawn_collection(self, context, asset, x, y, op):
    pass

def spawn_material(self, context, asset, x, y, op):
    coords = (x, y)
    mat = append_material(context, asset, op)

    if not mat:
        op.report({'WARNING'}, "Asset not found!")
        return False

    # check if there is an object under the mouse.
    hit, location, normal, rotation, face_index, hit_obj, matrix = mouse_raycast(context, coords)

    if hit:
        # face_index returned by mouse_raycast is the index of the face of the evaluated object (i.e. object after all modifiers etc. have been applied)
        # so we need to use KDTree to get the face of the original object whose center is closest to the hit location
        mesh = hit_obj.data
        size = len(mesh.polygons)
        kd = kdtree.KDTree(size)
        for i, p in enumerate(mesh.polygons):
            kd.insert(p.center, i)
        kd.balance()

        # find the closest face to the hit location
        co_find = (location)
        co, index, dist = kd.find(co_find)
        face = hit_obj.data.polygons[index]

        # find vertex group that face belongs to
        vertex_group = find_vertex_group_of_face(face, hit_obj)

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
            material_index = get_material_index(hit_obj, mat)

            # assign material to entire object
            for poly in mesh.polygons:
                poly.material_index = material_index

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
            if asset['Name'] in data_from.materials:
                data_to.materials = [asset['Name']]
                asset_found = True

        if asset_found:
            # check if material is unique
            materials = [material for material in bpy.data.materials if material != data_to.materials[0]]
            unique, matched_material = material_is_unique(data_to.materials[0], materials)

            # if not unique remove newly added material and return original material
            if not unique:
                bpy.data.materials.remove(data_to.materials[0])
                op.report({'INFO'}, 'Already exists. Nothing added.')
                return matched_material

            op.report({'INFO'}, data_to.materials[0].name + ' added to scene.')
            return data_to.materials[0]

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
            if asset['Name'] in data_from.objects:
                data_to.objects = [asset['Name']]
                asset_found = True

        if asset_found:
            obj = data_to.objects[0]  # the object that corresponds to the asset['Name']

            # link our imported object to current collection
            context.collection.objects.link(obj)

            # we now need to find what OTHER objects have been added as a side effect
            updated_obs = bpy.data.objects.keys()
            new_obs = (set(existing_obs) | set(updated_obs)) - (set(existing_obs) & set(updated_obs))

            # set a fake user for our secondary objects
            for ob_name in new_obs:
                ob = bpy.data.objects[ob_name]
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

            op.report({'INFO'}, obj.name + ' added to scene.')

            return obj

    return False

