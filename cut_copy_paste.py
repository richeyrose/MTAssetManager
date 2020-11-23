import os
import json
import bpy
import copy

from .preferences import get_prefs
from bpy.types import Operator

class MT_OT_AM_Cut_Asset(Operator):
    bl_idname = "object.mt_cut_asset"
    bl_label = "Cut Asset"
    bl_description = "Cut Asset"

    def execute(self, context):
        props = context.scene.mt_am_props
        props.cut = True
        props.copied_asset = props.current_asset_desc
        return {'FINISHED'}


class MT_OT_AM_Copy_Asset(Operator):
    bl_idname = "object.mt_copy_asset"
    bl_label = "Copy Asset"
    bl_description = "Copy Asset"

    def execute(self, context):
        props = context.scene.mt_am_props
        props.cut = False
        props.copied_asset = props.current_asset_desc
        return {'FINISHED'}


class MT_OT_AM_Paste_Asset(Operator):
    bl_idname = "object.mt_paste_asset"
    bl_label = "Paste Asset"
    bl_description = "Paste Asset"

    @classmethod
    def poll(cls, context):
        props = context.scene.mt_am_props
        if props.copied_asset:
            if props.copied_asset["Type"] == props.active_category["Contains"] and props.copied_asset["Category"] != props.active_category["Slug"]:
                return True

    def execute(self, context):
        prefs = get_prefs()
        props = context.scene.mt_am_props
        orig_asset = props.copied_asset
        active_category = props.active_category

        # get in memory list of asset descs
        asset_descs = getattr(props, orig_asset["Type"].lower())

        if props.cut:
            for asset in asset_descs:
                if asset == orig_asset:
                    asset["Category"] = active_category["Slug"]
                    break
        else:
            new_asset = copy.deepcopy(orig_asset)
            new_asset["Category"] = active_category["Slug"]
            asset_descs.append(new_asset)

        # overwrite .json file with modified list
        json_file = os.path.join(
            prefs.user_assets_path,
            "data",
            orig_asset["Type"].lower() + ".json")

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
