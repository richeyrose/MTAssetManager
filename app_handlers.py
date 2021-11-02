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
        if os.path.exists(src):
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

    def load_icon(filepath):
        if os.path.exists(filepath):
            return bpy.data.images.load(filepath, check_existing=True)

    icons_path = os.path.join(prefs.default_assets_path, "misc", "icons.blend")
    with bpy.data.libraries.load(icons_path, link=True) as (data_from, data_to):
        data_to.images = [img for img in data_from.images if img not in bpy.data.images]

    bar_props.object_icon = bpy.data.images['object_data.png']
    bar_props.collection_icon = bpy.data.images['outliner_collection.png']
    bar_props.material_icon = bpy.data.images['material.png']
    bar_props.missing_preview_icon = bpy.data.images['no_image.png']

bpy.app.handlers.depsgraph_update_pre.append(mt_am_initialise_on_activation)
bpy.app.handlers.load_post.append(mt_am_initialise_on_load)
