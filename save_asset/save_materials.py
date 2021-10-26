"""This module contains classes and functions for saving materials to the MakeTile library."""
import os
from bpy.types import Operator
from bpy.props import StringProperty, EnumProperty, BoolProperty
from .add_to_library import create_preview_obj_enums
from .add_to_library import (
    draw_save_props_menu,
    check_category_type,
    add_asset_to_library,
    construct_asset_description,
    save_as_blender_asset)
from ..preferences import get_prefs
from .preview_rendering import render_material_preview
from ..utils import tagify


class MT_OT_AM_Add_Material_To_Library(Operator):
    """Add active material to library."""

    bl_idname = "material.mt_ot_am_add_material_to_library"
    bl_label = "Add active material to library"
    bl_description = "Adds the active material to the MakeTile Library"

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
        # pack images into material
        nodes = material.node_tree.nodes
        for node in nodes:
            try:
                node.image.pack()
            except AttributeError:
                pass

        props = context.scene.mt_am_props
        prefs = get_prefs()
        assets_path = prefs.user_assets_path
        asset_type = "MATERIALS"

        if self.DisplacementMaterial:
            material['mt_material'] = True

        tags = tagify(self.Tags)

        kwargs = {
            "Description": self.Description,
            "URI": self.URI,
            "Author": self.Author,
            "License": self.License,
            "Tags": tags}

        asset_desc = construct_asset_description(
            props,
            asset_type,
            assets_path,
            material,
            **kwargs)

        scene_path = os.path.join(
            prefs.default_assets_path,
            "previews",
            "preview_scenes.blend")

        # Preview object should be a choice between wall, floor, roof, base etc.
        # TODO implement mini base and roof preview objects
        preview_obj = self.PreviewObject

        if render_material_preview(
                self,
                context,
                asset_desc['PreviewImagePath'],
                scene_path,
                prefs.preview_scene,
                material,
                preview_obj):

            # save asset data for Blender asset browser
            if hasattr(material, 'asset_data'):
                save_as_blender_asset(material, asset_desc, tags)

            add_asset_to_library(
                self,
                context,
                material,
                asset_type,
                asset_desc)

            props.assets_updated = True

            return {'FINISHED'}

        return {'CANCELLED'}


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
