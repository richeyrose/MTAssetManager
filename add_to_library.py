import os
import json
import bpy
from bpy.types import Operator
from bpy.props import StringProperty
from .utils import slugify, tagify, find_and_rename
from .preferences import get_prefs
from .previews import render_object_preview

class MT_OT_AM_Add_Multiple_Object_To_Library(Operator):
    """Operator that adds all selected mesh objects to the MakeTile Library."""
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

        for obj in obs:
            asset_desc = add_asset_to_library(
                self,
                context,
                props,
                obj,
                assets_path,
                "objects")

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

        asset_desc = add_asset_to_library(
            self,
            context,
            props,
            obj,
            assets_path,
            "objects",
            self.Description,
            self.URI,
            self.Author,
            self.License,
            self.Tags)

        scene_path = os.path.join(
            prefs.default_assets_path,
            "previews",
            "preview_scenes.blend")

        render_object_preview(self, context, asset_desc['PreviewImagePath'], scene_path, prefs.preview_scene, obj)
        props.assets_updated = True

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


def add_asset_to_library(self, context, props, asset, assets_path, asset_type, description="", URI="", author="", license="", tags=""):
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

    # check if slug already exists and increment and rename if not.
    new_slug = find_and_rename(self, asset.name, slug, current_slugs)

    pretty_name = asset.name  # when we reimport an asset we will rename it to this

    asset.name = new_slug

    # check if we're in a sub category. If not add the object to the
    # root category for its type
    if props.active_category == "":
        category = asset_type
    else:
        category = props.active_category

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
        "Description": description,
        "URI": URI,
        "Author": author,
        "License": license,
        "Type": asset_type.upper(),
        "Tags": tagify(tags)}

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
        os.path.join(filepath),
        {asset},
        fake_user=True)

    # change asset name back to pretty_name
    asset.name = pretty_name

    self.report({'INFO'}, pretty_name + " added to Library.")

    return asset_desc


def draw_object_context_menu_items(self, context):
    """Add options to object right click context menu."""
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

def register():
    """Register."""
    bpy.types.VIEW3D_MT_object_context_menu.append(draw_object_context_menu_items)

def unregister():
    """UnRegister."""
    bpy.types.VIEW3D_MT_object_context_menu.remove(draw_object_context_menu_items)