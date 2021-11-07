import os
import bpy
from bpy.types import Operator
from bpy.props import StringProperty
from .preferences import get_prefs
from .lib.send2trash import send2trash
from .utils import path_leaf


class MT_OT_Save_Library(Operator):
    bl_idname = "scene.mt_am_save_library"
    bl_label = "Save Library Path"
    bl_description = "Save a Library Path so you can use it again."
    bl_options = {"REGISTER"}

    library_name: StringProperty(
        name="Name",
        default="Library"
    )

    library_path: StringProperty(
        name="Folder",
        subtype='DIR_PATH',
        default=""
    )

    @classmethod
    def poll(cls, context):
        return os.path.isdir(context.scene.mt_am_props.new_library_path)

    def execute(self, context):
        prefs = get_prefs()
        props= context.scene.mt_am_props
        libs = context.preferences.filepaths.asset_libraries

        # check if library already exists
        for lib in libs:
            try:
                if os.path.samefile(props.current_path, lib.path):
                    self.report({'INFO'}, "Library Already Exists")
                    return {'CANCELLED'}
            # skip libraries with no paths
            except OSError as err:
                self.report({'INFO'}, str(err))
                return {'CANCELLED'}

        # save library
        if not self.library_name:
            self.library_name = path_leaf(props.current_path)

        # doesn't seem to be a way of doing this without using an operator
        bpy.ops.preferences.asset_library_add()
        libs[-1].name = self.library_name
        libs[-1].path = props.current_path
        self.report({'INFO'}, "Library" + libs[-1].name + "Added")
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
                props.assets_updated = True
                return {'FINISHED'}
            except OSError as err:
                self.report({'INFO'}, str(err))
                return {'CANCELLED'}

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
            return {'FINISHED'}
        except OSError as err:
            self.report({'INFO'}, str(err))
            return {'CANCELLED'}

    def invoke(self, context, event):
        """Call when user accesses operator via menu."""
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        """Draw modal pop up."""
        layout = self.layout
        layout.prop(self, 'new_folder_name')
