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
    load_asset_descriptions(props, asset_types)

@persistent
def mt_am_initialise_on_load(dummy):
    props = bpy.context.scene.mt_am_props
    create_properties()
    asset_types = ['objects', 'collections', 'materials']
    load_asset_descriptions(props, asset_types)

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


def load_asset_descriptions(props, asset_types):
    """Load asset descriptions from .json file.

    Args:
        props (mt_am_props): asset manager props
        asset_types (list[str]): list of asset types
    """

    prefs = get_prefs()
    descs = []
    for a_type in asset_types:
        # load default assets bundled with asset manager
        json_path = os.path.join(
            prefs.default_assets_path,
            "data",
            a_type + ".json")

        if os.path.exists(json_path):
            with open(json_path) as json_file:
                descs = json.load(json_file)

        # load user objects
        json_path = os.path.join(
            prefs.user_assets_path,
            "data",
            a_type + ".json")

        if os.path.exists(json_path):
            with open(json_path) as json_file:
                descs.extend(json.load(json_file))
            #deduplicate list
            descs = list(dedupe(descs, key=lambda d: d['Slug']))

        setattr(props, a_type, descs)


bpy.app.handlers.depsgraph_update_pre.append(mt_am_initialise_on_activation)
bpy.app.handlers.load_post.append(mt_am_initialise_on_load)
