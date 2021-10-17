import bpy
from .utils import material_is_unique

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

        # used to ensure we only add unique materials
        existing_mats = bpy.data.materials.keys()

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
        updated_mats = bpy.data.materials.keys()
        new_mats = (set(existing_mats) | set(updated_mats)) - (set(existing_mats) & set(updated_mats))

        # check if newly added materials are unique
        for mat in new_mats:
            materials = [material for material in bpy.data.materials if mat != material]
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
