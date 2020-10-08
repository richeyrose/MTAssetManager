import json
import os
import bpy
from bpy.app.handlers import persistent
from .system import get_addon_path


def create_properties_on_activation(dummy):
    bpy.app.handlers.depsgraph_update_pre.remove(create_properties_on_activation)
    load_categories()
    load_asset_descriptions()

@persistent
def create_properties_on_load(dummy):
    load_categories()
    load_asset_descriptions()

def load_categories():
    """Load categories from .json file."""
    props = bpy.context.scene.mt_am_props
    props.active_category = ""

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
    props['current_assets'] = []


def load_asset_descriptions():
    """Load asset descriptions from .json file."""
    load_object_descriptions()
    load_collection_descriptions()
    load_material_descriptions()


def load_collection_descriptions():
    """Load Collection descriptions from .json file."""
    props = bpy.context.scene.mt_am_props
    props['collections'] = []


def load_material_descriptions():
    """Load Material descriptions from .json file."""
    props = bpy.context.scene.mt_am_props
    props['materials'] = []

def load_object_descriptions():
    """Load Object descriptions from .json file."""
    addon_path = get_addon_path()
    props = bpy.context.scene.mt_am_props

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


bpy.app.handlers.depsgraph_update_pre.append(create_properties_on_activation)
bpy.app.handlers.load_post.append(create_properties_on_load)
