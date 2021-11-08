"""This module contains classes and functions for saving objects to the MakeTile library."""
import os
import bpy
from bpy.types import Operator
from .add_to_library import (
    MT_Save_To_Library)
from ..preferences import get_prefs
from .preview_rendering import render_object_preview
from ..utils import tagify

class MT_OT_AM_Add_Multiple_Objects_To_Library(Operator, MT_Save_To_Library):
    """Add all selected mesh objects to the MakeTile Library."""

    bl_idname = "object.add_selected_objects_to_library"
    bl_label = "Add selected objects to library"
    bl_description = "Adds selected objects to the MakeTile Library"

    @classmethod
    def poll(cls, context):
        """Check the active object is a mesh object and we have at least 1 object selected."""
        try:
            if context.active_object.type == 'MESH' and len(context.selected_objects) > 0:
                return True
        except KeyError:
            return None
        return None

    def execute(self, context):
        """Save all selected mesh objects to MakeTile library."""
        obs = [ob for ob in context.selected_editable_objects if ob.type == 'MESH']
        props = context.scene.mt_am_props
        prefs = get_prefs()
        tags = tagify(self.tags)

        kwargs = {
            "desc": self.desc,
            "author": self.author,
            "license": self.license,
            "tags": tags}

        scene_path = os.path.join(
            prefs.default_assets_path,
            "previews",
            "preview_scenes.blend")

        for obj in obs:
            asset_desc = self.construct_asset_description(
                props,
                obj,
                **kwargs)

            if self.preview_img:
                img = bpy.data.images[self.preview_img, None]
            else:
                imagepath = asset_desc['imagepath']

                img = render_object_preview(
                    self,
                    context,
                    imagepath,
                    scene_path,
                    prefs.preview_scene,
                    obj)

            # save asset data for Blender asset browser
            if hasattr(obj, 'asset_data'):
                self.mark_as_asset(obj, asset_desc, tags)

            # add the asset to the MakeTile library
            self.add_asset_to_library(
                obj,
                asset_desc,
                img)

        props.assets_updated = True

        return {'FINISHED'}

    def invoke(self, context, event):
        """Call when operator invoked from UI."""
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        """Draw popup property menu."""
        layout = self.layout
        if len([ob for ob in context.selected_editable_objects if ob.type == 'MESH']) == 1:
            layout.prop(context.active_object, 'name')
        else:
            layout.label(text="All objects will have the same asset properties.")
        self.draw_save_props_menu(context)