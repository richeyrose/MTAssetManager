import os
import uuid
import bpy
from bpy.app.handlers import persistent
from math import floor
from bpy.types import Operator
from bpy.props import StringProperty
from .preferences import get_prefs
from .categories import get_child_cats, get_parent_cat_slug, get_category, load_categories
from .assets import get_assets_by_cat, append_preview_images
from .ui.ui_bar import MT_UI_AM_Asset_Bar
from .ui.ui_asset import MT_AM_UI_Asset
from .ui.ui_nav_arrow import MT_UI_AM_Left_Nav_Arrow, MT_UI_AM_Right_Nav_Arrow
from .app_handlers import create_properties

class MT_OT_AM_Asset_Bar_2(Operator):
    """Operator for displaying the MakeTile Asset bar"""
    bl_idname = "view3d.mt_asset_bar_2"
    bl_label = "Show Asset Bar"
    bl_description = "Display asset bar"
    bl_options = {'REGISTER'}

    current_category_path: StringProperty(
        name="Category Path",
        subtype='DIR_PATH',
        description="Path to the current category"
    )

    bar_draw_handler = None
    asset_bar = None

    def __init__(self):
        self.previous_category = ""

    def invoke(self, context, event):
        props = context.scene.mt_am_props

        # save these so we can check later. Used for removing draw handlers
        # when we switch scene, change window etc.
        self.window = context.window
        self.area = context.area
        self.scene = bpy.context.scene
        self.has_quad_views = len(bpy.context.area.spaces[0].region_quadviews) > 0

        # update side bar
        self.update_sidebar(context)

        if props.current_category_path:
            # Check to see if we are already displaying asset bar
            # and add asset bar draw handler and modal handler if not
            if not MT_OT_AM_Asset_Bar_2.asset_bar:
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
        # check we've not switched scene
        if bpy.context.scene != self.scene:
            self.finish(context)
            return {'CANCELLED'}

        # handle closing or switching workspaces here
        areas = []

        for w in context.window_manager.windows:
            areas.extend(w.screen.areas)

        if self.area not in areas or self.area.type != 'VIEW_3D' or self.has_quad_views != (
                len(self.area.spaces[0].region_quadviews) > 0):
            self.finish(context)
            return {'CANCELLED'}

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


    def image_from_preview(self, preview, unique_id=None):
        """Return a normal image from a data block preview image.

        Args:
            preview (bpy.types.ImagePreview): A data block preview image
        Returns:
            image (bpy.types.Image): Blender image
        """
        newImage = bpy.data.images.new(
            name=unique_id,
            width=preview.image_size[0],
            height=preview.image_size[1])

        newImage.pixels = preview.image_pixels_float
        return newImage


    def init_assets(self, context, reset_index=True):
        """Initialise assets based on current active category.

        Args:
            context (bpy.context): context
            reset_index (bool, optional): Whether to reset the asset bar index to 0. Defaults to True.
        """
        path = self.current_category_path
        current_assets = []

        # get all assets in current directory
        for file in os.listdir(path):
            if file.endswith(".blend"):
                with bpy.data.libraries.load(os.path.join(path, file), assets_only=True, link=True) as (data_from, data_to):
                    data_to.collections = [coll for coll in data_from.collections]
                    data_to.objects = [obj for obj in data_from.objects]
                    data_to.materials = [mat for mat in data_from.materials]
                items = data_to.collections + data_to.objects + data_to.materials
                for i in items:
                    current_assets.append(i)

        # props = context.scene.mt_am_props
        for asset in current_assets:
            if asset.mt_preview_img:
                asset_img = asset.mt_preview_img
            else:
                pass



        # props = context.scene.mt_am_props
        # # get current assets based on active category
        # current_assets = get_assets_by_cat(props.active_category["Slug"])

        # # make sure preview images are appended
        # append_preview_images(current_assets)

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
                MT_OT_AM_Asset_Bar_2.asset_bar,
                current_assets.index(asset),
                self)
            assets.append(new_asset)

        try:
            # reset asset indexes.
            # We don't want to do this if we are reinitialising
            # assets after we've added, removed or updated one as we want the
            # asset bar to remain at its current index
            if reset_index:
                self.asset_bar.first_asset_index = 0
        except AttributeError:
            self.init_asset_bar(context)
            if reset_index:
                self.asset_bar.first_asset_index = 0

        # register assets in asset bar
        self.asset_bar.assets = assets

        # initialise assets
        for asset in assets:
            asset.init(context)

    def init_asset_bar(self, context):
        context.scene.mt_am_props.asset_bar = MT_OT_AM_Asset_Bar_2.asset_bar = MT_UI_AM_Asset_Bar(50, 50, 300, 200, self)
        self.asset_bar.init(context)

    def update_sidebar(self, context):
        am_props = context.scene.mt_am_props

        # update parent category path
        context.scene.mt_am_props.parent_category_path = os.path.abspath(os.path.join(self.current_category_path, os.pardir))

        #update current category path
        context.scene.mt_am_props.current_category_path = self.current_category_path

    def register_asset_bar_draw_handler(self, args, context):
        """Register the draw handler for the asset bar.

        Args:
            args (tuple(self, context)): self and bpy.context
            context (bpy.context): context
        """
        MT_OT_AM_Asset_Bar_2.bar_draw_handler = bpy.types.SpaceView3D.draw_handler_add(
            self.draw_callback_asset_bar,
            args,
            "WINDOW",
            "POST_PIXEL")

    def unregister_handlers(self, context):
        """Unregister the draw handlers

        Args:
            context (bpy.context): context
        """
        if MT_OT_AM_Asset_Bar_2.bar_draw_handler:
            bpy.types.SpaceView3D.draw_handler_remove(
                MT_OT_AM_Asset_Bar_2.bar_draw_handler,
                "WINDOW")
            MT_OT_AM_Asset_Bar_2.bar_draw_handler = None
            MT_OT_AM_Asset_Bar_2.asset_bar = context.scene.mt_am_props.asset_bar = None

    def finish(self, context):
        """Unregister handlers and clean up. Call when switching windows, scenes etc.

        Args:
            context (bpy.context): Context

        Returns:
            operator return value {'FINISHED'}: Operator return
        """
        props = context.scene.mt_am_props
        self.unregister_handlers(context)

        # reset categories for side bar
        props.active_category = None
        props.parent_category = ""

        # get child categories and update side bar
        props['child_cats'] = get_child_cats(
            props.categories,
            "")
        return {"FINISHED"}

    def draw_callback_asset_bar(self, op, context):
        """Draw callback for asset bar.

        Args:
            op (operator): operator
            context (bpy.context): context
        """
        # check to see if an asset has been added, removed or updated.
        if hasattr(context.scene, 'mt_am_props') and context.scene.mt_am_props.assets_updated:
            context.scene.mt_am_props.assets_updated = False
            self.init_assets(context, reset_index=False)
        try:
            MT_OT_AM_Asset_Bar_2.asset_bar.draw()
        except AttributeError:
            pass

    def handle_events(self, event):
        try:
            return self.asset_bar.handle_event(event)
        except AttributeError:
            return False

