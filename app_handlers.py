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
    """Call the first time the depsgraph is updated after add-on activation.

    Sets up asset cache .json files
    """
    bpy.app.handlers.depsgraph_update_pre.remove(mt_am_initialise_on_activation)
    create_properties()

@persistent
def mt_am_initialise_on_load(dummy):
    create_properties()

def create_properties():
    """Create custom properties."""
    prefs = get_prefs()
    props = bpy.context.scene.mt_am_props
    props.current_path = prefs.current_library_path

    bar_props = bpy.context.scene.mt_bar_props
    bar_props['hovered_asset'] = None
    bar_props['selected_asset'] = None
    bar_props['dragged_asset'] = None
    bar_props['missing_preview_image'] = load_missing_preview_image()


def load_missing_preview_image():
    """Load the image used for assets with no preview.

    Returns:
        bpy.types.Image: Image
    """
    prefs = get_prefs()
    no_image_path = os.path.join(
        prefs.default_assets_path,
        "misc",
        "no_image.png"
    )

    if os.path.exists(no_image_path):
        return bpy.data.images.load(no_image_path, check_existing=True)
    return None

bpy.app.handlers.depsgraph_update_pre.append(mt_am_initialise_on_activation)
bpy.app.handlers.load_post.append(mt_am_initialise_on_load)
