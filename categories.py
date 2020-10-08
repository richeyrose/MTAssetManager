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


def get_parent_cat(categories, category):
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
            parent = get_parent_cat(cat['Children'], category)
        if parent:
            return parent
