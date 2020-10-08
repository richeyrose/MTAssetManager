import bpy
from bpy.props import StringProperty, EnumProperty
from .categories import get_category

mt_types = [
    ("OBJECT", "Object", ""),
    ("COLLECTION", "Collection", ""),
    ("MATERIAL", "Material", "")]


mt_licenses = [
    ("ARR", "All RIghts Reserved", ""),
    ("CC0", "CC0", "")]


def get_assets_by_cat(cat_slug):
    """Return a list of asset descriptions belonging to the category.

    Args:
        cat_slug (string): category slug

    Returns:
        list: asset descriptions
    """
    props = bpy.context.scene.mt_am_props
    category = get_category(props['categories'], cat_slug)
    if "Contains" in category:
        if category['Contains'] == 'OBJECTS':
            return [obj for obj in props['objects'] if obj['Category'] == category['Slug']]
        elif category['Contains'] == 'COLLECTIONS':
            return [coll for coll in props['collections'] if coll['Category'] == category['Slug']]
        elif category['Contains'] == 'MATERIALS':
            return [mat for mat in props['materials'] if mat['Category'] == category['Slug']]
    return []
