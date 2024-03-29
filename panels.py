import bpy
from bpy.types import Panel
from .categories import load_categories


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
        active_category = props.active_category
        try:
            child_cats = props['child_cats']
            if active_category is None and len(child_cats) == 0:
                child_cats = load_categories()
        except KeyError:
            child_cats = load_categories()

        layout = self.layout

        if active_category is not None:
            op = layout.operator('view3d.mt_ret_to_parent', text=active_category['Name'], icon='FILE_PARENT')

            row = layout.row()
            row.label(text='Categories')
            row.operator('scene.mt_am_add_category', text="", icon='ADD')
        else:
            layout.label(text='Categories')

        for cat in child_cats:
            cat_text = cat["Name"]
            row = layout.row()
            op = row.operator("view3d.mt_asset_bar", text=cat_text, icon="FILE_FOLDER")
            op.category_slug = cat["Slug"]
            if cat["Parent"]:
                del_op = row.operator("view3d.mt_delete_category", text="", icon="REMOVE")
                del_op.category_slug = cat["Slug"]
