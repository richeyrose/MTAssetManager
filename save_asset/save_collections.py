"""This module contains classes and functions related to the saving of collections as assets."""

import os
import bpy
from bpy.types import Operator
from bpy.props import StringProperty, EnumProperty
from ..collections import (
    get_object_owning_collections,
    activate_collection)
from .add_to_library import (
    draw_save_props_menu,
    check_category_type,
    add_asset_to_library)
from ..preferences import get_prefs
from .preview_rendering import render_collection_preview


class MT_OT_Add_Collection_To_Library(Operator):
    """Add the active object's owning collection to the MakeTile Library."""

    bl_idname = "collection.add_collection_to_library"
    bl_label = "Add Collection To Library"
    bl_description = "Adds the active object's owning collection to the MakeTile Library"

    def create_root_object_enums(self, context):
        """Return an enum list constructed out of a list of objects in a collection that don't have parents.

        Args:
            context (bpy.Context): context

        Returns:
            list[bpy.types.EnumPropertyItem]: enum items
        """
        enum_items = []

        if context is None:
            return enum_items

        collection = context.collection
        if collection is None:
            return enum_items

        for obj in collection.objects:
            # We only want objects that don't have parents.
            if obj.parent is None:
                item = (obj.name, obj.name, "")
                enum_items.append(item)

        enum_items.sort()
        enum_items.insert(0, ('NEW_EMPTY_ROOT', 'None', ""))

        return enum_items


    def create_owning_collection_enums(self, context):
        """Return an enum list containing the collections the active object belongs to.

        Args:
            context (bpy.Context): context

        Returns:
            list[bpy.types.EnumPropertyItem]: enum items
        """
        enum_items = []

        if context is None:
            return enum_items

        obj = context.active_object
        collections = get_object_owning_collections(obj)

        for coll in collections:
            item = (coll.name, coll.name, "")
            enum_items.append(item)

        return sorted(enum_items)


    def update_active_collection(self, context):
        """Updates the active collection

        Args:
            context (bpy.Context): context
        """
        activate_collection(self.OwningCollection)

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

    RootObject: EnumProperty(
        name="Root Object",
        items=create_root_object_enums,
        description="Object that all other objects in this collection are parented to. Select None to create a new empty object"
    )

    OwningCollection: EnumProperty(
        name="Collection",
        items=create_owning_collection_enums,
        update=update_active_collection,
        description="Collection to save."
    )

    def execute(self, context):
        return add_collection_to_library(
            self,
            context,
            bpy.data.collections[self.OwningCollection],
            self.RootObject)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'RootObject')
        layout.prop(self, 'OwningCollection')
        draw_save_props_menu(self, context)


def add_collection_to_library(self, context, collection, root_obj_name):
    """Add the passed in collection to the MakeTile Library.

    Args:
        context (bpy.Context): context
        collection (bpy.types.Collection): collection
        root_obj_name (str): name of root object

    Returns:
        Enum in {'FINISHED', 'CANCELLED'}: Operator return
    """
    obj = context.active_object
    props = context.scene.mt_am_props
    prefs = get_prefs()
    assets_path = prefs.user_assets_path
    asset_type = "COLLECTIONS"

    # if user doesn't choose one of the existing objects as the root object create a new empty
    # and move it to the origin of the active object
    if root_obj_name == "NEW_EMPTY_ROOT":
        root = bpy.data.objects.new(collection.name + ' Root', None)
        collection.objects.link(root)
        root.location = obj.location
        root.show_in_front = True
        context.view_layer.update()

    else:
        root = bpy.data.objects[root_obj_name]

    # parent all objects in collection that don't already have a parent
    # to the root object
    for ob in collection.objects:
        if ob != root:
            if ob.parent is None:
                ob.parent = root
                ob.matrix_parent_inverse = root.matrix_world.inverted()

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
        "License": self.License,
        "RootObject": root.name}

    asset_desc = add_asset_to_library(
        self,
        context,
        props,
        collection,
        assets_path,
        asset_type,
        category,
        self.Tags,
        **kwargs)

    scene_path = os.path.join(
        prefs.default_assets_path,
        "previews",
        "preview_scenes.blend")

    render_collection_preview(
        context,
        asset_desc['PreviewImagePath'],
        scene_path,
        prefs.preview_scene,
        collection)

    props.assets_updated = True

    return {'FINISHED'}