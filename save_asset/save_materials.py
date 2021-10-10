"""This module contains classes and functions for saving materials to the MakeTile library."""
import os
from bpy.types import Operator
from bpy.props import EnumProperty, BoolProperty
from .add_to_library import create_preview_obj_enums
from .add_to_library import (
    draw_save_props_menu,
    add_asset_to_library,
    construct_asset_description,
    mark_as_asset,MT_Save_To_Library)
from ..preferences import get_prefs
from .preview_rendering import render_material_preview
from ..utils import tagify


class MT_OT_AM_Add_Material_To_Library(Operator, MT_Save_To_Library):
    """Add active material to library."""

    bl_idname = "material.mt_ot_am_add_material_to_library"
    bl_label = "Add active material to library"
    bl_description = "Adds the active material to the MakeTile Library"

    DisplacementMaterial: BoolProperty(
        name="Displacement Material",
        description="Is this a MakeTile diplacement material",
        default=True
    )

    PreviewObject: EnumProperty(
        items=create_preview_obj_enums,
        name="Preview Object",
        description="Preview object to use for material render"
    )

    @classmethod
    def poll(cls, context):
        """Check we have an active material on the active object.

        Args:
            context (bpy.context): context

        Returns:
            Bool: boolean
        """
        if context.object is not None:
            return context.object.active_material is not None
        return False

    def execute(self, context):
        """Add the active material to the MakeTile Library."""
        material = context.active_object.active_material
        props = context.scene.mt_am_props
        prefs = get_prefs()
        asset_type = "MATERIALS"
        tags = tagify(self.Tags)

        if self.DisplacementMaterial:
            material['mt_material'] = True

        kwargs = {
            "Description": self.Description,
            "URI": self.URI,
            "Author": self.Author,
            "License": self.License,
            "Tags": tags}

        scene_path = os.path.join(
            prefs.default_assets_path,
            "previews",
            "preview_scenes.blend")

        asset_desc = construct_asset_description(
            props,
            asset_type,
            material,
            **kwargs)

        # Preview object should be a choice between wall, floor, roof, base etc.
        # TODO implement mini base and roof preview objects
        preview_obj = self.PreviewObject

        imagepath = os.path.join(
            asset_desc['FilePath'],
            asset_desc['PreviewImageName'])

        img = render_material_preview(
                self,
                context,
                imagepath,
                scene_path,
                prefs.preview_scene,
                material,
                preview_obj)

        # save asset data for Blender asset browser
        if hasattr(material, 'asset_data'):
            mark_as_asset(material, asset_desc, tags)

        add_asset_to_library(
            self,
            material,
            asset_desc,
            img)

        props.assets_updated = True

        return {'FINISHED'}

    def invoke(self, context, event):
        """Call when operator invoked from UI."""
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        """Draw a pop up property menu."""
        layout = self.layout
        layout.prop(context.active_object.active_material, 'name')
        draw_save_props_menu(self, context)
        layout.prop(self, 'DisplacementMaterial')
        layout.prop(self, 'PreviewObject')
