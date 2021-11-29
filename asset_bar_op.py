import os
from operator import itemgetter, attrgetter
import re
import ntpath
import pathlib
import bpy
import addon_utils
from bpy.app.handlers import persistent
from bpy.types import Operator, Object, Collection, Material
from bpy.props import StringProperty
import collections
from .preferences import get_prefs
from .ui.ui_bar import MT_UI_AM_Asset_Bar
from .ui.ui_asset import MT_AM_UI_Asset
from .utils import absolute_file_paths

class MT_OT_AM_Hide_Asset_Bar(Operator):
    """Operator for hiding the MakeTile Asset bar"""
    bl_idname = "view3d.mt_hide_asset_bar"
    bl_label = "Hide Asset Bar"
    bl_description = "Hide the asset bar"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return context.scene.mt_am_props.asset_bar

    def execute(self, context):
        """Remove the asset bar from the viewport."""

        asset_bar=context.scene.mt_am_props.asset_bar
        asset_bar.op.finish(context)
        return {'FINISHED'}

class MT_OT_AM_Asset_Bar(Operator):
    """Operator for displaying the MakeTile Asset bar"""
    bl_idname = "view3d.mt_asset_bar"
    bl_label = "Show Asset Bar"
    bl_description = "Display asset bar"
    bl_options = {'REGISTER'}

    current_path: StringProperty(
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

        if props.current_path:
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

    def get_assets(self, data_from, data_to, filename, full_names, existing_items, asset_type):
        """Link assets to blender file.

        Args:
            data_from (library object): data_from library object from bpy.data.libraries.load
            data_to (library object): data_from library object from bpy.data.libraries.load
            filename (str): filename
            full_names (list): a list of datablock.full_names of this datablock type
            existing_items (list): list of existing items of this datablock type
            asset_type (str): Asset type to get.
        """
        for item in getattr(data_from, asset_type):
            name_full = str(item + ' [' + filename + ']')
            if name_full not in full_names:
                getattr(data_to, asset_type).append(item)
            else:
                for item in getattr(bpy.data, asset_type):
                    if item.name_full == name_full:
                        existing_items.append(item)
                        break


    def asset_str_filter(self, props, search_str, name, desc):
        """Filter assets by name and description.

        Args:
            props (MTAssetManager.properties.MT_PT_AM_Props): Properties
            search_str (str): String to search for
            name (str): Asset Name
            desc (str): Asset Description

        Returns:
            Bool: True iff search_str found.
        """
        search_str = re.sub(r'[^aA-zZ0-9 ]',"", search_str).lower()
        name = re.sub(r'[^aA-zZ0-9 ]',"", name).lower()
        desc = re.sub(r'[^aA-zZ0-9 ]',"", desc).lower()
        if re.search(search_str, name):
            return True
        if props.search_description:
            if re.search(search_str, desc):
                return True
        return False

    def init_assets(self, context, reset_index=True):
        """Initialise assets based on current active directory.

        Args:
            context (bpy.context): context
            reset_index (bool, optional): Whether to reset the asset bar index to 0. Defaults to True.
        """
        prefs = get_prefs()
        props = context.scene.mt_am_props
        current_path = self.current_path = context.scene.mt_am_props.current_path
        type_filter = props.type_filter
        search_str = props.text_filter
   
        # Unload libraries that are not being used.
        self.unload_libs(context, current_path)

        # load assets in current directory
        current_assets = self.load_assets_from_dir(props, current_path, type_filter, search_str)

        # sort assets
        self.sort_assets(props, current_assets)

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
            # Control first asset displayed in asset bar
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

    def load_assets_from_dir(self, props, dir, type_filter, search_str):
        assets = []

        # list of files in current directory
        files = [file for file in absolute_file_paths(dir) if file.endswith(".blend")]

        # load new files
        for file in files:
            with bpy.data.libraries.load(file, assets_only=True, link=True) as (data_from, data_to):
                # Filter by type
                if type_filter == 'NONE':
                    data_to.objects = data_from.objects
                    data_to.collections = data_from.collections
                    data_to.materials = data_from.materials
                elif type_filter == 'MATERIAL':
                    data_to.materials = data_from.materials
                elif type_filter == 'COLLECTION':
                    data_to.collections = data_from.collections
                elif type_filter == 'OBJECT':
                    data_to.objects = data_from.objects

            all_assets = data_to.objects + data_to.materials + data_to.collections

            for asset in all_assets:
                # Filter by search string
                if search_str:
                    if not self.asset_str_filter(
                        props,
                        search_str,
                        asset.name,
                        asset.asset_data.description):
                        continue
                assets.append(asset)
        return assets

    def sort_assets(self, props, current_assets):
        sort_by = props.asset_sort_by
        reverse = props.asset_reverse_sort
        if sort_by == "ALPHABETICAL":
            current_assets.sort(key=attrgetter('name'), reverse=reverse)
        elif sort_by == "MODIFIED":
            current_assets.sort(key=lambda asset: os.path.getmtime(asset.library.filepath), reverse=reverse)

    
    def unload_libs(self, context, current_path):
        # gather up all objects, materials and collections in file scene
        
        blocks = {
            "scenes": bpy.data.scenes,
            "collections": [],
            "objects":[],
            "materials":[],
            "actions":[],
            "armatures":[],
            "brushes":[],
            "cache_files":[],
            "cameras":[],
            "curves":[],
            "fonts":[],
            "grease_pencils":[],
            "hairs":[],
            "images":[],
            "lattices":[],
            "lightprobes":[],
            "lights":[],
            "linestyles":[],
            "masks":[],
            "meshes":[],
            "metaballs":[],
            "movieclips":[],
            "node_groups":[],
            "objects":[],
            "paint_curves":[],
            "palettes":[],
            "particles":[],
            "pointclouds":[],
            "screens":[],
            "simulations":[],
            "sounds":[],
            "speakers":[],
            "texts":[],
            "textures":[],
            "volumes":[],
            "workspaces":[],
            "worlds":[]}

        for scene in blocks['scenes']:
            blocks['collections'].append(scene.collection)
            blocks['collections'].extend(scene.collection.children)
            blocks['objects'].extend(scene.collection.all_objects)

        for ob in blocks['objects']:
            mats = [slot.material for slot in ob.material_slots]
            blocks['materials'].extend(mats)

        # create a set of linked libraries that contain assets that are being used in this file
        exception_libs = set()
        for block_type in blocks.values():
            for block in block_type:
                exception_libs.add(block.library)
        exception_libs.add(bpy.data.libraries['icons.blend'])
        
        # create a set of filepaths of default materials used by MakeTile
        if 'MakeTile' in context.preferences.addons:
            exception_filepaths = set([mat['filepath'] for mat in context.preferences.addons['MakeTile'].preferences['default_materials']])

        # remove any libraries not in current directory or meeting above conditions
        for lib in bpy.data.libraries:
            if lib not in exception_libs and lib.filepath not in exception_filepaths:
                bpy.data.libraries.remove(lib)

    def init_asset_bar(self, context):
        context.scene.mt_am_props.asset_bar = MT_OT_AM_Asset_Bar.asset_bar = MT_UI_AM_Asset_Bar(50, 50, 300, 200, self)
        self.asset_bar.init(context)

    def update_sidebar(self, context):
        am_props = context.scene.mt_am_props

        # update parent path
        context.scene.mt_am_props.parent_path = os.path.abspath(
            os.path.join(self.current_path, os.pardir))

        #update current path
        context.scene.mt_am_props.current_path = self.current_path

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

    def finish(self, context):
        """Unregister handlers and clean up. Call when switching windows, scenes etc.

        Args:
            context (bpy.context): Context

        Returns:
            operator return value {'FINISHED'}: Operator return
        """
        self.unload_libs(context, self.current_path)
        self.unregister_handlers(context)
        return {"FINISHED"}

    def draw_callback_asset_bar(self, op, context):
        """Draw callback for asset bar.

        Args:
            op (operator): operator
            context (bpy.context): context
        """
        # check to see if an asset has been added, removed or updated.
        try:
            if hasattr(context.scene, 'mt_am_props') and context.scene.mt_am_props.assets_updated:
                context.scene.mt_am_props.assets_updated = False
                self.init_assets(context, reset_index=False)
        except ReferenceError as err:
            self.report({'INFO'}, str(err))
            self.init_asset_bar(self, context)
        try:
            MT_OT_AM_Asset_Bar.asset_bar.draw()
        except AttributeError:
            pass

    def handle_events(self, event):
        try:
            return self.asset_bar.handle_event(event)
        except AttributeError:
            return False

class MT_OT_AM_Return_To_Parent(Operator):
    bl_idname = "view3d.mt_ret_to_parent"
    bl_label = "MakeTile return to parent"
    bl_description = "Move up a category level"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        props = context.scene.mt_am_props
        bpy.ops.view3d.mt_asset_bar(
            'INVOKE_DEFAULT',
            current_path=props.parent_path)
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
