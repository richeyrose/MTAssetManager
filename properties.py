import bpy
from bpy.types import PropertyGroup

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



def register():
    bpy.types.Scene.mt_am_props = bpy.props.PointerProperty(
        type=MT_PT_AM_Props
    )


def unregister():
    del bpy.types.Scene.mt_am_props
