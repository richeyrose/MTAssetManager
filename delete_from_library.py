import os
import json
import bpy
from bpy.types import Operator
from bpy.props import BoolProperty
from .preferences import get_prefs
from .lib.send2trash import send2trash


class MT_OT_AM_Delete_Selected_Assets_from_Library(Operator):
    """Delete all selected assets."""

    bl_idname = "object.delete_selected_assets_from_library"
    bl_label = "Delete Selected Assets"
    bl_description = "Delete all selected assets."

    def __init__(self):
        props = bpy.context.scene.mt_am_props
        self.selected_assets = [asset for asset in props.asset_bar.assets if asset.selected]

    @classmethod
    def poll(cls, context):
        props = context.scene.mt_am_props
        selected_assets = [asset for asset in props.asset_bar.assets if asset.selected]
        return len(selected_assets) > 0

    def execute(self, context):
        props = context.scene.mt_am_props

        for asset in self.selected_assets:
            name =asset.asset.name
            lib = asset.asset.library
            filepath = lib.filepath
            if os.path.isfile(filepath):
                try:
                    bpy.data.libraries.remove(asset.asset.library)
                    send2trash(filepath)
                    self.report({'INFO'}, name + ' deleted.')
                except OSError as err:
                    self.report({'INFO'}, str(err))
                    return {'CANCELLED'}

        props.assets_updated = True

        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        """Draw modal pop up."""
        layout = self.layout
        layout.label(text="Delete " + str(len(self.selected_assets)) + " Assets?")
        layout.label(text="Warning this will delete both the assets and the file!")
