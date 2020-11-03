import os
import json
import bpy
from bpy.types import Operator
from bpy.props import StringProperty, PointerProperty, BoolProperty

class MT_OT_AM_Delete_Asset_from_Library(Operator):
    """Operator that deletes asset from MakeTile library and optionally from disk."""
    bl_idname = "object.delete_asset_from_library"
    bl_label = "Delete asset from Library"
    bl_description = "Deletes asset from the MakeTile Library and optionally from disk"

    def execute(self, context):
        print("Deleting asset")
        return {'FINISHED'}