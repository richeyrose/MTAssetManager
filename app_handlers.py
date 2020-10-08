import json
import os
import bpy
from bpy.app.handlers import persistent
from .system import get_addon_path


def create_properties_on_activation(dummy):
    bpy.app.handlers.depsgraph_update_pre.remove(create_properties_on_activation)
    load_categories()


@persistent
def create_properties_on_load(dummy):
    load_categories()


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

    with open(json_path) as json_file:
        categories = json.load(json_file)

    props['categories'] = categories  # all categories
    props['child_cats'] = categories  # current child categories of active category

bpy.app.handlers.depsgraph_update_pre.append(create_properties_on_activation)
bpy.app.handlers.load_post.append(create_properties_on_load)
