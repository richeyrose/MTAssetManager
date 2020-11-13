import os
import json
import bpy
from bpy.types import Operator
from bpy.props import StringProperty
from bpy.props import EnumProperty
from .preferences import get_prefs
from .categories import get_child_cats
from .utils import slugify, tagify, find_and_rename

class MT_OT_AM_Edit_Asset_Metadata(Operator):
    bl_idname = "object.mt_am_edit_asset_metadata"
    bl_label = "Edit Asset Metadata"
    bl_description = "Edit Asset Metadata"

    Name: StringProperty(
        name="Name",
        default=""
    )

    FilePath: StringProperty(
        name="Filepath",
        subtype='FILE_PATH'
    )

    PreviewImagePath: StringProperty(
        name="Preview Image Path",
        subtype='FILE_PATH'
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
        name="Tags"
    )

    def execute(self, context):
        props = context.scene.mt_am_props
        prefs = get_prefs()
        orig_asset_desc = props.current_asset_desc
        assets = getattr(props, orig_asset_desc["Type"].lower())

        # remove asset from in memory list
        assets.remove(orig_asset_desc)

        # construct new asset description
        asset_desc = {
            "Name": self.Name,
            "Slug": orig_asset_desc["Slug"],
            "Category": orig_asset_desc["Category"],
            "FileName": os.path.basename(self.FilePath),
            "FilePath": self.FilePath,
            "PreviewImagePath": self.PreviewImagePath,
            "PreviewImageName": os.path.basename(self.PreviewImagePath),
            "Description": self.Description,
            "URI": self.URI,
            "Author": self.Author,
            "License": self.License,
            "Type": orig_asset_desc["Type"],
            "Tags": tagify(self.Tags)}

        # append new asset description
        assets.append(asset_desc)

        json_file = os.path.join(
            prefs.user_assets_path,
            "data",
            orig_asset_desc["Type"].lower() + ".json")

        if os.path.exists(json_file):
            with open(json_file, "w") as write_file:
                json.dump(assets, write_file, indent=4)

        props.assets_updated = True
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "Name")
        layout.prop(self, "Description")
        layout.prop(self, "FilePath")
        layout.prop(self, "PreviewImagePath")
        layout.prop(self, "URI")
        layout.prop(self, "Author")
        layout.prop(self, "License")
        layout.prop(self, "Tags")

