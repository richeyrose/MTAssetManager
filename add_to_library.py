import os
import json
import bpy
from bpy.types import Operator
from bpy.props import StringProperty
from .utils import slugify, find_and_rename
from .preferences import get_prefs

class MT_OT_AM_Add_Selected_Object_To_Library(Operator):
    """Operator that adds selected mesh object to the MakeTile Library."""
    bl_idname = "object.add_selected_to_library"
    bl_label = "Add selected object to library"
    bl_options = {'REGISTER'}
    bl_description = "Adds selected mesh object to the MakeTile Library"

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

    def execute(self, context):
        obj = context.active_object
        props = context.scene.mt_am_props
        prefs = get_prefs()
        assets_path = prefs.user_assets_path
        add_asset_to_library(self, context, props, obj, assets_path, "objects", self.Description, self.URI, self.Author, self.License)
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        obj = context.active_object
        layout = self.layout
        layout.prop(obj, 'name')
        layout.prop(self, 'Description')
        layout.prop(self, 'URI')
        layout.prop(self, 'Author')
        layout.prop(self, 'License')
        layout.prop(self, 'Tags')


def add_asset_to_library(self, context, props, asset, assets_path, asset_type, description="", URI="", Author="", License=""):
    assets = getattr(props, asset_type)

    asset_save_path = os.path.join(
        assets_path,
        asset_type
    )

    json_path = os.path.join(
        assets_path,
        "data"
    )

    slug = slugify(asset.name)
    current_slugs = [asset['Slug'] for asset in assets]

    # check if slug already exists and increment and rename if not
    new_slug = find_and_rename(self, asset, slug, current_slugs)

    # check if we're in a sub category. If not add the object to the
    # root category for its type
    if props.active_category == "":
        category = asset_type

    # construct dict for saving to users objects.json
    asset_desc = {
        "Name": asset.name,
        "Slug": new_slug,
        "Category": category,
        "FileName": new_slug + '.blend',
        "FilePath": asset_save_path,
        "PreviewImagePath": asset_save_path,
        "PreviewImageName": new_slug + '.png',
        "Description": description,
        "URI": URI,
        "Author": Author,
        "License": License,
        "Type": asset_type.upper(),
        "Tags": []}

    # update current objects list
    assets = assets.append(asset_desc)


    if not os.path.exists(json_path):
        os.makedirs(json_path)

    # open user asset description file and then write description to file
    file_assets = []
    json_file = os.path.join(json_path, asset_type + '.json')

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
        os.path.join(asset_save_path, new_slug + '.blend'),
        {asset},
        fake_user=True)

def draw_object_context_menu_items(self, context):
    """Add options to object right click context menu."""
    layout = self.layout
    if context.active_object.type in ['MESH']:
        layout.separator()
        layout.operator_context = 'INVOKE_DEFAULT'
        layout.operator(
            "object.add_selected_to_library",
            text="Save active object to MakeTile Library"
        )

def register():
    """Register."""
    bpy.types.VIEW3D_MT_object_context_menu.append(draw_object_context_menu_items)

def unregister():
    """UnRegister."""
    bpy.types.VIEW3D_MT_object_context_menu.remove(draw_object_context_menu_items)