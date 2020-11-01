import bpy
from math import floor
from bpy.types import Operator
from bpy.props import StringProperty
from .preferences import get_prefs
from .categories import get_child_cats, get_parent_cat_slug, get_category, load_categories
from .assets import get_assets_by_cat, append_preview_images
from .ui_bar import MT_UI_AM_Asset_Bar
from .ui_asset import MT_AM_UI_Asset
from .ui_nav_arrow import MT_UI_AM_Left_Nav_Arrow, MT_UI_AM_Right_Nav_Arrow
from .app_handlers import create_propertes

#TODO see if we can get self.report to work properly
class MT_OT_AM_Asset_Bar(Operator):
    bl_idname = "view3d.mt_asset_bar"
    bl_label = "Show Asset Bar"
    bl_description = "Display asset bar based on passed in category_slug"
    bl_options = {'REGISTER'}

    category_slug: StringProperty(
        name="Category",
        default="None"
    )

    bar_draw_handler = None
    asset_bar = None

    def __init__(self):
        self.previous_category = ""

    def invoke(self, context, event):

        props = context.scene.mt_am_props
        # update categories
        self.update_categories(context)

        # check to see if current category contains any assets. We only display asset bar if it does
        current_assets = get_assets_by_cat(props.active_category)

        if len(current_assets) > 0:
            # Check to see if we are already displaying asset bar
            # and add asset bar draw handler and modal handler if not
            if not MT_OT_AM_Asset_Bar.asset_bar:
                # initialise asset bar
                self.init_asset_bar(context)
                # register asset bar draw handler
                args = (self, context)
                self.register_asset_bar_draw_handler(args, context)
                # add the modal handler that handles events
                context.window_manager.modal_handler_add(self)
            # initialise assets
            self.init_assets(context)
            return {'RUNNING_MODAL'}

        self.unregister_handlers(context)
        return {'FINISHED'}

    def modal(self, context, event):
        """Handle user input.

        Args:
            context (bpy.context): context
            event (event): mouse or keyboard event
        """
        # make sure we always redraw 3d view if we are drawing
        if context.area:
            context.area.tag_redraw()

        # handle events
        if self.handle_events(event):
            return {'RUNNING_MODAL'}

        # close asset bar if Esc is pressed and end modal
        elif event.type == 'ESC':
            self.unregister_handlers(context)
            return {'CANCELLED'}

        # Undo really screws up the operator as it removes images and fucks up custom properties so we
        # remove the asset bar when an undo event is detected
        elif event.type == 'Z' and event.value == 'PRESS':
            if event.ctrl:
                self.unregister_handlers(context)
                return {'CANCELLED'}

        return {'PASS_THROUGH'}

    def init_assets(self, context):
        props = context.scene.mt_am_props
        # get current assets based on active category
        current_assets = get_assets_by_cat(props.active_category)

        if len(current_assets) > 0:
            # make sure preview images are appended
            append_preview_images(current_assets)

            # instantiate a thumbnail for each asset in current assets
            prefs = get_prefs()
            assets = []
            for asset in current_assets:
                new_asset = MT_AM_UI_Asset(
                    50,
                    50,
                    prefs.asset_item_dimensions,
                    prefs.asset_item_dimensions,
                    asset,
                    MT_OT_AM_Asset_Bar.asset_bar,
                    current_assets.index(asset),
                    self)
                assets.append(new_asset)

            try:
                # reset asset indexes
                self.asset_bar.first_asset_index = 0
            except AttributeError:
                self.init_asset_bar(context)
                self.asset_bar.first_asset_index = 0

            # register assets in asset bar
            self.asset_bar.assets = assets

            # initialise assets
            for asset in assets:
                asset.init(context)

    def init_asset_bar(self, context):
        MT_OT_AM_Asset_Bar.asset_bar = MT_UI_AM_Asset_Bar(50, 50, 300, 200, self)
        self.asset_bar.init(context)

    def update_categories(self, context):
        # update parent and active categories based on passed in category_slug
        am_props = context.scene.mt_am_props
        '''
        try:
            categories = am_props['categories']
        except KeyError:
            categories = context.scene.mt_am_props['categories'] = context.scene.mt_am_props['child_cats'] = load_categories()
        '''
        categories = am_props.categories

        context.scene.mt_am_props.parent_category = get_parent_cat_slug(
            categories,
            self.category_slug)

        active_category = context.scene.mt_am_props.active_category = self.category_slug

        # get child categories and update side bar
        am_props['child_cats'] = get_child_cats(
            categories,
            active_category)

    def register_asset_bar_draw_handler(self, args, context):
        MT_OT_AM_Asset_Bar.bar_draw_handler = bpy.types.SpaceView3D.draw_handler_add(
            self.draw_callback_asset_bar,
            args,
            "WINDOW",
            "POST_PIXEL")

    def unregister_handlers(self, context):
        """Unregister the draw handlers

        Args:
            context (bpy.context): context
        """
        if MT_OT_AM_Asset_Bar.bar_draw_handler:
            bpy.types.SpaceView3D.draw_handler_remove(
                MT_OT_AM_Asset_Bar.bar_draw_handler,
                "WINDOW")
            MT_OT_AM_Asset_Bar.bar_draw_handler = None
            MT_OT_AM_Asset_Bar.asset_bar = None

    def handle_events(self, event):
        result = False
        try:
            if self.asset_bar.handle_event(event):
                result = True
        except AttributeError:
            return result

        return result

    def finish(self, context):
        self.unregister_handlers(context)
        return {"FINISHED"}

    def draw_callback_asset_bar(self, op, context):
        MT_OT_AM_Asset_Bar.asset_bar.draw()


class MT_OT_AM_Return_To_Parent(Operator):
    bl_idname = "view3d.mt_ret_to_parent"
    bl_label = "MakeTile return to parent"
    bl_description = "Move up a category level"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        props = context.scene.mt_am_props
        bpy.ops.view3d.mt_asset_bar(
            'INVOKE_DEFAULT',
            category_slug=props.parent_category)
        return {'FINISHED'}
