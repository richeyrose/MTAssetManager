import os
import shutil
import bpy
from .system import get_addon_path
from bpy.app.handlers import persistent
from .preferences import get_prefs

def copy_default_asset_library():
    """Copy the default assets to the user asset library."""
    prefs = get_prefs()
    addon_path = get_addon_path()
    user_assets_path = prefs.user_assets_path
    default_assets_path = os.path.join(addon_path, "assets")
    asset_types = ['objects', 'collections', 'materials']

    for t in asset_types:
        src = os.path.join(default_assets_path, t)
        dst = os.path.join(user_assets_path, t)
        shutil.copytree(src, dst, dirs_exist_ok=True)

def create_libraries():
    """Add the user asset path as asset library."""
    prefs = get_prefs()
    context = bpy.context
    libs = context.preferences.filepaths.asset_libraries
    user_assets_path = prefs.user_assets_path

    # add user library to libraries list.
    if not os.path.isdir(user_assets_path):
        os.makedirs(user_assets_path)

    exists = False
    for lib in libs:
        if os.path.samefile(user_assets_path, lib.path):
            exists = True

    if not exists:
        bpy.ops.preferences.asset_library_add()
        libs[-1].name = "MakeTile"
        libs[-1].path = user_assets_path

def mt_am_initialise_on_activation(dummy):
    """Call the first time the depsgraph is updated after add-on activation."""
    bpy.app.handlers.depsgraph_update_pre.remove(mt_am_initialise_on_activation)
    create_libraries()
    copy_default_asset_library()
    create_properties()
    bpy.context.view_layer.update()

@persistent
def mt_am_initialise_on_load(dummy):
    """Call when new file is loaded."""
    create_properties()

def create_properties():
    """Create custom properties."""
    prefs = get_prefs()
    props = bpy.context.scene.mt_am_props
    props.library_path = prefs.library_path
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
