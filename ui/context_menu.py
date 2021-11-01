import bpy

def draw_object_context_menu_items(self, context):
    """Add save options to object right click context menu."""
    layout = self.layout
    layout.operator_context = 'INVOKE_DEFAULT'
    layout.separator()
    # save assets
    layout.operator(
        "object.add_selected_objects_to_library",
        text="Save selected objects to MakeTile Library")
    layout.operator(
        "material.mt_ot_am_add_material_to_library",
        text="Save active material to MakeTile Library")
    op = layout.operator("collection.add_collection_to_library")
    op.name = context.collection.name

    layout.separator()
    # cut, copy, paste, delete assets
    layout.operator("object.delete_selected_assets_from_library")

def register():
    """Register aditional options in object context (right click) menu."""
    bpy.types.VIEW3D_MT_object_context_menu.append(draw_object_context_menu_items)


def unregister():
    """UnRegister."""
    bpy.types.VIEW3D_MT_object_context_menu.remove(draw_object_context_menu_items)

