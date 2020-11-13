import re
import bpy


def material_is_unique(material, materials):
    """Check whether the passed in material already exists.

    Parameters
    material : bpy.types.Material
        material to check for uniqueness

    Returns
    Boolean
        True if material is unique

    matched_material : bpy.types.Material
        Matching material. None if material is unique

    """
    found = []
    # remove digits from end of material name
    mat_name = material.name.rstrip('0123456789. ')

    # check if material shares a name with another material (minus numeric suffix)
    for mat in materials:
        stripped_name = mat.name.rstrip('0123456789. ')
        if stripped_name == mat_name:
            found.append(mat)

    if len(found) == 0:
        return True, None

    # check if materials that share the same name share the same node tree by comparing names of nodes
    mat_node_keys = material.node_tree.nodes.keys()

    found_2 = []
    for mat in found:
        found_mat_node_keys = mat.node_tree.nodes.keys()
        if mat_node_keys.sort() == found_mat_node_keys.sort():
            found_2.append(mat)

    if len(found_2) == 0:
        return True, None

    # check if all nodes of type 'VALUE' have the same default values on their outputs
    mat_node_values = []
    for node in material.node_tree.nodes:
        if node.type == 'VALUE':
            mat_node_values.append(node.outputs[0].default_value)

    for mat in found_2:
        found_mat_node_values = []
        for node in mat.node_tree.nodes:
            if node.type == 'VALUE':
                found_mat_node_values.append(node.outputs[0].default_value)
        if mat_node_values.sort() == found_mat_node_values.sort():
            return False, mat

    return True, None


def find_vertex_group_of_face(face, mesh, excluded_vert_groups):
    """Return the vertex group face belongs to.

    If the face belongs to more than 1 group return vertex group most verts in face are in (mode)

    Parameters
    face : bpy.types.MeshPolygon
    mesh : bpy.types.Mesh

    Returns
    mode_group : bpy.types.VertexGroup
    """

    # get all vertex groups polygon belongs to
    all_groups = [g.group for v in face.vertices for g in mesh.vertices[v].groups if g.group not in excluded_vert_groups]

    if len(all_groups) is 0:
        return None

    # find the most frequent (mode) of all vertex groups verts in this face is in
    counts = [all_groups.count(index) for index in all_groups]
    mode_index = counts.index(max(counts))
    mode_group = all_groups[mode_index]

    return mode_group


def dedupe(items, key=None):
    """Remove duplicates from sequence while retaining order.

    Args:
        items (sequence): Usually a list
        key (function, optional): Function that converts seq items into hashable types. e.g. key=lambda d: d['Slug'] Defaults to None.

    Yields:
        [set]: deduped set
    """
    seen = set()
    for item in items:
        val = item if key is None else key(item)
        if val not in seen:
            yield item
            seen.add(val)


def get_material_index(obj, material):
    """Return the material index of the passed in material."""
    material_index = list(obj.material_slots.keys()).index(material.name)
    return material_index


def assign_mat_to_vert_group(vert_group, obj, material):
    """Assign material to vertex group."""
    vg_index = obj.vertex_groups[vert_group].index
    vert_group = [v.index for v in obj.data.vertices if vg_index in [vg.group for vg in v.groups]]
    material_index = get_material_index(obj, material)

    for poly in obj.data.polygons:
        count = 0
        for vert in poly.vertices:
            if vert in vert_group:
                count += 1
        if count == len(poly.vertices):
            poly.material_index = material_index


def slugify(slug):
    """Return passed in string as a slug suitable for transmission.

    Normalize string, convert to lowercase, remove non-alpha numeric characters,
    and convert spaces to hyphens.
    """
    slug = slug.lower()
    slug = slug.replace('.', '_')
    slug = slug.replace('"', '')
    slug = slug.replace(' ', '_')
    slug = re.sub(r'[^a-z0-9]+.- ', '-', slug).strip('-')
    slug = re.sub(r'[-]+', '-', slug)
    slug = re.sub(r'/', '_', slug)
    return slug

def find_and_rename(self, asset_name, slug, current_slugs):
    """Recursively search for and rename ID object based on slug.

    Recursively searches for the passed in slug in current slugs and
    appends and increments a number to the slug if found until slug is unique.

    Parameters
    obj : bpy.types.ID
    slug : str
    current_slugs : list of str

    Returns
    slug : str
    """
    if slug not in current_slugs:
        current_slugs.append(slug)
        return slug

    match = re.search(r'\d+$', slug)
    if match:
        slug = rchop(slug, match.group())
        slug = slug + str(int(match.group()) + 1).zfill(3)
        asset_name = rchop(asset_name, match.group())
        asset_name = asset_name + str(int(match.group()) + 1).zfill(3)
        find_and_rename(self, asset_name, slug, current_slugs)
    else:
        slug = slug + '_001'
        asset_name = asset_name + '.001'
        find_and_rename(self, asset_name, slug, current_slugs)
    return slug


def rchop(s, suffix):
    """Return right chopped string.

    Parameters
    s : str
        string to chop
    suffix : str
        suffix to remove from string
    """
    if suffix and s.endswith(suffix):
        return s[:-len(suffix)]
    return s


def tagify(tag_string):
    """Return passed in string as list of tags."""
    tags = []
    if len(tag_string) is not 0:
        tags = tag_string.split(",")
        tags = [tag.strip() for tag in tags]
        tags = [tag.lower() for tag in tags]
    return tags
