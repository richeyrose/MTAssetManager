"""Contains helper functions for adding assets to MakeTile library..."""
import os
from pathlib import Path
import bpy
from bpy.props import StringProperty, EnumProperty, BoolProperty
from bpy.types import Operator
from ..utils import slugify, tagify, find_and_rename
from ..preferences import create_license_enums, get_prefs
from .preview_rendering import render_collection_preview, render_material_preview, render_object_preview
from ..collections import get_all_descendent_collections, get_object_owning_collections, activate_collection


class MT_Save_To_Library:
    """Mixin for save operators."""
    preview_img: StringProperty(
        name="Preview Image Name"
    )

    name: StringProperty(
        name="Name",
        default=''
    )

    desc: StringProperty(
        name="Description",
        default=""
    )

    author: StringProperty(
        name="Author",
        default=""
    )

    license: EnumProperty(
        items=create_license_enums,
        name="License",
        description="License for asset use")

    tags: StringProperty(
        name="Tags",
        description="Comma seperated list",
        default=""
    )

    save_directory: StringProperty(
        name="Save Directory",
        subtype="DIR_PATH"
    )

    def draw_save_props_menu(self, context):
        """Draw a pop up menu for entering properties.

        Args:
            context (bpy.Context): context
        """
        props = context.scene.mt_am_props
        layout = self.layout
        layout.prop(self, 'desc')
        layout.prop(self, 'author')
        layout.prop(self, 'license')
        layout.prop(self, 'tags')
        layout.prop(props, 'current_path', text="Save Directory")


    def add_asset_to_library(self, asset, asset_desc, preview_img = None, del_preview=True):
        """Add the passed in asset to the asset library.

        Args:
            asset (bpy.types.object, material, collection): the asset to add
            asset_desc (dict): dict containing imagepath, filepath, filename
            preview_img (bpy.types.Image): Preview Image. Default None
            del_preview (bool): Whether to delete the source file for the preview image.

        Returns:
            dict: asset_desc
        """
        imagepath = asset_desc['imagepath']
        assetpath = os.path.join(asset_desc['filepath'], asset_desc['filename'])

        if preview_img:
            # save asset preview image to asset
            asset.mt_preview_img = preview_img
            preview_img.pack()


        # save asset in individual file
        if not os.path.exists(asset_desc['filepath']):
            os.makedirs(asset_desc['filepath'])

        ids = {asset}

        if preview_img:
            ids.add(preview_img)

        bpy.data.libraries.write(
            assetpath,
            ids,
            fake_user=True)

        # # delete external image
        if del_preview:
            if os.path.exists(imagepath):
                os.remove(imagepath)

        self.report({'INFO'}, asset.name + " added to Library.")

        return asset_desc


    def construct_asset_description(self, props, asset, save_path=None, **kwargs):
        if not save_path:
            asset_save_path = props.current_path
        else:
            asset_save_path = save_path

        # create a unique (within this directory) slug for our file
        slug = slugify(asset.name)

        # list of .blend file stem names in asset_save_path:
        try:
            blends = [f for f in os.listdir(asset_save_path) if os.path.isfile(os.path.join(asset_save_path, f)) and f.endswith(".blend")]
            stems = [Path(blend).stem for blend in blends]
        except FileNotFoundError:
            os.makedirs(asset_save_path)
            stems=[]

        # check if slug already exists and increment and rename if not.
        if stems:
            slug = find_and_rename(slug, stems)

        # construct dict for saving to .json cache file
        asset_desc = {
            "slug": slug,
            "filename": slug + '.blend',
            "filepath": asset_save_path,
            "imagepath": os.path.join(asset_save_path, slug + '.png')}

        for key, value in kwargs.items():
            asset_desc[key] = value

        return asset_desc


    def mark_as_asset(self, asset, asset_desc, tags):
        """Save asset as blender asset for blender's internal asset browser.

        Args:
            asset (ID data block): Asset
            asset_desc (dict): asset description
            tags (list[str]): list of tags
        """

        # Clear any existing asset data and then mark as asset
        asset.asset_clear()
        asset.asset_mark()
        asset_data = asset.asset_data

        # set asset preview
        ctx = {'id': asset}
        imagepath = asset_desc['imagepath']
        if os.path.isfile(imagepath):
            bpy.ops.ed.lib_id_load_custom_preview(ctx, filepath=imagepath)

        # set asset description
        asset_data.description = asset_desc['desc']

        # set asset tags
        for tag in tags:
            if tag:
                asset_data.tags.new(tag, skip_if_exists=True)

        # set author
        asset_data.author = asset_desc['author']

        # set custom license prop
        asset_data.mt_license = asset_desc['license']

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

