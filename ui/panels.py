import os
import bpy
from ..utils import path_leaf
from bpy.types import Panel, Operator, PointerProperty
from bpy_extras import asset_utils

class ASSETBROWSER_PT_custom_name(asset_utils.AssetMetaDataPanel, Panel):
    bl_label = "MakeTile Properties"
    bl_space_type = "FILE_BROWSER"
    bl_region_type = 'TOOL_PROPS'
    bl_description = "Display custom MakeTile asset properties in internal asset browser"

    def draw(self, context):
        layout=self.layout
        active_asset = asset_utils.SpaceAssetInfo.get_active_asset(context)

        if active_asset:
            layout.prop(active_asset, 'mt_license')

class MT_PT_AM_Main_Panel:
    bl_category = "Asset Manager"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

class MT_PT_AM_Bar_Panel(MT_PT_AM_Main_Panel, Panel):
    bl_idname = "MT_PT_AM_Main_Panel"
    bl_description = "Panel for navigating asset bar."
    bl_label = "Assets"
    bl_order = 0

    def draw(self, context):
        props = context.scene.mt_am_props
        layout = self.layout
        subfolder = []

        # show label for current library
        layout.label(text="Current Library:")
        layout.prop(props, 'libraries', text="")

        # show / hide asset bar
        if not props.asset_bar:
            op = layout.operator("view3d.mt_asset_bar")
            op.current_path = props.current_path
        else:
            layout.operator("view3d.mt_hide_asset_bar")

        # filter by
        layout.label(text="Filter By")
        row = layout.row()
        row.prop(props, 'asset_filter', text="")

        # sort by
        layout.label(text="Sort By")
        row = layout.row()
        row.prop(props, 'asset_sort_by', text="")
        row.prop(props, 'asset_reverse_sort')

        # display return to parent button if we're not in the library root
        if not os.path.samefile(props.current_path, props.library_path):
            op = layout.operator(
                'view3d.mt_ret_to_parent',
                text=os.path.basename(props.parent_path),
                icon='FILE_PARENT')



        # get list of subfolders
        try:
            subfolder = [f.path for f in os.scandir(props.current_path) if f.is_dir()]
        except FileNotFoundError:
            subfolder = [f.path for f in os.scandir(props.library_path) if f.is_dir()]

        # subfolder row
        row = layout.row()
        row.label(text='Subfolders')

        # add subfolder link
        row.operator('scene.mt_am_add_subfolder', text="", icon='ADD')

        # display subfolder name
        for subfolder in subfolder:
            row = layout.row()
            op = row.operator(
                "view3d.mt_asset_bar",
                text=os.path.basename(subfolder),
                icon="FILE_FOLDER")
            op.current_path = subfolder

            # show delete subfolder link
            del_op = row.operator("scene.mt_am_delete_subfolder", text="", icon="REMOVE")
            del_op.folder_name = subfolder

class MT_PT_AM_Asset_Info_Panel(MT_PT_AM_Main_Panel, Panel):
    """Asset Info Panel in Sidebar"""
    bl_idname = "MT_PT_AM_Asset_Info_Panel"
    bl_label = "Asset Info"
    bl_order = 1

    @classmethod
    def poll(cls, context):
        bar = context.scene.mt_am_props.asset_bar
        return bar and bar.last_selected_asset

    def draw(self, context):
        props=context.scene.mt_am_props
        bar = props.asset_bar
        asset = bar.last_selected_asset
        layout = self.layout
        try:
            asset_data = asset.asset_data
            layout.prop(asset, "name")
            layout.prop(asset_data, "description")
            layout.prop(asset_data, "author")
            layout.prop(asset_data, "mt_license")
            layout.prop(asset_data, "tags")
            op = layout.operator("asset.mt_open_containing_blend_file")
            op.filepath = asset.library.filepath
            op.name = asset.name
        except ReferenceError:
            pass


class MT_PT_AM_Library_Select_Panel(MT_PT_AM_Main_Panel, Panel):
    """Library Selection Sub Panel"""
    bl_idname = "MT_PT_AM_Library_Select_Panel"
    bl_label = "Library"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 2

    def draw(self, context):
        props = context.scene.mt_am_props
        layout = self.layout

        layout.label(text="Add New Library:")

        layout.prop(props, 'new_library_path', text="")
        op = layout.operator('scene.mt_am_save_library')
        op.library_path = props.new_library_path
        op.library_name = path_leaf(props.new_library_path)


