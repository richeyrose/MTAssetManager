import os
import bpy
from .raycast import mouse_raycast, floor_raycast
from .utils import material_is_unique


def spawn_object(self, context, asset, x, y, op):
    coords = (x, y)
    obj = append_object(context, asset)
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
    pass

def append_object(context, asset, link=False):
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
            return obj

    return False

