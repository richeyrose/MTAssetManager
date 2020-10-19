import bpy
from math import floor
from bpy.types import Operator
from bpy.props import StringProperty
from .preferences import get_prefs
from .categories import get_child_cats, get_parent_cat_slug, get_category
from .assets import get_assets_by_cat, append_preview_images
from .ui_bar import MT_UI_AM_Asset_Bar, MT_AM_UI_Asset


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

    def init_asset_bar(self, context, asset_bar):
        asset_bar.init(context)

    def invoke(self, context, event):
        # Check to see if we are already displaying asset bar and add asset bar draw handler
        # and modal handler if not
        if not MT_OT_AM_Asset_Bar.asset_bar:
            MT_OT_AM_Asset_Bar.asset_bar = MT_UI_AM_Asset_Bar(50, 50, 300, 200)
            self.init_asset_bar(context, self.asset_bar)
            args = (self, context)
            self.register_asset_bar_draw_handler(args, context)
            context.window_manager.modal_handler_add(self)

        # update parent and active categories based on passed in category_slug
        am_props = context.scene.mt_am_props
        context.scene.mt_am_props.parent_category = am_props.active_category
        active_category = context.scene.mt_am_props.active_category = self.category_slug

        # set child_cats and update side bar
        for cat in am_props['child_cats']:
            if cat['Slug'] == am_props.active_category:
                am_props['child_cats'] = cat['Children']
                break

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
        if self.handle_asset_events(event):
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
        """Unregister the draw handler

        Args:
            context (bpy.context): context
        """
        if MT_OT_AM_Asset_Bar.bar_draw_handler:
            bpy.types.SpaceView3D.draw_handler_remove(MT_OT_AM_Asset_Bar.bar_draw_handler, "WINDOW")
            MT_OT_AM_Asset_Bar.bar_draw_handler = None
            MT_OT_AM_Asset_Bar.asset_bar = None
        if MT_OT_AM_Asset_Bar.assets_draw_handler:
            bpy.types.SpaceView3D.draw_handler_remove(MT_OT_AM_Asset_Bar.assets_draw_handler, "WINDOW")
            MT_OT_AM_Asset_Bar.assets_draw_handler = None

    def handle_asset_events(self, event):
        result = False
        for asset in self.assets:
            if asset.handle_event(event):
                result = True
        return result

    def finish(self, context):
        self.unregister_handlers(context)
        return {"FINISHED"}

    def draw_callback_asset_bar(self, op, context):
        MT_OT_AM_Asset_Bar.asset_bar.draw()

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
        # get new parent category from current parent category
        new_parent_category = get_category(props['categories'], props.parent_category)

        # set child_cats to children of new_parent_category
        if new_parent_category:
            props['child_cats'] = new_parent_category['Children']
        else:
            props['child_cats'] = get_child_cats(props['categories'], new_parent_category)

        # set mt_am_props.active_category to old parent category
        context.scene.mt_am_props.active_category = props.parent_category
        # set mt_am_props.parent_category to new parent category
        context.scene.mt_am_props.parent_category = get_parent_cat_slug(props['categories'], props.parent_category)

        # reset asset index
        bar_props = context.scene.mt_bar_props
        bar_props.first_visible_asset = 0

        return {'FINISHED'}