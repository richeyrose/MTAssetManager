"""Contains helper fiunctions for adding assets to MakeTile library..."""

import os
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


def add_asset_to_library(self, context, asset, asset_type, asset_desc):
    """Add the passed in asset to the asset library.

    Args:
        context (bpy.Context): context
        asset (bpy.types.object, material, collection): the asset to add
        asset_type (enum in {OBJECTS, COLLECTIONS, MATERIALS}): asset type

    Returns:
        dict: asset_desc
    """
    props = context.scene.mt_am_props
    prefs = get_prefs()
    assets_path = prefs.user_assets_path

    # in memory list of assets of asset_type
    assets = getattr(props, asset_type.lower())

    asset_save_path = os.path.join(
        assets_path,
        asset_type.lower()
    )

    json_path = os.path.join(
        assets_path,
        "data"
    )

    # update current objects list
    assets = assets.append(asset_desc)

    if not os.path.exists(json_path):
        os.makedirs(json_path)

    # open user asset description file and then write description to file
    file_assets = []
    json_file = os.path.join(json_path, asset_type.lower() + '.json')

    if os.path.exists(json_file):
        with open(json_file) as read_file:
            file_assets = json.load(read_file)

    file_assets.append(asset_desc)

    # write description to .json file
    with open(json_file, "w") as write_file:
        json.dump(file_assets, write_file, indent=4)

    # save asset to library file
    if not os.path.exists(asset_save_path):
        os.makedirs(asset_save_path)

    # change asset name to asset slug
    asset.name = asset_desc['Slug']

    # save asset in individual file
    bpy.data.libraries.write(
        os.path.join(asset_desc['FilePath']),
        {asset},
        fake_user=True)

    # change asset name back to pretty name
    asset.name = asset_desc['Name']

    self.report({'INFO'}, asset_desc['Name'] + " added to Library.")

    return asset_desc


def construct_asset_description(props, asset_type, assets_path, asset, **kwargs):
    # check if we're in a sub category that contains assets of the correct type.
    # If not add the object to the root category for its type
    if props.active_category is None:
        category = asset_type.lower()
    else:
        category = check_category_type(props.active_category, asset_type)

    # in memory list of assets of asset_type
    assets = getattr(props, asset_type.lower())

    asset_save_path = os.path.join(
        assets_path,
        asset_type.lower()
    )

    slug = slugify(asset.name)
    current_slugs = [asset['Slug'] for asset in assets]

    # check if slug already exists and increment and rename if not.
    new_slug = find_and_rename(slug, current_slugs)

    pretty_name = asset.name  # when we reimport an asset we will rename it to this

    filepath = os.path.join(
        asset_save_path,
        new_slug + '.blend')

    imagepath = os.path.join(
        asset_save_path,
        new_slug + '.png')

    # construct dict for saving to .json cache file
    asset_desc = {
        "Name": pretty_name,
        "Slug": new_slug,
        "Category": category,
        "FileName": new_slug + '.blend',
        "FilePath": filepath,
        "PreviewImagePath": imagepath,
        "PreviewImageName": new_slug + '.png',
        "Type": asset_type.upper()}

    for key, value in kwargs.items():
        asset_desc[key] = value

    return asset_desc


def save_as_blender_asset(asset, asset_desc, tags):
    """Save asset as blender asset for blender's internal asset browser.

    Args:
        asset (ID data block): Asset
        asset_desc (dict): asset description
        tags (list[str]): list of tags
    """
    ctx = {'id': asset}

    if not hasattr(asset.asset_data, 'id_data'):
        bpy.ops.asset.mark(ctx)
    else:
        bpy.ops.asset.clear(ctx)
        bpy.ops.asset.mark(ctx)

    if os.path.isfile(asset_desc['PreviewImagePath']):
        bpy.ops.ed.lib_id_load_custom_preview(ctx, filepath=asset_desc['PreviewImagePath'])

    asset.asset_data.description = asset_desc['Description']

    for tag in tags:
        asset.asset_data.tags.new(tag, skip_if_exists=True)


def draw_object_context_menu_items(self, context):
    """Add save options to object right click context menu."""
    layout = self.layout
    layout.operator_context = 'INVOKE_DEFAULT'
    if context.active_object.type in ['MESH']:
        layout.separator()
        layout.operator(
            "object.add_active_object_to_library",
            text="Save active object to MakeTile Library")
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


def register():
    """Register aditional options in object context (right click) menu."""
    bpy.types.VIEW3D_MT_object_context_menu.append(draw_object_context_menu_items)


def unregister():
    """UnRegister."""
    bpy.types.VIEW3D_MT_object_context_menu.remove(draw_object_context_menu_items)
