import bpy


def get_child_cats(categories, category):
    """Return children of category.

    Args:
        categories (list[categories]): categories
        category (string): category

    Returns:
        list[categories]: categories
    """
    if category == '':
        return categories
    children = []
    for cat in categories:
        if cat['Slug'] == category:
            return cat['Children']
        else:
            children = get_child_cats(cat['Children'], category)
        if children:
            return children
    return children


def get_parent_cat_name(categories, category):
    """Return parent of category.

    Args:
        categories (list[categories]): categories
        category (string): category

    Returns:
        string: category
    """
    if category == "":
        return ""
    parent = ""
    for cat in categories:
        if cat['Slug'] == category:
            return cat['Parent']
        else:
            parent = get_parent_cat_name(cat['Children'], category)
        if parent:
            return parent
    return parent


def get_category(categories, category):
    """Return the category.

    Args:
        categories (list[categories]): categories
        category (string): category name

    Returns:
        dict{Name,
            Slug,
            Parent,
            Children[list[categories]]}: category
    """
    props = context.scene.mt_am_props

    if category == "":
        return props['categories']
    ret_cat = ""
    for cat in categories:
        if cat['Slug'] == category:
            return cat
        else:
            ret_cat = get_category(cat['Children'], category)
        if ret_cat:
            return ret_cat
    return props['categories']
