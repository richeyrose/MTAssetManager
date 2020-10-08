import bpy
from bpy.props import StringProperty, EnumProperty

mt_types = [
    ("OBJECT", "Object", ""),
    ("COLLECTION", "Collection", ""),
    ("MATERIAL", "Material", "")]


mt_licenses = [
    ("ARR", "All RIghts Reserved", ""),
    ("CC0", "CC0", "")]


def get_cat_enums():
    return


def get_assets_by_cat(category):
    pass