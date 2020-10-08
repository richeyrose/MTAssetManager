import bpy
from bpy.types import Operator
from bpy.props import StringProperty
from .categories import get_child_cats, get_parent_cat

class MT_OT_AM_Asset_Bar(Operator):
    bl_idname = "view3d.mt_asset_bar"
    bl_label = "MakeTile Asset Bar UI"
    bl_options = {'INTERNAL'}

    category_slug: StringProperty(
        name="Category",
        default="None",
    )

    def modal(self, context, event):
        """Handle user input.

        Args:
            context (bpy.context): context
            event (event): mouse or keyboard event
        """
        props = context.scene.mt_am_props.active_category

        # close asset bar if Esc is pressed and end modal
        if event.type == 'ESC':
            return {'CANCELLED'}

        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        """Handle operator button being clicked on

        Args:
            context (bpy.context): context
            event (event): mouse or keyboard event
        """

        props = context.scene.mt_am_props
        context.scene.mt_am_props.parent_category = props.active_category
        context.scene.mt_am_props.active_category = self.category_slug  # the category that has just been clicked on

        props = context.scene.mt_am_props
        for cat in props['child_cats']:
            if cat['Slug'] == props.active_category:
                props['child_cats'] = cat['Children']
                break

        return {'FINISHED'}


class MT_OT_AM_Return_To_Parent(Operator):
    bl_idname = "view3d.mt_ret_to_parent"
    bl_label = "MakeTile return to parent"
    bl_description = "Move up a category level"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        props = context.scene.mt_am_props

        props['child_cats'] = get_child_cats(props['categories'], props.parent_category)

        context.scene.mt_am_props.active_category = props.parent_category
        context.scene.mt_am_props.parent_category = get_parent_cat(props['categories'], props.parent_category)
        return {'FINISHED'}
