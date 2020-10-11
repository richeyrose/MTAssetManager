import bpy
from bpy.types import Panel, Operator
from .categories import get_category, get_child_cats, get_parent_cat_slug


class MT_PT_AM_Main_Panel(Panel):
    """Asset N Menu UI panel."""

    bl_category = "Asset Manager"
    bl_idname = "MT_PT_AM_Main_Panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_label = "Assets"


    def draw(self, context):
        scene = context.scene
        props = context.scene.mt_am_props
        active_category = props['active_category']
        child_cats = props['child_cats']

        layout = self.layout

        if active_category != "":
            op = layout.operator('view3d.mt_ret_to_parent', text='...', icon='FILE_PARENT')

        layout.label(text="Categories")
        for cat in child_cats:
            cat_text = cat["Name"]
            op = layout.operator("view3d.mt_asset_bar", text=cat_text, icon="FILE_FOLDER")
            op.category_slug = cat["Slug"]



