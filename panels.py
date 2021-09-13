import bpy
import os
from bpy.types import Panel
from .categories import load_categories
from .preferences import get_prefs

def list_subfolders_with_paths(path):
    return [f.path for f in os.scandir(path) if f.is_dir()]

class MT_PT_AM_Main_Panel(Panel):
    """Asset N Menu UI panel."""

    bl_category = "Asset Manager"
    bl_idname = "MT_PT_AM_Main_Panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_label = "Assets"

    def draw(self, context):
        props = context.scene.mt_am_props
        prefs = get_prefs()
        layout = self.layout
        child_cats = []

        # display return to parent button
        if props.parent_category_path and props.current_category_path != prefs.user_assets_path:
            op = layout.operator(
                'view3d.mt_ret_to_parent_2',
                text=os.path.basename(props.parent_category_path),
                icon='FILE_PARENT')

        if props.current_category_path == prefs.user_assets_path:
            path = prefs.user_assets_path
            child_cats = [
                os.path.join(path,'collections'),
                os.path.join(path,'objects'),
                os.path.join(path,'materials')]
        else:
            try:
                child_cats = list_subfolders_with_paths(props.current_category_path)
            except FileNotFoundError:
                path = prefs.user_assets_path
                child_cats = [
                    os.path.join(path,'collections'),
                    os.path.join(path,'objects'),
                    os.path.join(path,'materials')]

        for cat in child_cats:
            row = layout.row()
            op = row.operator(
                "view3d.mt_asset_bar_2",
                text=os.path.basename(cat),
                icon="FILE_FOLDER")
            op.current_category_path = cat



    # def draw(self, context):
    #     props = context.scene.mt_am_props
    #     active_category = props.active_category
    #     layout = self.layout

    #     # Check to see if props['child_cats'] is set.
    #     # If not we are in one of the root categories of objects, collections, materials
    #     try:
    #         child_cats = props['child_cats']
    #         if active_category is None and len(child_cats) == 0:
    #             child_cats = load_categories()
    #     except KeyError:
    #         child_cats = load_categories()

    #     # If we're not in a root category then display the return to parent button
    #     if active_category is not None:
    #         op = layout.operator(
    #             'view3d.mt_ret_to_parent',
    #             text=active_category['Name'],
    #             icon='FILE_PARENT')

    #         # also draw the add category button
    #         row = layout.row()
    #         row.label(text='Categories')
    #         row.operator('scene.mt_am_add_category', text="", icon='ADD')
    #     else:
    #         layout.label(text='Categories')

    #     # Draw list of child categories
    #     for cat in child_cats:
    #         cat_text = cat["Name"]
    #         row = layout.row()
    #         op = row.operator("view3d.mt_asset_bar", text=cat_text, icon="FILE_FOLDER")
    #         op.category_slug = cat["Slug"]

    #         # if we're not in one of the root categories give option to delete category
    #         if cat["Parent"]:
    #             del_op = row.operator("view3d.mt_delete_category", text="", icon="REMOVE")
    #             del_op.category_slug = cat["Slug"]
