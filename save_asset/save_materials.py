"""This module contains classes and functions for saving materials to the MakeTile library."""
import os
from bpy.types import Operator
from bpy.props import EnumProperty, BoolProperty
from .add_to_library import (
    MT_Save_To_Library)
from ..preferences import get_prefs
from .preview_rendering import render_material_preview
from ..utils import tagify


class MT_OT_AM_Add_Material_To_Library(Operator, MT_Save_To_Library):
    """Add active material to library."""

    bl_idname = "material.mt_ot_am_add_material_to_library"
    bl_label = "Add active material to library"
    bl_description = "Adds the active material to the MakeTile Library"

    def create_preview_obj_enums(self, context):
        """Create a blender enum list of objects that can be used for rendering material previews.

        Scans the addon/assets/previews/objects path and creates an enum based on the names
        of the .blend files it finds there.

        Args:
            context (bpy.Context): Blender context

        Returns:
            list[bpy.types.EnumPropertyItem]: Enum Items
        """
        enum_items = []

        if context is None:
            return enum_items

        prefs = get_prefs()

        obj_path = os.path.join(
            prefs.default_assets_path,
            "previews",
            "objects")

        filenames = [name for name in os.listdir(obj_path)
                    if os.path.isfile(os.path.join(obj_path, name))]

        for name in filenames:
            stripped_name = os.path.splitext(name)[0]
            enum = (stripped_name, stripped_name, "")
            enum_items.append(enum)

        return sorted(enum_items)

    displacement_material: BoolProperty(
        name="Displacement Material",
        description="Is this a MakeTile diplacement material",
        default=True
    )

    preview_object: EnumProperty(
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
        return context.active_object and context.active_object.active_material

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
        tags = tagify(self.tags)

        if self.displacement_material:
            material['mt_material'] = True

        kwargs = {
            "desc": self.desc,
            "author": self.author,
            "license": self.license,
            "tags": tags}

        scene_path = os.path.join(
            prefs.default_assets_path,
            "previews",
            "preview_scenes.blend")

        asset_desc = self.construct_asset_description(
            props,
            material,
            **kwargs)

        # Preview object should be a choice between wall, floor, roof, base etc.
        # TODO implement mini base and roof preview objects
        preview_obj = self.preview_object

        imagepath = asset_desc['imagepath']

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
            self.mark_as_asset(material, asset_desc, tags)

        self.add_asset_to_library(
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
        self.draw_save_props_menu(context)
        layout.prop(self, 'displacement_material')
        layout.prop(self, 'preview_object')
