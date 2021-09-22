"""Contains helper functions for adding assets to MakeTile library..."""
import os
from pathlib import Path
import json
import bpy
from ..utils import slugify, tagify, find_and_rename
from ..preferences import get_prefs


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


def construct_asset_description(props, asset_type, asset, **kwargs):
    prefs = get_prefs()
    # check if we're in a sub category that contains assets of the correct type.
    # If not add the object to the root category for its type
    if props.current_path:
        asset_save_path = props.current_path
    else:
        asset_save_path = os.path.join(
            prefs.user_assets_path,
            asset_type.lower())

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
        "PreviewImageName": new_slug + '.png',
        "Type": asset_type.upper()}

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

def draw_object_context_menu_items(self, context):
    """Add save options to object right click context menu."""
    layout = self.layout
    layout.operator_context = 'INVOKE_DEFAULT'
    try:
        if context.active_object.type in ['MESH']:
            layout.separator()
            layout.operator(
                "object.add_selected_objects_to_library",
                text="Save all selected objects to MakeTile Library")
            layout.operator(
                "material.mt_ot_am_add_material_to_library",
                text="Save active material to MakeTile Library"
            )
        if context.active_object.type in ['MESH', 'EMPTY']:
            layout.operator(
                "collection.add_collection_to_library",
                text="Save active object's owning collection to MakeTile Library"
            )
    except AttributeError:
        pass


def register():
    """Register aditional options in object context (right click) menu."""
    bpy.types.VIEW3D_MT_object_context_menu.append(draw_object_context_menu_items)


def unregister():
    """UnRegister."""
    bpy.types.VIEW3D_MT_object_context_menu.remove(draw_object_context_menu_items)
