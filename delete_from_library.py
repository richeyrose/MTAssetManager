import os
import json
import bpy
from bpy.types import Operator
from bpy.props import BoolProperty
from .preferences import get_prefs


class MT_OT_AM_Delete_Selected_Assets_from_Library(Operator):
    """Delete all selected assets from the MakeTile library and optionally from disk."""

    bl_idname = "object.delete_selected_assets_from_library"
    bl_label = "Delete Selected Assets"
    bl_description = "Delete all selected assets from the MakeTile library and optionally from disk."

    delete_from_disk: BoolProperty(
        name="Also Delete From Disk?",
        default=False)

    def __init__(self):
        props = bpy.context.scene.mt_am_props
        self.selected_assets = [asset.asset_desc for asset in props.asset_bar.assets if asset.selected]

    @classmethod
    def poll(cls, context):
        props = context.scene.mt_am_props
        selected_assets = [asset for asset in props.asset_bar.assets if asset.selected]
        return len(selected_assets) > 0

    def execute(self, context):
        prefs = get_prefs()
        props = context.scene.mt_am_props
        # get in memory list of asset_descs
        asset_type = self.selected_assets[0]["Type"].lower()
        delete_assets(self.selected_assets, prefs, props, asset_type, self.delete_from_disk)

        props.assets_updated = True

        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        props = context.scene.mt_am_props
        layout = self.layout
        layout.label(text="Delete " + str(len(self.selected_assets)) + " Assets?")
        layout.label(text="Warning! Cannot be Undone!")
        layout.prop(self, 'delete_from_disk')


def delete_assets(selected_assets, prefs, props, asset_type, delete_from_disk=True):
    """Delete the selected assets.

    Args:
        selected_assets (list[asset_descriptions]): list of MakeTile asset descriptions
        prefs (dict): Asset manager prefs
        props (dict): Asset manager props
        asset_type (ENUM in {'objects', 'collections', 'materials'}): asset type
        delete_from_disk (bool, optional): Delete .blend file containing asset from disk? Defaults to True.
    """
    asset_descs = getattr(props, asset_type)
    for asset in selected_assets:
        # remove item from in memory list
        asset_descs.remove(asset)
        # delete preview image
        if os.path.exists(asset["PreviewImagePath"]):
            os.remove(asset["PreviewImagePath"])
        # delete asset file
        if delete_from_disk:
            if os.path.exists(asset["FilePath"]):
                os.remove(asset["FilePath"])

    # overwrite .json file with modified list
    json_file = os.path.join(
        prefs.user_assets_path,
        "data",
        asset_type + ".json")

    if os.path.exists(json_file):
        with open(json_file, "w") as write_file:
            json.dump(asset_descs, write_file, indent=4)
    else:
        os.makedirs(json_file)
        with open(json_file, "w") as write_file:
            json.dump(asset_descs, write_file, indent=4)