class MT_OT_Set_Object_Bool_Type(Operator, MT_Save_To_Library):
    """Set the object type for objects saved as part of a ARCH_ELEM collection."""

    bl_idname = "collection.set_object_type"
    bl_label = "Set Object Propertis."
    bl_description = "Set the properties for objects saved as part of an architectural element collection."

    name: StringProperty(
        name="Name",
        default=""
    )

    desc: StringProperty(
        name="desc",
        default=""
    )

    author: StringProperty(
        name="author",
        default=""
    )

    license: EnumProperty(
        items=create_license_enums,
        name="License",
        description="License for asset use")

    tags: StringProperty(
        name="tags",
        description="Comma seperated list",
        default=""
    )

    root_object: StringProperty(
        name="Root Object",
        description="Object that all other objects in this collection are parented to. Select None to create a new empty object"
    )

    owning_collection: StringProperty(
        name="Collection",
        description="Collection to save."
    )

    collection_type: StringProperty(
        name="Collection Type",
        description="Collection Type."
    )

    def execute(self, context):
        return add_collection_to_library(self, context)

    def invoke(self, context, event):
        collection = bpy.data.collections[self.owning_collection]
        objects = sorted(
            [obj for obj in collection.objects if obj.type == 'MESH'],
            key=lambda obj: obj.name)

        for i, obj in enumerate(objects):
            obj.mt_object_props.boolean_order = i

        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        collection = bpy.data.collections[self.owning_collection]
        objects = sorted([obj for obj in collection.objects if obj.type == 'MESH'], key=lambda obj: obj.name)
        layout = self.layout
        layout.use_property_decorate = False

        for obj in objects:
            row = layout.row(align=True)
            row.prop(obj, "name")
            row.prop(obj.mt_object_props, "boolean_type", text="")
            row.prop(obj.mt_object_props, "boolean_order", text="")


class MT_OT_Add_Collection_To_Library(Operator, MT_Save_To_Library):
    """Add the active object's owning collection to the MakeTile Library."""

    bl_idname = "collection.add_collection_to_library"
    bl_label = "Save collection to library"
    bl_description = "Add the active object's owning collection to the MakeTile Library"

    def create_root_object_enums(self, context):
        """Return an enum list constructed out of a list of objects in a collection
        that don't have parents.

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
        """Update the active collection

        Args:
            context (bpy.Context): context
        """
        activate_collection(self.owning_collection)


    name: StringProperty(
        name="Name",
        default="Collection"
    )

    root_object: EnumProperty(
        name="Root Object",
        items=create_root_object_enums,
        description="Object that all other objects in this collection are parented to. Select None to create a new empty object"
    )

    owning_collection: EnumProperty(
        name="Collection",
        items=create_owning_collection_enums,
        update=update_active_collection,
        description="Collection to save."
    )

    collection_type: EnumProperty(
        name="Collection Type",
        items=create_collection_type_enums,
        description="Collection Type."
    )

    def execute(self, context):
        if self.collection_type == 'ARCH_ELEMENT':
            return bpy.ops.collection.set_object_type(
                'INVOKE_DEFAULT',
                name=self.name,
                desc=self.desc,
                author=self.author,
                license=self.license,
                tags=self.tags,
                root_object=self.root_object,
                owning_collection=self.owning_collection)
        else:
            return add_collection_to_library(self, context)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'name')
        layout.prop(self, 'owning_collection')
        layout.prop(self, 'collection_type')
        layout.prop(self, 'root_object')
        self.draw_save_props_menu(context)

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
    collection = bpy.data.collections[self.owning_collection]
    root_obj_name = self.root_object

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

    tags = tagify(self.tags)

    kwargs = {
        "desc": self.desc,
        "author": self.author,
        "license": self.license,
        "tags": tags,
        "root_object": root.name}

    asset_desc = self.construct_asset_description(
        props,
        collection,
        **kwargs)

    # for collections we set this here because it's hard to know what collection the user wants to
    # save in advance.
    asset_desc['name'] = self.name

    scene_path = os.path.join(
        prefs.default_assets_path,
        "previews",
        "preview_scenes.blend")

    imagepath = asset_desc['imagepath']

    img = render_collection_preview(
            self,
            context,
            imagepath,
            scene_path,
            prefs.preview_scene,
            collection)

    if hasattr(collection, 'asset_data'):
        self.mark_as_asset(collection, asset_desc, tags)

    self.add_asset_to_library(
        collection,
        asset_desc,
        img)

    props.assets_updated = True

    return {'FINISHED'}