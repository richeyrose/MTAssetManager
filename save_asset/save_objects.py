"""This module contains classes and functions for saving objects to the MakeTile library."""
import os
from bpy.types import Operator
from bpy.props import StringProperty
from .add_to_library import (
    draw_save_props_menu,
    check_category_type,
    add_asset_to_library)
from ..preferences import get_prefs
from .preview_rendering import render_object_preview


class MT_OT_AM_Add_Multiple_Objects_To_Library(Operator):
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
        assets_path = prefs.user_assets_path
        scene_path = os.path.join(
            prefs.default_assets_path,
            "previews",
            "preview_scenes.blend")
        asset_type = "OBJECTS"

        # check if we're in a sub category that contains assets of the correct type.
        # If not add the object to the root category for its type
        if props.active_category is None:
            category = asset_type.lower()
        else:
            category = check_category_type(props.active_category, asset_type)

        kwargs = {
            "Description": "",
            "URI": "",
            "Author": "",
            "License": ""}

        for obj in obs:
            asset_desc = add_asset_to_library(
                self,
                context,
                props,
                obj,
                assets_path,
                "OBJECTS",
                category,
                **kwargs)

            render_object_preview(
                self,
                context,
                asset_desc['PreviewImagePath'],
                scene_path,
                prefs.preview_scene,
                obj)

        props.assets_updated = True
        return {'FINISHED'}


class MT_OT_AM_Add_Active_Object_To_Library(Operator):
    """Add selected active mesh object to the MakeTile Library."""

    bl_idname = "object.add_active_object_to_library"
    bl_label = "Add active object to library"
    bl_options = {'REGISTER'}
    bl_description = "Adds active object to the MakeTile Library"

    Description: StringProperty(
        name="Description",
        default=""
    )

    URI: StringProperty(
        name="URI",
        default=""
    )

    Author: StringProperty(
        name="Author",
        default=""
    )

    License: StringProperty(
        name="License",
        default="All Rights Reserved"
    )

    Tags: StringProperty(
        name="Tags",
        description="Comma seperated list",
        default=""
    )

    @classmethod
    def poll(cls, context):
        """Check the active object is a mesh object and we have at least 1 object selected."""
        try:
            return context.active_object.type == 'MESH' and len(context.selected_objects) > 0
        except KeyError:
            return None
        return None

    def execute(self, context):
        """Save the active object to MakeTile library."""
        obj = context.active_object
        props = context.scene.mt_am_props
        prefs = get_prefs()
        assets_path = prefs.user_assets_path
        asset_type = "OBJECTS"

        # check if we're in a sub category that contains assets of the correct type.
        # If not add the object to the root category for its type
        if props.active_category is None:
            category = asset_type.lower()
        else:
            category = check_category_type(props.active_category, asset_type)

        kwargs = {
            "Description": self.Description,
            "URI": self.URI,
            "Author": self.Author,
            "License": self.License}

        asset_desc = add_asset_to_library(
            self,
            context,
            props,
            obj,
            assets_path,
            asset_type,
            category,
            self.Tags,
            **kwargs)

        scene_path = os.path.join(
            prefs.default_assets_path,
            "previews",
            "preview_scenes.blend")

        render_object_preview(
            self,
            context,
            asset_desc['PreviewImagePath'],
            scene_path,
            prefs.preview_scene,
            obj)

        props.assets_updated = True

        return {'FINISHED'}

    def invoke(self, context, event):
        """Call when operator invoked from UI."""
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        """Draw popup property menu."""
        layout = self.layout
        layout.prop(context.active_object, 'name')
        draw_save_props_menu(self, context)
