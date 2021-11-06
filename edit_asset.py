import bpy
from bpy.types import Operator
from bpy.props import StringProperty

class MT_OT_open_containing_blend_file(Operator):
    """Open the blend file that contains the active asset"""

    bl_idname = "asset.mt_open_containing_blend_file"
    bl_label = "Open Asset Blend File"
    bl_options = {'REGISTER'}

    _process = None  # Optional[subprocess.Popen]

    filepath: StringProperty(
        name="Filepath",
        subtype="FILE_PATH"
    )

    name: StringProperty(
        name="Asset Name"
    )

    def execute(self, context):
        self.open_in_new_blender(self.filepath)

        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)

        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type != 'TIMER':
            return {'PASS_THROUGH'}

        if self._process is None:
            self.report({'ERROR'}, "Unable to find any running process")
            self.cancel(context)
            return {'CANCELLED'}

        returncode = self._process.poll()
        if returncode is None:
            # Process is still running.
            return {'RUNNING_MODAL'}

        if returncode:
            self.report({'WARNING'}, "Blender sub-process exited with error code %d" % returncode)

        self.cancel(context)
        return {'FINISHED'}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)

    def open_in_new_blender(self, filepath):
        import subprocess

        cli_args = [bpy.app.binary_path, str(filepath)]
        self._process = subprocess.Popen(cli_args)
