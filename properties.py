import bpy
from bpy.types import PropertyGroup


class MT_PT_AM_Props(PropertyGroup):
    active_category: bpy.props.StringProperty(
        name="Active Category",
        default="",
        description="The active category."
    )

    parent_category: bpy.props.StringProperty(
        name="Parent Category",
        default="",
        description="The parent of the current active category."
    )



def register():
    bpy.types.Scene.mt_am_props = bpy.props.PointerProperty(
        type=MT_PT_AM_Props
    )


def unregister():
    del bpy.types.Scene.mt_am_props