# TODO see if we can get self.report to work properly
class MT_OT_AM_Asset_Bar(Operator):
    """Operator for displaying the MakeTile Asset bar"""
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

        # save these so we can check later. Used for removing draw handlers
        # when we switch scene, change window etc.
        self.window = context.window
        self.area = context.area
        self.scene = bpy.context.scene
        self.has_quad_views = len(bpy.context.area.spaces[0].region_quadviews) > 0

        # update categories
        self.update_categories(context)

        if props.active_category:
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
        # check we've not switched scene
        if bpy.context.scene != self.scene:
            self.finish(context)
            return {'CANCELLED'}

        # handle closing or switching workspaces here
        areas = []

        for w in context.window_manager.windows:
            areas.extend(w.screen.areas)

        if self.area not in areas or self.area.type != 'VIEW_3D' or self.has_quad_views != (
                len(self.area.spaces[0].region_quadviews) > 0):
            self.finish(context)
            return {'CANCELLED'}

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

    def init_assets(self, context, reset_index=True):
        """Initialise assets based on current active category.

        Args:
            context (bpy.context): context
            reset_index (bool, optional): WHether to reset the asset bar index to 0. Defaults to True.
        """
        props = context.scene.mt_am_props
        # get current assets based on active category
        current_assets = get_assets_by_cat(props.active_category["Slug"])

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
            # reset asset indexes.
            # We don't want to do this if we are reinitialising
            # assets after we've added, removed or updated one as we want the
            # asset bar to remain at its current index
            if reset_index:
                self.asset_bar.first_asset_index = 0
        except AttributeError:
            self.init_asset_bar(context)
            if reset_index:
                self.asset_bar.first_asset_index = 0

        # register assets in asset bar
        self.asset_bar.assets = assets

        # initialise assets
        for asset in assets:
            asset.init(context)

    def init_asset_bar(self, context):
        context.scene.mt_am_props.asset_bar = MT_OT_AM_Asset_Bar.asset_bar = MT_UI_AM_Asset_Bar(50, 50, 300, 200, self)
        self.asset_bar.init(context)

    def update_categories(self, context):
        # update parent and active categories based on passed in category_slug
        am_props = context.scene.mt_am_props
        categories = am_props.categories

        # update parent category
        context.scene.mt_am_props.parent_category = get_parent_cat_slug(
            categories,
            self.category_slug)

        # update active_category
        context.scene.mt_am_props.active_category = get_category(categories, self.category_slug)

        # get child categories and update side bar
        #TODO: Should be an annotation
        am_props['child_cats'] = get_child_cats(
            categories,
            self.category_slug)

    def register_asset_bar_draw_handler(self, args, context):
        """Register the draw handler for the asset bar.

        Args:
            args (tuple(self, context)): self and bpy.context
            context (bpy.context): context
        """
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
            MT_OT_AM_Asset_Bar.asset_bar = context.scene.mt_am_props.asset_bar = None


    def handle_events(self, event):
        try:
            return self.asset_bar.handle_event(event)
        except AttributeError:
            return False

    def finish(self, context):
        """Unregister handlers and clean up. Call when switching windows, scenes etc.

        Args:
            context (bpy.context): Context

        Returns:
            operator return value {'FINISHED'}: Operator return
        """
        props = context.scene.mt_am_props
        self.unregister_handlers(context)

        # reset categories for side bar
        props.active_category = None
        props.parent_category = ""

        # get child categories and update side bar
        props['child_cats'] = get_child_cats(
            props.categories,
            "")
        return {"FINISHED"}

    def draw_callback_asset_bar(self, op, context):
        """Draw callback for asset bar.

        Args:
            op (operator): operator
            context (bpy.context): context
        """
        # check to see if an asset has been added, removed or updated.
        if hasattr(context.scene, 'mt_am_props') and context.scene.mt_am_props.assets_updated:
            context.scene.mt_am_props.assets_updated = False
            self.init_assets(context, reset_index=False)
        try:
            MT_OT_AM_Asset_Bar.asset_bar.draw()
        except AttributeError:
            pass


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

class MT_OT_AM_Return_To_Parent_2(Operator):
    bl_idname = "view3d.mt_ret_to_parent_2"
    bl_label = "MakeTile return to parent"
    bl_description = "Move up a category level"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        props = context.scene.mt_am_props
        bpy.ops.view3d.mt_asset_bar_2(
            'INVOKE_DEFAULT',
            current_category_path=props.parent_category_path)
        return {'FINISHED'}

@persistent
def remove_asset_bar_on_load(dummy):
    """Remove the asset bar when a new file is loaded."""
    if MT_OT_AM_Asset_Bar.bar_draw_handler:
        bpy.types.SpaceView3D.draw_handler_remove(
            MT_OT_AM_Asset_Bar.bar_draw_handler,
            "WINDOW")
        MT_OT_AM_Asset_Bar.bar_draw_handler = None
        MT_OT_AM_Asset_Bar.asset_bar = bpy.context.scene.mt_am_props.asset_bar = None

bpy.app.handlers.load_pre.append(remove_asset_bar_on_load)
