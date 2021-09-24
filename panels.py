import bpy
import os
from bpy.types import Panel
from .categories import load_categories
from .preferences import get_prefs
from bpy_extras import (
    asset_utils,
)

class ASSETBROWSER_PT_custom_name(asset_utils.AssetMetaDataPanel, Panel):
    bl_label = "MakeTile Properties"
    bl_space_type = "FILE_BROWSER"
    bl_region_type = 'TOOL_PROPS'
    bl_description = "Display custom MakeTile asset properties"

    def draw(self, context):
        layout=self.layout
        active_asset = asset_utils.SpaceAssetInfo.get_active_asset(context)

        if active_asset:
            layout.prop(active_asset, 'mt_author')
            layout.prop(active_asset, 'mt_license')
            layout.prop(active_asset, 'mt_URI')

class MT_PT_AM_Main_Panel(Panel):
    """Asset N Menu UI panel."""

    bl_category = "Asset Manager"
    bl_idname = "MT_PT_AM_Main_Panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_label = "Assets"

    def draw(self, context):
        props = context.scene.mt_am_props
        layout = self.layout
        child_cats = []

        layout.label(text="Library")
        layout.prop(props, 'library_path', text="")

        if not props.asset_bar:
            op = layout.operator("view3d.mt_asset_bar")
            op.current_path = props.current_path
        else:
            layout.operator("view3d.mt_hide_asset_bar")

        # display return to parent button if we're not in the library root
        if not os.path.samefile(props.current_path, props.library_path):
            op = layout.operator(
                'view3d.mt_ret_to_parent',
                text=os.path.basename(props.parent_path),
                icon='FILE_PARENT')

        # get list of subfolders
        try:
            child_cats = [f.path for f in os.scandir(props.current_path) if f.is_dir()]
        except FileNotFoundError:
            child_cats = [f.path for f in os.scandir(props.library_path) if f.is_dir()]

        row = layout.row()
        row.label(text='Subfolders')
        row.operator('scene.mt_am_add_subfolder', text="", icon='ADD')

        for cat in child_cats:
            row = layout.row()
            op = row.operator(
                "view3d.mt_asset_bar",
                text=os.path.basename(cat),
                icon="FILE_FOLDER")
            op.current_path = cat

            del_op = row.operator("scene.mt_am_delete_subfolder", text="", icon="REMOVE")
            del_op.folder_name = cat
