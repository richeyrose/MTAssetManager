import os
import json
from copy import deepcopy
from shutil import copy2

import bpy
from .preferences import get_prefs
from bpy.types import Operator
from .utils import find_and_rename
from .append import append_collection, append_material, append_object

# TODO: #7 fix copy asset for collections
class MT_OT_AM_Cut_Asset(Operator):
    """Cut an asset in the asset bar."""
    bl_idname = "object.mt_cut_asset"
    bl_label = "Cut Asset"
    bl_description = "Cut Asset"

    def execute(self, context):
        props = context.scene.mt_am_props
        props.cut = True
        props.copied_assets = [asset.asset_desc for asset in props.asset_bar.assets if asset.selected]
        return {'FINISHED'}


class MT_OT_AM_Copy_Asset(Operator):
    """Copy an asset in the asset bar."""
    bl_idname = "object.mt_copy_asset"
    bl_label = "Copy Asset"
    bl_description = "Copy Asset"

    def execute(self, context):
        props = context.scene.mt_am_props
        props.cut = False
        props.copied_assets = [asset.asset_desc for asset in props.asset_bar.assets if asset.selected]
        return {'FINISHED'}


class MT_OT_AM_Paste_Asset(Operator):
    """Paste an asset in the asset bar."""
    bl_idname = "object.mt_paste_asset"
    bl_label = "Paste Asset"
    bl_description = "Paste Asset"

    @classmethod
    def poll(cls, context):
        props = context.scene.mt_am_props
        if props.copied_assets and props.copied_assets[0]["Type"] == props.active_category["Contains"]:
            return True

    def execute(self, context):
        prefs = get_prefs()
        props = context.scene.mt_am_props
        copied_asset_descs = props.copied_assets
        asset_type = copied_asset_descs[0]["Type"]
        active_category = props.active_category

        # get in memory list of asset descs
        asset_descs = getattr(props, asset_type.lower())

        # cut is simple. We just change the category in the asset description and update the .json
        if props.cut:
            for asset in asset_descs:
                if asset in copied_asset_descs:
                    asset["Category"] = active_category["Slug"]

        # copy is more complex as we need to duplicate the actual asset
        else:
            for asset_desc in copied_asset_descs:
                if asset_type == "OBJECTS":
                    # copy asset desc and update it so it has unique slug
                    new_asset_desc = self.copy_asset_desc_and_make_unique(props, asset_desc, prefs, asset_type, active_category["Slug"])
                    asset_descs.append(new_asset_desc)

                    # load asset into Blender
                    asset = append_object(context, asset_desc)

                    # give it a unique slug
                    asset.name = new_asset_desc["Slug"]

                    # save asset to a new library file
                    bpy.data.libraries.write(
                        new_asset_desc["FilePath"],
                        {asset},
                        fake_user=True)

                    # copy image file
                    copy2(asset_desc["PreviewImagePath"], new_asset_desc["PreviewImagePath"])

                    # cleanup
                    bpy.data.objects.remove(asset)

                elif asset_type == "COLLECTIONS":
                    new_asset_desc = self.copy_asset_desc_and_make_unique(props, asset_desc, prefs, asset_type, active_category["Slug"])
                    asset_descs.append(new_asset_desc)
                    ret = append_collection(context, asset_desc)
                    asset = ret[0]
                    asset.name = new_asset_desc["Slug"]
                    bpy.data.libraries.write(
                        new_asset_desc["FilePath"],
                        {asset},
                        fake_user=True)
                    copy2(asset_desc["PreviewImagePath"], new_asset_desc["PreviewImagePath"])
                    bpy.data.collections.remove(asset)
                else:
                    new_asset_desc = self.copy_asset_desc_and_make_unique(props, asset_desc, prefs, asset_type, active_category["Slug"])
                    asset_descs.append(new_asset_desc)
                    asset = append_material(context, asset_desc)
                    asset.name = new_asset_desc["Slug"]
                    bpy.data.libraries.write(
                        new_asset_desc["FilePath"],
                        {asset},
                        fake_user=True)
                    copy2(asset_desc["PreviewImagePath"], new_asset_desc["PreviewImagePath"])
                    bpy.data.materials.remove(asset)

        # overwrite .json file with modified list
        json_file = os.path.join(
            prefs.user_assets_path,
            "data",
            asset_type.lower() + ".json")

        if os.path.exists(json_file):
            with open(json_file, "w") as write_file:
                json.dump(asset_descs, write_file, indent=4)
        else:
            os.makedirs(json_file)
            with open(json_file, "w") as write_file:
                json.dump(asset_descs, write_file, indent=4)

        # raise flag to update asset bar
        props.assets_updated = True

        return {'FINISHED'}

    def copy_asset_desc_and_make_unique(self, props, asset_desc, prefs, asset_type, cat_slug):
        """Copy the passed in asset description and updates its slug and other items to make it unique.

        Args:
            asset_desc (dict): NakeTile asset description
            prefs (dict): Asset manager prefs
            asset_type (Enum in {OBJECTS, COLLECTIONS, MATERIALS}): asset type
            cat_slug (string): Category slug asset belongs to

        Returns:
            dict: Asset description.
        """
        # get in memory list of asset descs
        asset_descs = getattr(props, asset_type.lower())

        # get slugs
        current_slugs = [desc['Slug'] for desc in asset_descs]

        # get a new unique slug for the asset
        new_slug = find_and_rename(asset_desc["Slug"], current_slugs)

        # get assets path
        assets_path = os.path.join(
            prefs.user_assets_path,
            asset_type.lower())

        # create deep copy of asset desc
        new_asset_desc = deepcopy(asset_desc)

        # update asset desc
        new_asset_desc["Category"] = cat_slug
        new_asset_desc["Slug"] = new_slug
        new_asset_desc["FileName"] = new_slug + '.blend'
        new_asset_desc["FilePath"] = os.path.join(assets_path, new_slug + '.blend')
        new_asset_desc["PreviewImagePath"] = os.path.join(assets_path, new_slug + '.png')
        new_asset_desc["PreviewImageName"] = new_slug + '.png'

        return new_asset_desc
