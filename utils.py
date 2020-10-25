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
