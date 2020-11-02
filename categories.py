import re
import os
import json
import bpy
from.utils import slugify
from .system import get_addon_path
from .preferences import get_prefs
from bpy.props import StringProperty


def get_child_cats(categories, category_slug):
    """Return children of category.

    Args:
        categories (list[categories]): categories
        category_slug (string): category

    Returns:
        list[categories]: categories
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
        return ""
    ret_cat = ""
    for cat in categories:
        if cat['Slug'] == category_slug:
            return cat
        else:
            ret_cat = get_category(cat['Children'], category_slug)
        if ret_cat:
            return ret_cat
    return ret_cat

def load_categories():
    """Load categories from .json file."""
    prefs = get_prefs()
    categories = []
    json_path = os.path.join(
        prefs.default_assets_path,
        "data",
        "categories.json"
    )

    if os.path.exists(json_path):
        with open(json_path) as json_file:
            categories = json.load(json_file)

    return categories


def add_category(parent_slug, name):
    """Add a new category.

    Args:
        parent_slug (str): parent slug
        name (str): name
    """
    prefs = get_prefs()
    props = bpy.context.scene.mt_am_props
    categories = props.categories
    parent_cat = get_category(categories, parent_slug)
    bpy.ops.rigidbody.world_add()

    new_cat = {
        "Name": name.strip(),
        "Slug": parent_slug + "\\" + slugify(name),
        "Parent": parent_slug,
        "Contains": parent_cat["Contains"],
        "Children": []}

    append_category(categories, parent_slug, new_cat)

    # update sidebar
    props['child_cats'] = get_child_cats(
        categories,
        parent_slug)

    # Write categories.json file
    json_file = os.path.join(
        prefs.default_assets_path,
        "data",
        "categories.json")

    if os.path.exists(json_file):
        with open(json_file, "w") as write_file:
            json.dump(categories, write_file, indent=4)


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


class MT_OT_Add_Category(bpy.types.Operator):
    bl_idname = "scene.mt_am_add_category"
    bl_label = "Add Category"
    bl_description = "Add a new Category"
    bl_options = {"REGISTER"}

    new_cat_name: StringProperty(
        name="Name",
        default=""
    )

    def execute(self, context):
        """Add a new category."""
        props = context.scene.mt_am_props
        add_category(props.active_category, self.new_cat_name)
        return {'FINISHED'}

    def invoke(self, context, event):
        """Call when user accesses operator via menu."""
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        """Draw modal pop up."""
        layout = self.layout
        layout.prop(self, 'new_cat_name')

