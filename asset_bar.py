import bpy
from bpy.types import Operator
from bpy.props import StringProperty
from .categories import get_child_cats, get_parent_cat_slug, get_category
from .assets import get_assets_by_cat


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
        """Called when category button in side bar is clicked on.

        Args:
            context (bpy.context): context
            event (event): mouse or keyboard event
        """

        props = context.scene.mt_am_props

        # update properties
        context.scene.mt_am_props.parent_category = props.active_category
        context.scene.mt_am_props.active_category = self.category_slug

        current_cats = props['child_cats'].copy()

        for cat in props['child_cats']:
            if cat['Slug'] == props.active_category:
                props['child_cats'] = cat['Children']
                break

        # get assets in active_category
        active_category = props.active_category
        if active_category:
            props['current_assets'] = get_assets_by_cat(active_category)
            for asset in props['current_assets']:
                print(asset['Name'])
        return {'FINISHED'}


class MT_OT_AM_Return_To_Parent(Operator):
    bl_idname = "view3d.mt_ret_to_parent"
    bl_label = "MakeTile return to parent"
    bl_description = "Move up a category level"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        props = context.scene.mt_am_props
        parent_category = get_category(props['categories'], props.parent_category)
        if parent_category:
            props['child_cats'] = parent_category['Children']
        else:
            props['child_cats'] = get_child_cats(props['categories'], parent_category)

        context.scene.mt_am_props.active_category = props.parent_category
        context.scene.mt_am_props.parent_category = get_parent_cat_slug(props['categories'], props.parent_category)
        return {'FINISHED'}
