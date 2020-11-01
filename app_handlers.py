import json
import os
import bpy
from bpy.app.handlers import persistent
from .system import get_addon_path
from .preferences import get_prefs
from .categories import load_categories
from .utils import dedupe


def mt_am_initialise_on_activation(dummy):
    prefs = get_prefs()
    bpy.app.handlers.depsgraph_update_pre.remove(mt_am_initialise_on_activation)
    props = bpy.context.scene.mt_am_props
    create_properties()
    asset_types = ['objects', 'collections', 'materials']
    set_asset_desc_filepaths(prefs.default_assets_path, asset_types)
    load_asset_descriptions(props)

@persistent
def mt_am_initialise_on_load(dummy):
    props = bpy.context.scene.mt_am_props
    create_properties()
    load_asset_descriptions(props)

def set_asset_desc_filepaths(assets_path, asset_types):
    """Stores the path to the associated asset type in asset description .json file

    Args:
        assets_path (str): path to assets folder
        asset_types (str): type of asset
    """
    for asset_type in asset_types:
        json_file = os.path.join(
            assets_path,
            "data",
            asset_type + ".json")

        if os.path.exists(json_file):
            with open(json_file) as read_file:
                assets = json.load(read_file)

            for asset in assets:
                asset["FilePath"] = os.path.join(
                    assets_path,
                    asset_type,
                    asset["FileName"])
                asset["PreviewImagePath"] = os.path.join(
                    assets_path,
                    asset_type,
                    asset["PreviewImageName"])

            with open(json_file, "w") as write_file:
                json.dump(assets, write_file, indent=4)


def create_properties():
    """Create custom properties."""
    prefs = get_prefs()
    props = bpy.context.scene.mt_am_props
    props.active_category = ""
    props.parent_category = ""

    bar_props = bpy.context.scene.mt_bar_props
    bar_props['hovered_asset'] = None
    bar_props['selected_asset'] = None
    bar_props['dragged_asset'] = None
    bar_props['missing_preview_image'] = load_missing_preview_image()

    categories = load_categories()
    props.categories = categories  # all categories
    props.child_cats = categories  # child categories of active category


def load_missing_preview_image():
    prefs = get_prefs()
    no_image_path = os.path.join(
        prefs.default_assets_path,
        "misc",
        "no_image.png"
    )

    if os.path.exists(no_image_path):
        return bpy.data.images.load(no_image_path, check_existing=True)
    return None


def load_asset_descriptions(props):
    """Load asset descriptions from .json file."""
    props.objects = load_object_descriptions()
    props.collections = load_collection_descriptions()
    props.materials = load_material_descriptions()


def load_collection_descriptions():
    """Load Collection descriptions from .json file.

    Returns:
        [list]: List of Collection asset descriptions
    """
    prefs = get_prefs()
    default_collections = []

    # load default collections bundled with asset manager
    json_path = os.path.join(
        prefs.default_assets_path,
        "data",
        "collections.json")

    if os.path.exists(json_path):
        with open(json_path) as json_file:
            default_collections = json.load(json_file)

    # TODO load user collections
    return default_collections


def load_material_descriptions():
    """Load Material descriptions from .json file.

    Returns:
        [list]: list of Material asset descriptions
    """
    prefs = get_prefs()
    default_materials = []

    # load materials bundled with asset manager
    json_path = os.path.join(
        prefs.default_assets_path,
        "data",
        "materials.json")

    if os.path.exists(json_path):
        with open(json_path) as json_file:
            default_materials = json.load(json_file)

    # TODO load default maketile materials if MT is installed
    # TODO load user materials
    return default_materials


def load_object_descriptions():
    """Load Object descriptions from .json file.

    Returns:
        [list]: list of Object asset descriptions
    """
    prefs = get_prefs()
    ob_descs = []

    # load default objects bundled with asset manager
    json_path = os.path.join(
        prefs.default_assets_path,
        "data",
        "objects.json")

    if os.path.exists(json_path):
        with open(json_path) as json_file:
            ob_descs = json.load(json_file)

    # load user objects
    json_path = os.path.join(
        prefs.user_assets_path,
        "data",
        "objects.json")

    if os.path.exists(json_path):
        with open(json_path) as json_file:
            ob_descs.extend(json.load(json_file))

    return list(dedupe(ob_descs, key=lambda d: d['Slug']))



bpy.app.handlers.depsgraph_update_pre.append(mt_am_initialise_on_activation)
bpy.app.handlers.load_post.append(mt_am_initialise_on_load)
