import bpy
from bpy.types import Operator
from bpy.props import StringProperty
from bpy.props import EnumProperty
from .categories import get_child_cats

class MT_OT_AM_Edit_Asset_Metadata(Operator):
    bl_idname = "object.mt_am_edit_asset_metadata"
    bl_label = "Edit Asset Metadata"
    bl_description = "Edit Asset Metadata"

    Name: StringProperty(
        name="Name",
        default=""
    )

    Slug: StringProperty(
        name="Slug",
        default="",
        options={'HIDDEN'}
    )

    FileName: StringProperty(
        options={'HIDDEN'}
    )

    FilePath: StringProperty(
        name="Filepath",
        subtype='FILE_PATH'
    )

    PreviewImagePath: StringProperty(
        name="Preview Image Path",
        subtype='FILE_PATH'
    )

    PreviewImageName: StringProperty(
        options={'HIDDEN'}
    )

    Category: StringProperty(
        name="Category",
        default="",
        options={'HIDDEN'}
    )

    Type: StringProperty(
        name="Type",
        default="",
        options={'HIDDEN'}
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

