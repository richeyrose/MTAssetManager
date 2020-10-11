import json
import os
import bpy
from bpy.app.handlers import persistent
from .system import get_addon_path
from .preferences import get_prefs

def initialise_on_activation(dummy):
    bpy.app.handlers.depsgraph_update_pre.remove(initialise_on_activation)
    create_propertes()
    load_categories()
    load_asset_descriptions()

@persistent
def initialise_on_load(dummy):
    create_propertes()
    load_categories()
    load_asset_descriptions()


def create_propertes():
    """Create custom properties."""
    prefs = get_prefs()
    props = bpy.context.scene.mt_am_props
    props.active_category = ""
    props.parent_category = ""

    props['categories'] = []  # all categories
    props['child_cats'] = []  # children of active category
    props['current_assets'] = []  # assets in current category
    props['objects'] = []  # assets of type OBJECT
    props['collections'] = []  # assets of type COLLECTION
    props['materials'] = []  # assets of type MATERIAL

    bar_props = bpy.context.scene.mt_bar_props
    bar_props['hovered_asset'] = None
    bar_props['selected_asset'] = None
    bar_props['dragged_asset'] = None

    no_image_path = os.path.join(
        prefs.assets_path,
        "misc",
        "no_image.png"
    )

    bar_props['missing_preview_image'] = bpy.data.images.load(no_image_path, check_existing=True)

def load_categories():
    """Load categories from .json file."""
    props = bpy.context.scene.mt_am_props

    addon_path = get_addon_path()
    json_path = os.path.join(
        addon_path,
        "data",
        "categories.json"
    )

    if os.path.exists(json_path):
        with open(json_path) as json_file:
            categories = json.load(json_file)

    props['categories'] = categories  # all categories
    props['child_cats'] = categories  # current child categories of active category


def load_asset_descriptions():
    """Load asset descriptions from .json file."""
    load_object_descriptions()
    load_collection_descriptions()
    load_material_descriptions()


def load_collection_descriptions():
    """Load Collection descriptions from .json file."""
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
    props['collections'] = default_collections


def load_material_descriptions():
    """Load Material descriptions from .json file."""
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

    # TODO load user materials
    props['materials'] = default_materials


def load_object_descriptions():
    """Load Object descriptions from .json file."""
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
    props['objects'] = default_objects


bpy.app.handlers.depsgraph_update_pre.append(initialise_on_activation)
bpy.app.handlers.load_post.append(initialise_on_load)
