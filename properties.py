import math
import bpy
from bpy.types import PropertyGroup
from bpy.props import StringProperty, BoolProperty, EnumProperty, PointerProperty

def get_cat_enums():
    mt_cats = [
        ("collections", "collections", ""),
        ("collections\\tiles", "collections\\tiles", ""),
        ("collections\\tiles\\walls", "collections\\tiles\\walls", ""),
        ("objects", "objects", ""),
        ("objects\\booleans", "objects\\booleans", ""),
        ("materials", "materials", "")]
    return mt_cats


def get_license_enums():
    mt_licenses = [
        ("ARR", "All RIghts Reserved", ""),
        ("CC0", "CC0", "")]
    return mt_licenses


def get_type_enums():
    mt_types = [
        ("OBJECT", "Object", ""),
        ("COLLECTION", "Collection", ""),
        ("MATERIAL", "Material", "")]
    return mt_types


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


class MT_PT_AM_Bar_Props(PropertyGroup):
    visible: bpy.props.BoolProperty(
        name="Visible",
        description="Whether asset bar is visible.",
        default=False
    )

    item_margin: bpy.props.IntProperty(
        name="Item Margin",
        default=5,
        description="Margin around each item in asset bar"
    )

    end_margin: bpy.props.IntProperty(
        name="End Margin",
        default=25,
        description="Marging to leave at end of asset bar for forward and back buttons"
    )

    first_visible_asset: bpy.props.IntProperty(
        name="First visible asset",
        description="The index of the first asset that is visible in the asset bar",
        default=0
    )

    last_visible_asset: bpy.props.IntProperty(
        name="Last Visible asset",
        description="Index of the last asset that is visible in the asset bar",
        default=0
    )


class MT_PT_AM_Object_Spawn_Props(PropertyGroup):
    randomize_rotation: bpy.props.BoolProperty(
        name='Randomize Rotation',
        description="randomize rotation at placement",
        default=False)

    randomize_rotation_amount: bpy.props.FloatProperty(
        name="Randomization Max Angle",
        description="maximum angle for random rotation",
        default=math.pi / 36,
        min=0,
        max=2 * math.pi,
        subtype='ANGLE')

    offset_rotation_amount: bpy.props.FloatProperty(
        name="Offset Rotation",
        description="offset rotation, hidden prop",
        default=0,
        min=0,
        max=360,
        subtype='ANGLE')

    offset_rotation_step: bpy.props.FloatProperty(
        name="Offset Rotation Step",
        description="offset rotation, hidden prop",
        default=math.pi / 2,
        min=0,
        max=180,
        subtype='ANGLE')

def register():
    bpy.types.Scene.mt_am_props = bpy.props.PointerProperty(
        type=MT_PT_AM_Props
    )

    bpy.types.Scene.mt_bar_props = bpy.props.PointerProperty(
        type=MT_PT_AM_Bar_Props
    )

    bpy.types.Scene.mt_am_spawn_props = bpy.props.PointerProperty(
        type=MT_PT_AM_Object_Spawn_Props
    )

def unregister():
    del bpy.types.Scene.mt_am_spawn_props
    del bpy.types.Scene.mt_bar_props
    del bpy.types.Scene.mt_am_props
