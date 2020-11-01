import json
import os
import bpy
from bpy.app.handlers import persistent
from .system import get_addon_path
from .preferences import get_prefs
from .categories import load_categories

def mt_am_initialise_on_activation(dummy):
    bpy.app.handlers.depsgraph_update_pre.remove(mt_am_initialise_on_activation)
    create_propertes()

@persistent
def mt_am_initialise_on_load(dummy):
    create_propertes()

def create_propertes():
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

    load_asset_descriptions(props)

def load_missing_preview_image():
    prefs = get_prefs()
    no_image_path = os.path.join(
        prefs.assets_path,
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

    addon_path = get_addon_path()
    props = bpy.context.scene.mt_am_props
    default_collections = []

    # load default collections bundled with asset manager
    json_path = os.path.join(
        addon_path,
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
    addon_path = get_addon_path()
    props = bpy.context.scene.mt_am_props
    default_materials = []

    # load default materials bundled with asset manager
    json_path = os.path.join(
        addon_path,
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
    addon_path = get_addon_path()
    props = bpy.context.scene.mt_am_props
    default_objects = []

    # load default objects bundled with asset manager
    json_path = os.path.join(
        addon_path,
        "data",
        "objects.json")

    if os.path.exists(json_path):
        with open(json_path) as json_file:
            default_objects = json.load(json_file)

    # TODO load user objects
    return default_objects

bpy.app.handlers.depsgraph_update_pre.append(mt_am_initialise_on_activation)
bpy.app.handlers.load_post.append(mt_am_initialise_on_load)
