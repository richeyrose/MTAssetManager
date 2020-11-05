import bpy
from bpy.types import Operator

class MT_OT_AM_Cut_Asset(Operator):
    bl_idname = "object.mt_cut_asset"
    bl_label = "Cut Asset"
    bl_description = "Cut Asset"

    def execute(self, context):
        return {'FINISHED'}


class MT_OT_AM_Copy_Asset(Operator):
    bl_idname = "object.mt_copy_asset"
    bl_label = "Copy Asset"
    bl_description = "Copy Asset"

    def execute(self, context):
        return {'FINISHED'}


class MT_OT_AM_Paste_Asset(Operator):
    bl_idname = "object.mt_paste_asset"
    bl_label = "Paste Asset"
    bl_description = "Paste Asset"

    @classmethod
    def poll(cls, context):
        return context.scene.mt_am_props.copied_asset

    def execute(self, context):
        props = context.scene.mt_am_props


        props.copied_asset = None
        return {'FINISHED'}

