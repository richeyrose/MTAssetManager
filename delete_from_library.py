import os
import json
import bpy
from bpy.types import Operator
from bpy.props import StringProperty, PointerProperty, BoolProperty
from .preferences import get_prefs


class MT_OT_AM_Delete_Selected_Assets_from_Library(Operator):
    """Operator that deletes all assets selected in the asset bar from the MakeTile library and optionally from disk."""

    bl_idname = "object.delete_selected_assets_from_library"
    bl_label = "Delete Selected Assets"
    bl_description = "deletes all assets selected in the asset bar from the MakeTile library and optionally from disk"

    delete_from_disk: BoolProperty(
        name="Also Delete From Disk?",
        default=False)

    def __init__(self):
        props = bpy.context.scene.mt_am_props
        self.assets = [asset for asset in props.asset_bar.assets if asset.selected]

    @classmethod
    def poll(cls, context):
        props = bpy.context.scene.mt_am_props
        selected_assets = [asset for asset in props.asset_bar.assets if asset.selected]
        return len(selected_assets) > 0

    def execute(self, context):
        prefs = get_prefs()
        props = bpy.context.scene.mt_am_props
        # get in memory list of asset_descs
        asset_descs = getattr(props, self.assets[0].asset_desc["Type"].lower())

        for asset in self.assets:
            # remove item from in memory list
            asset_descs.remove(asset.asset_desc)
            # delete preview image
            if os.path.exists(asset.asset_desc["PreviewImagePath"]):
                os.remove(asset.asset_desc["PreviewImagePath"])
            # delete asset file
            if self.delete_from_disk:
                if os.path.exists(asset.asset_desc["FilePath"]):
                    os.remove(asset.asset_desc["FilePath"])

        # overwrite .json file with modified list
        json_file = os.path.join(
            prefs.user_assets_path,
            "data",
            self.assets[0].asset_desc["Type"].lower() + ".json")

        if os.path.exists(json_file):
            with open(json_file, "w") as write_file:
                json.dump(asset_descs, write_file, indent=4)
        else:
            os.makedirs(json_file)
            with open(json_file, "w") as write_file:
                json.dump(asset_descs, write_file, indent=4)

        props.assets_updated = True

        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        props = context.scene.mt_am_props
        layout = self.layout
        layout.label(text="Delete " + str(len(self.assets)) + " Assets?")
        layout.label(text="Warning! Cannot be Undone!")
        layout.prop(self, 'delete_from_disk')


class MT_OT_AM_Delete_Asset_from_Library(Operator):
    """Operator that deletes asset from MakeTile library and optionally from disk."""
    bl_idname = "object.delete_asset_from_library"
    bl_label = "Delete Asset from Library"
    bl_description = "Deletes asset from the MakeTile Library and optionally from disk"

    delete_from_disk: BoolProperty(
        name="Also Delete From Disk?",
        default=False)

    def execute(self, context):
        prefs = get_prefs()
        props = context.scene.mt_am_props
        asset_desc = props.current_asset_desc

        # get in memory list of asset_descs
        asset_descs = getattr(props, asset_desc["Type"].lower())

        # remove item from in memory list
        asset_descs.remove(asset_desc)

        # overwrite .json file with modified list
        json_file = os.path.join(
            prefs.user_assets_path,
            "data",
            asset_desc["Type"].lower() + ".json")

        if os.path.exists(json_file):
            with open(json_file, "w") as write_file:
                json.dump(asset_descs, write_file, indent=4)
        else:
            os.makedirs(json_file)
            with open(json_file, "w") as write_file:
                json.dump(asset_descs, write_file, indent=4)

        # delete preview image
        if os.path.exists(asset_desc["PreviewImagePath"]):
            os.remove(asset_desc["PreviewImagePath"])

        # delete asset file
        if self.delete_from_disk:
            if os.path.exists(asset_desc["FilePath"]):
                os.remove(asset_desc["FilePath"])

        # raise flag to update asset bar
        props.assets_updated = True

        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        props = context.scene.mt_am_props
        layout = self.layout
        layout.label(text="Delete " + props.current_asset_desc['Name'] + "?")
        layout.label(text="Warning! Cannot be Undone!")
        layout.prop(self, 'delete_from_disk')
