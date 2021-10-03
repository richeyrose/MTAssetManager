import re
import os
import json
import bpy
from bpy.types import Operator
from bpy.props import StringProperty
from .preferences import get_prefs
from .delete_from_library import delete_assets
from .lib.send2trash import send2trash

# TODO #1 Create a rename category operator
def get_descendent_cats(category):
    """Return all descendents of category as a flat list.

    Args:
        category (dict): category dict

    Returns:
        list[dict{Name,
            Slug,
            Parent,
            Children[list[categories]]}]: flat list of categories
    """
    descendents = []
    for child in category['Children']:
        descendents.append(child)
        descendents.extend(get_descendent_cats(child))
    return descendents


def get_child_cats(categories, category_slug):
    """Return children of category.

    Args:
        categories (list[categories]): categories
        category_slug (string): category

    Returns:
        list[dict{Name,
            Slug,
            Parent,
            Children[list[categories]]}]: list of categories
    """
    if category_slug == '':
        return categories
    children = []
    for cat in categories:
        if cat['Slug'] == category_slug:
            return cat['Children']
        else:
            children = get_child_cats(cat['Children'], category_slug)
        if children:
            return children
    return children


def get_parent_cat_slug(categories, category_slug):
    """Return parent slug of category.

    Args:
        categories (list[categories]): categories
        category_slug (string): category slug

    Returns:
        string: slug
    """
    if category_slug == "":
        return ""
    parent = ""
    for cat in categories:
        if cat['Slug'] == category_slug:
            return cat['Parent']
        else:
            parent = get_parent_cat_slug(cat['Children'], category_slug)
        if parent:
            return parent
    return parent


def get_category(categories, category_slug):
    """Return the category.

    Args:
        categories (list[categories]): categories
        category_slug (string): category slug

    Returns:
        dict{Name,
            Slug,
            Parent,
            Children[list[categories]]}: category
    """
    if category_slug == "":
        return None
    ret_cat = None
    for cat in categories:
        if cat['Slug'] == category_slug:
            return cat
        else:
            ret_cat = get_category(cat['Children'], category_slug)
        if ret_cat:
            return ret_cat
    return ret_cat



def delete_category(categories, category_slug, prefs):
    """Delete the category and all child categories.

    Args:
        categories (list[categories]): categories
        category_slug (string): category slug
        prefs (dict): AssetManager prefs
    """
    for cat in categories:
        if cat['Slug'] == category_slug:
            categories.remove(cat)
            break
        else:
            delete_category(cat['Children'], category_slug, prefs)

    # Update categories.json file
    json_file = os.path.join(
        prefs.user_assets_path,
        "data",
        "categories.json")

    if os.path.exists(json_file):
        with open(json_file, "w") as write_file:
            json.dump(categories, write_file, indent=4)


def load_categories():
    """Load categories from .json file."""
    prefs = get_prefs()
    categories = []
    json_path = os.path.join(
        prefs.user_assets_path,
        "data",
        "categories.json"
    )

    if os.path.exists(json_path):
        with open(json_path) as json_file:
            categories = json.load(json_file)

    return categories


def append_category(categories, parent_slug, new_cat):
    found = False
    for cat in categories:
        if cat['Slug'] == parent_slug:
            cat['Children'].append(new_cat)
            return True
        else:
            found = append_category(cat['Children'], parent_slug, new_cat)
        if found:
            return found
    return found


class MT_OT_Delete_Category(Operator):
    """Delete an existing category and the assets and subcategories it contains."""

    bl_idname = "view3d.mt_delete_category"
    bl_label = "Delete the category and all assets it contains?"
    bl_description = "Warning, this cannot be Undone!"
    bl_options = {'INTERNAL'}

    category_slug: StringProperty(
        name="Category")

    def execute(self, context):
        prefs = get_prefs()
        props = context.scene.mt_am_props
        category = get_category(props.active_category["Children"], self.category_slug)

        try:
            asset_type = category["Contains"].lower()
            asset_descs = getattr(props, asset_type)

            # construct list containing all sub categories
            descendent_cats = get_descendent_cats(category)
            descendent_cats.append(category)
            category_slugs = [cat["Slug"] for cat in descendent_cats]

            # get all assets
            selected_assets = [desc for desc in asset_descs if desc["Category"] in category_slugs]
            delete_assets(selected_assets, prefs, props, asset_type, True)
        except TypeError:
            pass

        # delete categories
        delete_category(props.categories, self.category_slug, prefs)

        # update sidebar
        props['child_cats'] = get_child_cats(
            props.categories,
            props.active_category["Slug"])

        # update asset bar
        props.assets_updated = True


        return {'FINISHED'}

    def invoke(self, context, event):
        """Call when user accesses operator via menu."""
        return context.window_manager.invoke_confirm(self, event)



class MT_OT_Save_Library(Operator):
    bl_idname = "scene.mt_am_save_library"
    bl_label = "Save Library Path"
    bl_description = "Save a Library Path so you can use it again."
    bl_options = {"REGISTER"}

    library_name: StringProperty(
        name="Name",
        default=""
    )

    library_path: StringProperty(
        name="Folder",
        subtype='DIR_PATH',
        default=""
    )

    def execute(self, context):
        prefs = get_prefs()
        props= context.scene.mt_am_props
        libs = prefs.libraries

        new_lib = libs.add()
        new_lib.name = self.library_name
        new_lib.path = props.current_path
        self.library_name = ""
        self.report({'INFO'}, "Library Added")
        return {'FINISHED'}

    def draw(self, context):
        """Draw modal pop up."""
        layout = self.layout
        layout.prop(self, 'library_name')

    def invoke(self, context, event):
        """Call when user accesses operator via menu."""
        return context.window_manager.invoke_props_dialog(self)

class MT_OT_Delete_Subfolder(Operator):
    """Delete a subfolder."""
    bl_idname = "scene.mt_am_delete_subfolder"
    bl_label = "Delete Subfolder"
    bl_description = "Delete a Subfolder"
    bl_options = {"REGISTER"}

    folder_name: StringProperty(
        name="Name",
        default=""
    )

    def execute(self, context):
        """Delete a folder."""
        props = context.scene.mt_am_props
        current_folder = props.current_path
        to_delete = os.path.join(current_folder, self.folder_name)
        if os.path.isdir(to_delete):
            try:
                send2trash(to_delete)
            except OSError as err:
                self.report({'INFO'}, str(err))
        return {'FINISHED'}

class MT_OT_Add_Subfolder(Operator):
    """Add a new subfolder."""
    bl_idname = "scene.mt_am_add_subfolder"
    bl_label = "Add Subfolder"
    bl_description = "Add a new Subfolder"
    bl_options = {"REGISTER"}

    new_folder_name: StringProperty(
        name="Name",
        default=""
    )

    def execute(self, context):
        """Add a new category."""
        props = context.scene.mt_am_props
        current_folder = props.current_path

        try:
            os.mkdir(os.path.join(current_folder, self.new_folder_name))
        except OSError as err:
            self.report({'INFO'}, str(err))
        return {'FINISHED'}

    def invoke(self, context, event):
        """Call when user accesses operator via menu."""
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        """Draw modal pop up."""
        layout = self.layout
        layout.prop(self, 'new_folder_name')
