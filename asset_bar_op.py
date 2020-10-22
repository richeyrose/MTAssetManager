import bpy
from math import floor
from bpy.types import Operator
from bpy.props import StringProperty
from .preferences import get_prefs
from .categories import get_child_cats, get_parent_cat_slug, get_category
from .assets import get_assets_by_cat, append_preview_images
from .ui_bar import MT_UI_AM_Asset_Bar
from .ui_asset import MT_AM_UI_Asset
from .ui_nav_arrow import MT_UI_AM_Left_Nav_Arrow, MT_UI_AM_Right_Nav_Arrow

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
    assets_draw_handler = None
    asset_bar = None
    nav_arrows = []
    assets = []

    def __init__(self):
        self.bar_draw_handler = MT_OT_AM_Asset_Bar.bar_draw_handler
        self.current_assets = []

    def init_assets(self, context, assets):
        for asset in self.assets:
            del asset
        MT_OT_AM_Asset_Bar.assets = assets
        for asset in assets:
            asset.init(context)
            self.asset_bar.widgets.append(asset)

    def init_asset_bar(self, context, asset_bar):
        asset_bar.init(context)
        for arrow in self.nav_arrows:
            arrow.init(context)
            self.asset_bar.widgets.append(arrow)

    def invoke(self, context, event):
        # Check to see if we are already displaying asset bar
        # and add asset bar draw handler and modal handler if not
        if not MT_OT_AM_Asset_Bar.asset_bar:
            # initialise asset bar
            MT_OT_AM_Asset_Bar.asset_bar = MT_UI_AM_Asset_Bar(50, 50, 300, 200, self)
            # initialise nav arrows
            left_nav = MT_UI_AM_Left_Nav_Arrow(50, 50, 300, 200, self.asset_bar)
            right_nav = MT_UI_AM_Right_Nav_Arrow(50, 50, 300, 200, self.asset_bar)
            MT_OT_AM_Asset_Bar.nav_arrows = [left_nav, right_nav]
            self.init_asset_bar(context, self.asset_bar)
            # register asset bar draw handler
            args = (self, context)
            self.register_asset_bar_draw_handler(args, context)
            # add the modal handler that handles events
            context.window_manager.modal_handler_add(self)

        # update parent and active categories based on passed in category_slug
        am_props = context.scene.mt_am_props

        context.scene.mt_am_props.parent_category = get_parent_cat_slug(am_props['categories'], self.category_slug)
        active_category = context.scene.mt_am_props.active_category = self.category_slug

        # get child categories and update side bar
        am_props['child_cats'] = get_child_cats(am_props['categories'], active_category)

        # get current assets based on active category
        self.current_assets = get_assets_by_cat(active_category)
        # make sure preview images are appended
        append_preview_images(self.current_assets)

        # instantiate a thumbnail for each asset in current assets
        prefs = get_prefs()
        assets = []
        for asset in self.current_assets:
            new_asset = MT_AM_UI_Asset(
                50,
                50,
                prefs.asset_item_dimensions,
                prefs.asset_item_dimensions,
                asset, MT_OT_AM_Asset_Bar.asset_bar,
                self.current_assets.index(asset))
            assets.append(new_asset)

        # reset asset indexes
        self.asset_bar.first_asset_index = 0

        self.init_assets(context, assets)

        # register the asset draw handler
        args = (self, context)
        self.register_assets_draw_handler(args, context)

        return {'RUNNING_MODAL'}

    def on_invoke(self, context, event):
        pass

    def modal(self, context, event):
        """Handle user input.

        Args:
            context (bpy.context): context
            event (event): mouse or keyboard event
        """
        # make sure we always redraw 3d view if we are drawing
        if context.area:
            context.area.tag_redraw()

        # handle events in thumbnails
        if self.handle_events(event):
            return {'RUNNING_MODAL'}


        # close asset bar if Esc is pressed and end modal
        if event.type == 'ESC':
            self.unregister_handlers(context)
            return {'CANCELLED'}

        return {'PASS_THROUGH'}

    def register_asset_bar_draw_handler(self, args, context):
        MT_OT_AM_Asset_Bar.bar_draw_handler = bpy.types.SpaceView3D.draw_handler_add(self.draw_callback_asset_bar, args, "WINDOW", "POST_PIXEL")

    def register_assets_draw_handler(self, args, context):
        if MT_OT_AM_Asset_Bar.assets_draw_handler:
            bpy.types.SpaceView3D.draw_handler_remove(MT_OT_AM_Asset_Bar.assets_draw_handler, "WINDOW")
            MT_OT_AM_Asset_Bar.assets_draw_handler = None
        MT_OT_AM_Asset_Bar.assets_draw_handler = bpy.types.SpaceView3D.draw_handler_add(self.draw_callback_assets, args, "WINDOW", "POST_PIXEL")

    def unregister_handlers(self, context):
        """Unregister the draw handlers

        Args:
            context (bpy.context): context
        """
        if MT_OT_AM_Asset_Bar.bar_draw_handler:
            bpy.types.SpaceView3D.draw_handler_remove(MT_OT_AM_Asset_Bar.bar_draw_handler, "WINDOW")
            MT_OT_AM_Asset_Bar.bar_draw_handler = None
            MT_OT_AM_Asset_Bar.asset_bar = None
            MT_OT_AM_Asset_Bar.nav_arrows = []

        if MT_OT_AM_Asset_Bar.assets_draw_handler:
            bpy.types.SpaceView3D.draw_handler_remove(MT_OT_AM_Asset_Bar.assets_draw_handler, "WINDOW")
            MT_OT_AM_Asset_Bar.assets_draw_handler = None

    def handle_events(self, event):
        result = False
        if self.asset_bar.handle_event(event):
            result = True
        for asset in self.assets:
            if asset.handle_event(event):
                result = True
        for arrow in self.nav_arrows:
            if arrow.handle_event(event):
                result = True
        return result

    def finish(self, context):
        self.unregister_handlers(context)
        return {"FINISHED"}

    def draw_callback_asset_bar(self, op, context):
        MT_OT_AM_Asset_Bar.asset_bar.draw()
        for nav_arrow in self.nav_arrows:
            nav_arrow.draw()

    def draw_callback_assets(self, op, context):
        for asset in self.assets:
            asset.draw()


class MT_OT_AM_Return_To_Parent(Operator):
    bl_idname = "view3d.mt_ret_to_parent"
    bl_label = "MakeTile return to parent"
    bl_description = "Move up a category level"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        props = context.scene.mt_am_props
        bpy.ops.view3d.mt_asset_bar('INVOKE_DEFAULT', category_slug=props.parent_category)
        return {'FINISHED'}
