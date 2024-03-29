import os
import bpy
from .utils import material_is_unique


def append_material(context, asset, link=False):
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
        with bpy.data.libraries.load(filepath, link=link) as (data_from, data_to):
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

    return None


def append_object(context, asset, link=False):
    """Append object to the scene based on passed in MakeTile Asset description.

    Args:
        context (bpy.context): context
        asset (dict): MakeTile asset description
        link (bool, optional): Whether to link or append asset. Defaults to False.

    Returns:
        bpy.types.Object: object
    """
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

            return obj

    return None


def append_collection(context, asset, link=False):
    """Append collection to scene based on passed in asset description.

    Args:
        context (bpy.context): context
        asset (dict): MakeTile Asset description
        link (bool, optional): Whether to link the collection or append it. Defaults to False.

    Returns:
        tuple (
            bpy.types.collection: collection,
            bpy.types.Object: Root object)
    """
    filepath = asset["FilePath"]

    # used to ensure we only add unique materials
    existing_mats = bpy.data.materials.keys()

    # used to ensure we set add a fake user on secondary objects, like those referred
    # to in modifiers, if they are added to the scene. If we don't do this then when
    # we resave an object it won't save the associated objects (as of 2.82a)
    existing_obs = bpy.data.objects.keys()

    asset_found = False
    if os.path.exists(filepath) and os.path.isfile(filepath):
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

            # rename collection to pretty name
            collection.name = asset["Name"]

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
            return collection, root_object
    return None
