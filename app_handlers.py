import json
import os
import shutil
import bpy
from bpy.app.handlers import persistent
from .system import get_addon_path
from .preferences import get_prefs
from .categories import load_categories
from .utils import dedupe


def mt_am_initialise_on_activation(dummy):
    bpy.app.handlers.depsgraph_update_pre.remove(mt_am_initialise_on_activation)
    prefs = get_prefs()
    props = bpy.context.scene.mt_am_props
    create_properties()

    # we store our asset library .json files in the users directory not the add-on directory
    # We do this because otherwise if the use removes the addon they will delete all
    # the metadata that describes the assets
    user_data_path = os.path.join(
        prefs.user_assets_path,
        "data"
    )

    default_data_path = os.path.join(
        prefs.default_assets_path,
        "data"
    )

    # Write the absolute filepath to the default assets included with the asset manager
    # to our asset description file
    asset_types = ['objects', 'collections', 'materials']
    set_asset_desc_filepaths(prefs.default_assets_path, asset_types)

    # check to see if the user assets path already exists
    if not os.path.exists(user_data_path):
        os.makedirs(user_data_path)
        # copy all files from addon assets/data folder to user assets/data folder
        src_files = [fname for fname in os.listdir(default_data_path)
                     if os.path.isfile(os.path.join(default_data_path, fname))]
        for fname in src_files:
            shutil.copy2(os.path.join(default_data_path, fname), user_data_path)
    else:
        # if the user already has asset description files we need to append any new
        # asset descriptions to them
        src_files = [fname for fname in os.listdir(default_data_path)
                     if os.path.isfile(os.path.join(default_data_path, fname))]
        dest_files = [fname for fname in os.listdir(user_data_path)
                      if os.path.isfile(os.path.join(user_data_path, fname))]

        for f in dest_files:
            # skip the categories file
            if f != 'categories.json' and f in src_files:
                # load asset descs from user file
                with open(os.path.join(user_data_path, f)) as json_file:
                    descs = json.load(json_file)
                # append the asset descs from asset manager file
                with open(os.path.join(default_data_path, f)) as json_file:
                    descs.extend(json.load(json_file))
                # deduplicate
                descs = list(dedupe(descs, key=lambda d: d['Slug']))
                # write data file
                with open(os.path.join(user_data_path, f), "w") as write_file:
                    json.dump(descs, write_file, indent=4)

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
    # props.active_category = None
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
        json_path = os.path.join(
            prefs.user_assets_path,
            "data",
            a_type + ".json")

        if os.path.exists(json_path):
            with open(json_path) as json_file:
                descs = (json.load(json_file))

        setattr(props, a_type, descs)


bpy.app.handlers.depsgraph_update_pre.append(mt_am_initialise_on_activation)
bpy.app.handlers.load_post.append(mt_am_initialise_on_load)
