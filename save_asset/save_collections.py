"""This module contains classes and functions related to the saving of collections as assets."""

import os
import bpy
from bpy.types import Operator
from bpy.props import StringProperty, EnumProperty, BoolProperty
from ..collections import (
    get_object_owning_collections,
    activate_collection,
    get_all_descendent_collections)
from .add_to_library import (
    draw_save_props_menu,
    check_category_type,
    add_asset_to_library,
    construct_asset_description,
    save_as_blender_asset)
from ..preferences import get_prefs
from .preview_rendering import render_collection_preview
from ..utils import tagify

class MT_OT_Set_Object_Bool_Type(Operator):
    """Set the object type for objects saved as part of a ARCH_ELEM collection."""

    bl_idname = "collection.set_object_type"
    bl_label = "Set Object Propertis."
    bl_description = "Set the properties for objects saved as part of an architectural element collection."

    Name: StringProperty(
        name="Name",
        default=""
    )

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

    RootObject: StringProperty(
        name="Root Object",
        description="Object that all other objects in this collection are parented to. Select None to create a new empty object"
    )

    OwningCollection: StringProperty(
        name="Collection",
        description="Collection to save."
    )

    CollectionType: StringProperty(
        name="Collection Type",
        description="Collection Type."
    )

    def execute(self, context):
        return add_collection_to_library(self, context)

    def invoke(self, context, event):
        collection = bpy.data.collections[self.OwningCollection]
        objects = sorted([obj for obj in collection.objects if obj.type == 'MESH'], key=lambda obj: obj.name)

        for i, obj in enumerate(objects):
            obj.mt_object_props.boolean_order = i

        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        collection = bpy.data.collections[self.OwningCollection]
        objects = sorted([obj for obj in collection.objects if obj.type == 'MESH'], key=lambda obj: obj.name)
        layout = self.layout
        layout.use_property_decorate = False

        for obj in objects:
            row = layout.row(align=True)
            row.prop(obj, "name")
            row.prop(obj.mt_object_props, "boolean_type", text="")
            row.prop(obj.mt_object_props, "boolean_order", text="")


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

    def create_collection_type_enums(self, context):
        enum_items = []

        if context is None:
            return enum_items

        return [
            ("TILE", "Tile", ""),
            # e.g. a doorway or window that should be added to a tile rather than printed on its own
            ("ARCH_ELEMENT", "Architectural Element", ""),
            # a building type prefab consisting of multiple tiles to be printed separately
            # ("BUILDING", "Building", ""),
            # A generic collection
            ("OTHER", "Other", "")]

    def update_active_collection(self, context):
        """Updates the active collection

        Args:
            context (bpy.Context): context
        """
        activate_collection(self.OwningCollection)

    Name: StringProperty(
        name="Name",
        default="Collection"
    )

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

    CollectionType: EnumProperty(
        name="Collection Type",
        items=create_collection_type_enums,
        description="Collection Type."
    )

    def execute(self, context):
        if self.CollectionType == 'ARCH_ELEMENT':
            return bpy.ops.collection.set_object_type(
                'INVOKE_DEFAULT',
                Name=self.Name,
                Description=self.Description,
                URI=self.URI,
                Author=self.Author,
                License=self.License,
                Tags=self.Tags,
                RootObject=self.RootObject,
                OwningCollection=self.OwningCollection)
        else:
            return add_collection_to_library(
                self,
                context)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'Name')
        layout.prop(self, 'RootObject')
        layout.prop(self, 'OwningCollection')
        layout.prop(self, 'CollectionType')
        draw_save_props_menu(self, context)


def add_collection_to_library(self, context):
    """Add the passed in collection to the MakeTile Library.

    Args:
        context (bpy.Context): context
    Returns:
        Enum in {'FINISHED', 'CANCELLED'}: Operator return
    """
    obj = context.active_object
    props = context.scene.mt_am_props
    prefs = get_prefs()
    assets_path = prefs.user_assets_path
    asset_type = "COLLECTIONS"
    collection = bpy.data.collections[self.OwningCollection]
    root_obj_name = self.RootObject

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

    root.mt_object_props.geometry_type = 'BASE'

    # we need to make sure we parent all objects, including those in sub collections
    # to our root
    colls = set(get_all_descendent_collections(collection))
    colls.add(collection)

    all_obs = set()

    for coll in colls:
        for obj in coll.objects:
            all_obs.add(obj)

    # parent all objects that don't already have a parent
    # to the root object
    for ob in all_obs:
        if ob != root:
            if ob.parent is None:
                ob.parent = root
                ob.matrix_parent_inverse = root.matrix_world.inverted()

    tags = tagify(self.Tags)

    kwargs = {
        "Description": self.Description,
        "URI": self.URI,
        "Author": self.Author,
        "License": self.License,
        "Tags": tags,
        "RootObject": root.name}

    asset_desc = construct_asset_description(
        props,
        asset_type,
        assets_path,
        collection,
        **kwargs)

    # for collections we set this here because it's hard to know what collection the user wants to
    # save in advance.
    asset_desc['Name'] = self.Name

    scene_path = os.path.join(
        prefs.default_assets_path,
        "previews",
        "preview_scenes.blend")


    img = render_collection_preview(
            self,
            context,
            asset_desc['PreviewImagePath'],
            scene_path,
            prefs.preview_scene,
            collection)
    if img:
        if hasattr(collection, 'asset_data'):
            save_as_blender_asset(collection, asset_desc, tags)

        add_asset_to_library(
            self,
            context,
            collection,
            asset_type,
            asset_desc,
            img)

        props.assets_updated = True

        return {'FINISHED'}

    return {'CANCELLED'}
