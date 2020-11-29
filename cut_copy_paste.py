import os
import json
import bpy
import copy
from shutil import copy2

from .preferences import get_prefs
from bpy.types import Operator
from .utils import find_and_rename
from .append import append_collection, append_material, append_object

class MT_OT_AM_Cut_Asset(Operator):
    bl_idname = "object.mt_cut_asset"
    bl_label = "Cut Asset"
    bl_description = "Cut Asset"

    def execute(self, context):
        props = context.scene.mt_am_props
        props.cut = True
        props.copied_assets = [asset.asset_desc for asset in props.asset_bar.assets if asset.selected]
        return {'FINISHED'}


class MT_OT_AM_Copy_Asset(Operator):
    bl_idname = "object.mt_copy_asset"
    bl_label = "Copy Asset"
    bl_description = "Copy Asset"

    def execute(self, context):
        props = context.scene.mt_am_props
        props.cut = False
        props.copied_assets = [asset.asset_desc for asset in props.asset_bar.assets if asset.selected]
        return {'FINISHED'}


class MT_OT_AM_Paste_Asset(Operator):
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
                    new_asset_desc = self.copy_and_update_asset_desc(asset_desc, asset_descs, prefs, asset_type, active_category)
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
                    ret = append_collection(context, asset_desc)
                    asset = ret[0]
                    # bpy.data.collections.remove(asset)
                else:
                    asset = append_material(context, asset_desc)
                    # bpy.data.materials.remove(asset)

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

    def copy_and_update_asset_desc(self, asset_desc, asset_descs, prefs, asset_type, active_category):
        current_slugs = [desc['Slug'] for desc in asset_descs]

        # get a new unique slug for the asset
        new_slug = find_and_rename(asset_desc["Slug"], current_slugs)

        # get assets path
        assets_path = os.path.join(
            prefs.user_assets_path,
            asset_type.lower())

        # create deep copy of asset desc
        new_asset_desc = copy.deepcopy(asset_desc)

        # update asset desc
        new_asset_desc["Category"] = active_category["Slug"]
        new_asset_desc["Slug"] = new_slug
        new_asset_desc["FileName"] = new_slug + '.blend'
        new_asset_desc["FilePath"] = os.path.join(assets_path, new_slug + '.blend')
        new_asset_desc["PreviewImagePath"] = os.path.join(assets_path, new_slug + '.png')
        new_asset_desc["PreviewImageName"] = new_slug + '.png'

        return new_asset_desc
