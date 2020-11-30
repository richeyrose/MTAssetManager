import os
import json
import bpy
from bpy.types import Operator
from bpy.props import StringProperty, BoolProperty, EnumProperty
from .utils import slugify, tagify, find_and_rename
from .preferences import get_prefs
from .previews import render_object_preview, render_material_preview, render_collection_preview
from .collections import get_object_owning_collections, activate_collection


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
        if context.object is not None:
            return context.object.active_material is not None
        return False

    def execute(self, context):
        material = context.active_object.active_material

        if self.DisplacementMaterial:
            material['mt_material'] = True

        props = context.scene.mt_am_props
        prefs = get_prefs()
        assets_path = prefs.user_assets_path

        asset_type = "MATERIALS"

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
            material,
            assets_path,
            "MATERIALS",
            category,
            self.Tags,
            **kwargs)

        scene_path = os.path.join(
            prefs.default_assets_path,
            "previews",
            "preview_scenes.blend")

        # Preview object should be a choice between wall, floor, roof, base etc.
        # TODO implement mini base and roof preview objects
        preview_obj = self.PreviewObject
        render_material_preview(self, context, asset_desc['PreviewImagePath'], scene_path, prefs.preview_scene, material, preview_obj)

        props.assets_updated = True
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.prop(context.active_object.active_material, 'name')
        draw_save_props_menu(self, context)
        layout.prop(self, 'DisplacementMaterial')
        layout.prop(self, 'PreviewObject')


class MT_OT_AM_Add_Multiple_Objects_To_Library(Operator):
    """Add all selected mesh objects to the MakeTile Library."""

    bl_idname = "object.add_selected_objects_to_library"
    bl_label = "Add selected objects to library"
    bl_description = "Adds selected objects to the MakeTile Library"

    @classmethod
    def poll(cls, context):
        if len(context.selected_editable_objects) > 0:
            for obj in context.selected_editable_objects:
                if obj.type == 'MESH':
                    return True
        return

    def execute(self, context):
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
    """Operator that adds active mesh object to the MakeTile Library."""

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
        return context.active_object and context.active_object.type == 'MESH' and len(context.selected_objects) > 0

    def execute(self, context):
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
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.prop(context.active_object, 'name')
        draw_save_props_menu(self, context)


def check_category_type(category, asset_type):
    """Return category["Slug"] if category contains assets of the correct asset type.

    If not we return root category for that asset type

    Args:
        category (dict): MakeTile category
        asset_type (ENUM in 'OBJECTS', 'MATERIALS', 'COLLECTIONS'): type of asset to save

    Returns:
        str: category_slug
    """
    # TODO: Create a popup to choose category
    # TODO: Ensure asset bar switches to active category
    if category["Contains"] == asset_type:
        category_slug = category["Slug"]
    else:
        category_slug = asset_type.lower()
    return category_slug


def draw_save_props_menu(self, context):
    """Draw a pop up menu for entering properties.

    Args:
        context (bpy.Context): context
    """
    layout = self.layout
    layout.prop(self, 'Description')
    layout.prop(self, 'URI')
    layout.prop(self, 'Author')
    layout.prop(self, 'License')
    layout.prop(self, 'Tags')


def add_asset_to_library(self, context, props, asset, assets_path, asset_type, category, tags="", **kwargs):
    """Add the passed in asset to the asset library.

    Args:
        context (bpy.Context): context
        props (scene.mt_am_props): asset manager properties
        asset (bpy.types.object, material, collection): the asset to add
        assets_path (path): the path to the root assets foldere
        asset_type (enum in {OBJECTS, COLLECTIONS, MATERIALS}): asset type
        category (dict): MakeTile category
        tags (str, optional): Comma seperated list of tags. Used for searching. Defaults to "".
        **kwargs: additional fields. Usually Description, Author, URI, License

    Returns:
        dict: asset_desc
    """
    assets = getattr(props, asset_type.lower())

    asset_save_path = os.path.join(
        assets_path,
        asset_type.lower()
    )

    json_path = os.path.join(
        assets_path,
        "data"
    )

    slug = slugify(asset.name)
    current_slugs = [asset['Slug'] for asset in assets]

    # check if slug already exists and increment and rename if not.
    new_slug = find_and_rename(slug, current_slugs)

    pretty_name = asset.name  # when we reimport an asset we will rename it to this

    asset.name = new_slug

    filepath = os.path.join(
        asset_save_path,
        new_slug + '.blend')

    imagepath = os.path.join(
        asset_save_path,
        new_slug + '.png')

    # construct dict for saving to users objects.json
    asset_desc = {
        "Name": pretty_name,
        "Slug": new_slug,
        "Category": category,
        "FileName": new_slug + '.blend',
        "FilePath": filepath,
        "PreviewImagePath": imagepath,
        "PreviewImageName": new_slug + '.png',
        "Type": asset_type.upper(),
        "Tags": tagify(tags)}

    for key, value in kwargs.items():
        asset_desc[key] = value
    # update current objects list
    assets = assets.append(asset_desc)

    if not os.path.exists(json_path):
        os.makedirs(json_path)

    # open user asset description file and then write description to file
    file_assets = []
    json_file = os.path.join(json_path, asset_type.lower() + '.json')

    if os.path.exists(json_file):
        with open(json_file) as read_file:
            file_assets = json.load(read_file)

    file_assets.append(asset_desc)

    # write description to .json file
    with open(json_file, "w") as write_file:
        json.dump(file_assets, write_file, indent=4)

    # save asset to library file
    if not os.path.exists(asset_save_path):
        os.makedirs(asset_save_path)

    bpy.data.libraries.write(
        os.path.join(filepath),
        {asset},
        fake_user=True)

    # change asset name back to pretty_name
    asset.name = pretty_name

    self.report({'INFO'}, pretty_name + " added to Library.")

    return asset_desc


def draw_object_context_menu_items(self, context):
    """Add save options to object right click context menu."""
    layout = self.layout
    if context.active_object.type in ['MESH']:
        layout.separator()
        layout.operator_context = 'INVOKE_DEFAULT'
        layout.operator(
            "object.add_active_object_to_library",
            text="Save active object to MakeTile Library")
        layout.operator(
            "object.add_selected_objects_to_library",
            text="Save all selected objects to MakeTile Library")
        layout.operator(
            "material.mt_ot_am_add_material_to_library",
            text="Save active material to MakeTile Library"
        )
    if context.active_object.type in ['MESH', 'EMPTY']:
        layout.operator(
            "collection.add_collection_to_library",
            text="Save active object's owning collection to MakeTile Library"
        )


def register():
    """Register aditional options in object context (right click) menu."""
    bpy.types.VIEW3D_MT_object_context_menu.append(draw_object_context_menu_items)


def unregister():
    """UnRegister."""
    bpy.types.VIEW3D_MT_object_context_menu.remove(draw_object_context_menu_items)