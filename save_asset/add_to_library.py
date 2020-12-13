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


def add_asset_to_library(self, context, props, asset, assets_path, asset_type, category, tags="", **kwargs):
    """Add the passed in asset to the asset library.

    Args:
        context (bpy.Context): context
        props (scene.mt_am_props): asset manager properties
        asset (bpy.types.object, material, collection): the asset to add
        assets_path (path): the path to the root assets foldere
        asset_type (enum in {OBJECTS, COLLECTIONS, MATERIALS}): asset type
        category (dict): MakeTile category
        tags (str, optional): Comma seperated list of tags. Used for searching. Defaults to "".
        **kwargs: additional fields. Usually Description, Author, URI, License

    Returns:
        dict: asset_desc
    """
    assets = getattr(props, asset_type.lower())

    asset_save_path = os.path.join(
        assets_path,
        asset_type.lower()
    )

    json_path = os.path.join(
        assets_path,
        "data"
    )

    slug = slugify(asset.name)
    current_slugs = [asset['Slug'] for asset in assets]

    # check if slug already exists and increment and rename if not.
    new_slug = find_and_rename(slug, current_slugs)

    pretty_name = asset.name  # when we reimport an asset we will rename it to this

    asset.name = new_slug

    filepath = os.path.join(
        asset_save_path,
        new_slug + '.blend')

    imagepath = os.path.join(
        asset_save_path,
        new_slug + '.png')

    # construct dict for saving to users objects.json
    asset_desc = {
        "Name": pretty_name,
        "Slug": new_slug,
        "Category": category,
        "FileName": new_slug + '.blend',
        "FilePath": filepath,
        "PreviewImagePath": imagepath,
        "PreviewImageName": new_slug + '.png',
        "Type": asset_type.upper(),
        "Tags": tagify(tags)}

    for key, value in kwargs.items():
        asset_desc[key] = value
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

    bpy.data.libraries.write(
        os.path.join(filepath),
        {asset},
        fake_user=True)

    # change asset name back to pretty_name
    asset.name = pretty_name

    self.report({'INFO'}, pretty_name + " added to Library.")

    return asset_desc


def draw_object_context_menu_items(self, context):
    """Add save options to object right click context menu."""
    layout = self.layout
    if context.active_object.type in ['MESH']:
        layout.separator()
        layout.operator_context = 'INVOKE_DEFAULT'
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
