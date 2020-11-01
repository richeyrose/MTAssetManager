import os
import bpy
from bpy.props import StringProperty, EnumProperty
from .categories import get_category

def get_assets_by_cat(cat_slug):
    """Return a list of asset descriptions belonging to the category.

    Args:
        cat_slug (string): category slug

    Returns:
        list: asset descriptions
    """
    props = bpy.context.scene.mt_am_props

    category = get_category(props.categories, cat_slug)
    assets = []
    if "Contains" in category:
        if category['Contains'] == 'OBJECTS':
            assets = [obj for obj in props.objects if obj['Category'] == category['Slug']]
            return assets
        if category['Contains'] == 'COLLECTIONS':
            assets = [coll for coll in props.collections if coll['Category'] == category['Slug']]
            return assets
        if category['Contains'] == 'MATERIALS':
            assets = [mat for mat in props.materials if mat['Category'] == category['Slug']]
            return assets
        return assets
    return assets


def append_preview_images(assets):
    """Append preview images to the scene.

    Args:
        assets (list): asset descriptions
    """
    for asset in assets:
        image_path = asset['PreviewImagePath']
        if os.path.exists(image_path) and os.path.isfile(image_path):
            bpy.data.images.load(image_path, check_existing=True)
