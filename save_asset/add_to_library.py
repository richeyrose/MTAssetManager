"""Contains helper functions for adding assets to MakeTile library..."""
import os
from pathlib import Path
import bpy
from bpy.props import StringProperty, EnumProperty
from ..utils import slugify, tagify, find_and_rename
from ..preferences import get_prefs

class MT_Save_To_Library:
    """Mixin for save operators."""
    Name: StringProperty(
        name="Name",
        default=""
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

    License: EnumProperty(
        items=[
            ("ARR", "All Rights Reserved", ""),
            ("CCBY", "Attribution (CC BY)", ""),
            ("CCBYSA", "Attribution-ShareAlike (CC BY-SA)", ""),
            ("CCBYND", "Attribution-NoDerivs (CC BY-ND)", ""),
            ("CCBYNC", "Attribution-NonCommercial (CC BY-NC)", ""),
            ("CCBYNCSA", "Attribution-NonCommercial-ShareAlike (CC BY-NC-SA)", ""),
            ("CCBYNCND", "Attribution-NonCommercial-NoDerivs (CC BY-NC-ND)", "")],
        name="License",
        description="License for asset use",
        default="ARR")

    Tags: StringProperty(
        name="Tags",
        description="Comma seperated list",
        default=""
    )

def create_preview_obj_enums(self, context):
    """Create a blender enum list of objects that can be used for rendering material previews.

    Scans the addon/assets/previews/objects path and creates an enum based on the names
    of the .blend files it finds there.

    Args:
        context (bpy.Context): Blender context

    Returns:
        list[bpy.types.EnumPropertyItem]: Enum Items
    """
    enum_items = []

    if context is None:
        return enum_items

    prefs = get_prefs()

    obj_path = os.path.join(
        prefs.default_assets_path,
        "previews",
        "objects")

    filenames = [name for name in os.listdir(obj_path)
                 if os.path.isfile(os.path.join(obj_path, name))]

    for name in filenames:
        stripped_name = os.path.splitext(name)[0]
        enum = (stripped_name, stripped_name, "")
        enum_items.append(enum)

    return sorted(enum_items)


def check_category_type(category, asset_type):
    """Return category["Slug"] if category contains assets of the correct asset type.

    If not we return root category for that asset type

    Args:
        category (dict): MakeTile category
        asset_type (ENUM in 'OBJECTS', 'MATERIALS', 'COLLECTIONS'): type of asset to save

    Returns:
        str: category_slug
    """
    # TODO: Create a popup to choose category
    # TODO: Ensure asset bar switches to active category
    if category["Contains"] == asset_type:
        category_slug = category["Slug"]
    else:
        category_slug = asset_type.lower()
    return category_slug


def draw_save_props_menu(self, context):
    """Draw a pop up menu for entering properties.

    Args:
        context (bpy.Context): context
    """
    layout = self.layout
    layout.prop(self, 'Description')
    layout.prop(self, 'URI')
    layout.prop(self, 'Author')
    layout.prop(self, 'License')
    layout.prop(self, 'Tags')


def add_asset_to_library(self, asset, asset_desc, preview_img = None):
    """Add the passed in asset to the asset library.

    Args:
        context (bpy.Context): context
        asset (bpy.types.object, material, collection): the asset to add
        asset_type (enum in {OBJECTS, COLLECTIONS, MATERIALS}): asset type

    Returns:
        dict: asset_desc
    """
    imagepath = os.path.join(asset_desc['FilePath'], asset_desc['PreviewImageName'])
    assetpath = os.path.join(asset_desc['FilePath'], asset_desc['FileName'])

    if preview_img:
        # save asset preview image to asset
        asset.mt_preview_img = preview_img
        preview_img.pack()


    # save asset in individual file
    if not os.path.exists(asset_desc['FilePath']):
        os.makedirs(asset_desc['FilePath'])

    bpy.data.libraries.write(
        assetpath,
        {asset, preview_img},
        fake_user=True)

    # # delete external image
    if os.path.exists(imagepath):
        os.remove(imagepath)

    self.report({'INFO'}, asset.name + " added to Library.")

    return asset_desc


def construct_asset_description(props, asset, **kwargs):
    asset_save_path = props.current_path

    # create a unique (within this directory) slug for our file
    slug = slugify(asset.name)

    # list of .blend file stem names in asset_save_path:
    blends = [f for f in os.listdir(asset_save_path) if os.path.isfile(os.path.join(asset_save_path, f)) and f.endswith(".blend")]
    stems = [Path(blend).stem for blend in blends]

    # check if slug already exists and increment and rename if not.
    new_slug = find_and_rename(slug, stems)

    # construct dict for saving to .json cache file
    asset_desc = {
        "Slug": new_slug,
        "FileName": new_slug + '.blend',
        "FilePath": asset_save_path,
        "PreviewImageName": new_slug + '.png'}

    for key, value in kwargs.items():
        asset_desc[key] = value

    return asset_desc


def mark_as_asset(asset, asset_desc, tags):
    """Save asset as blender asset for blender's internal asset browser.

    Args:
        asset (ID data block): Asset
        asset_desc (dict): asset description
        tags (list[str]): list of tags
    """

    # Clear any existing asset data and then mark as asset
    asset.asset_clear()
    asset.asset_mark()
    asset_data = asset.asset_data

    # set asset preview
    ctx = {'id': asset}
    imagepath = os.path.join(asset_desc['FilePath'], asset_desc['PreviewImageName'])
    if os.path.isfile(imagepath):
        bpy.ops.ed.lib_id_load_custom_preview(ctx, filepath=imagepath)

    # set asset description
    asset_data.description = asset_desc['Description']

    # set asset tags
    for tag in tags:
        asset_data.tags.new(tag, skip_if_exists=True)

    # set custom Maketile asset props
    asset_data.mt_author = asset_desc['Author']
    asset_data.mt_license = asset_desc['License']
    asset_data.mt_URI = asset_desc['URI']
