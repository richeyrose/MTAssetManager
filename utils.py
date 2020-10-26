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


def find_vertex_group_of_face(face, obj):
    """Return the vertex group face belongs to.

    If the face belongs to more than 1 group return vertex group most verts in face are in (mode)

    Parameters
    face : bpy.types.MeshPolygon
    obj : bpy.types.Object

    Returns
    mode_group : bpy.types.VertexGroup
    """
    # get all vertex groups polygon belongs to
    all_groups = [g.group for v in face.vertices for g in obj.data.vertices[v].groups]

    if len(all_groups) is 0:
        return None

    # find the most frequent (mode) of all vertex groups verts in this face is in
    counts = [all_groups.count(index) for index in all_groups]
    mode_index = counts.index(max(counts))
    mode_group = all_groups[mode_index]

    return mode_group

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

