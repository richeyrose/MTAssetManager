import bpy
from bpy.types import Operator

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
    layout.operator("object.delete_selected_assets_from_library")


class MT_OT_link_to_active_collection(Operator):
    """Link object to active collection."""
    bl_idname = "outliner.mt_link_to_active_collection"
    bl_label = "Link to active collection"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Link data block to active collection."

    def execute(self, context):
        active_collection = context.collection
        ids = context.selected_ids
        for id in ids:
            try:
                active_collection.objects.link(id)
            except RuntimeError as err:
                self.report({'INFO'}, err)

        return {'FINISHED'}

def draw_outliner_context_menu_items(self, context):
    """Outliner context menu when an object is selected."""
    layout = self.layout
    layout.operator_context = 'INVOKE_DEFAULT'
    layout.operator("outliner.mt_link_to_active_collection")

def register():
    """Register aditional options in object context (right click) menu."""
    bpy.types.VIEW3D_MT_object_context_menu.append(draw_object_context_menu_items)
    bpy.types.OUTLINER_MT_object.append(draw_outliner_context_menu_items)

def unregister():
    """UnRegister."""
    bpy.types.OUTLINER_MT_object.remove(draw_outliner_context_menu_items)
    bpy.types.VIEW3D_MT_object_context_menu.remove(draw_object_context_menu_items)
