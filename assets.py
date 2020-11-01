import os
import bpy
from bpy.props import StringProperty, EnumProperty
from .categories import get_category
from .app_handlers import load_collection_descriptions, load_material_descriptions, load_object_descriptions


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
            try:
                obj_descs = props['objects']
            except KeyError:
                obj_descs = bpy.context.scene.mt_am_props['objects'] = load_object_descriptions()
            assets = [obj for obj in obj_descs if obj['Category'] == category['Slug']]
            return assets
        if category['Contains'] == 'COLLECTIONS':
            try:
                coll_descs = props['collections']
            except KeyError:
                coll_descs = bpy.context.scene.mt_am_props['collections'] = load_collection_descriptions()
            assets = [coll for coll in coll_descs if coll['Category'] == category['Slug']]
            return assets
        if category['Contains'] == 'MATERIALS':
            try:
                mat_descs = props['materials']
            except KeyError:
                mat_descs = bpy.context.scene.mt_am_props['materials'] = load_material_descriptions()
            assets = [mat for mat in mat_descs if mat['Category'] == category['Slug']]
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
