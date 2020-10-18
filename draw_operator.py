import bpy
from bpy.types import Operator


class MT_OT_AM_Draw_Operator(Operator):
    bl_idname = "view3d.mt_am_draw"
    bl_label = "MakeTile ui Widget Operator"
    bl_options = {'REGISTER'}

    def __init__(self):
        self.draw_handle = None
        self.widgets = []  # list of widgets to be drawn by this operator

    def init_widgets(self, context, widgets):
        for widget in widgets:
            widget.init(context)
        self.widgets.extend(widgets)

    def invoke(self, context, event):
        self.on_invoke(context, event)

        args = (self, context)
        self.register_handlers(args, context)
        context.window_manager.modal_handler_add(self)

        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        """Handle user input.

        Args:
            context (bpy.context): context
            event (event): mouse or keyboard event
        """
        # make sure we always redraw 3d view if we are drawing
        if context.area:
            context.area.tag_redraw()

        # handle events in widgets
        if self.handle_widget_events(event):
            return {'RUNNING_MODAL'}

        # close widget if Esc is pressed and end modal
        if event.type == 'ESC':
            self.unregister_handlers(context)
            return {'CANCELLED'}

        return {'PASS_THROUGH'}

    def register_handlers(self, args, context):
        """Register the draw handler.

        Args:
            args (tuple(bpy.types.Operator, bpy.context)): args
            context (bpy.context): context
        """
        self.draw_handle = bpy.types.SpaceView3D.draw_handler_add(self.draw_callback_px, args, "WINDOW", "POST_PIXEL")

    def unregister_handlers(self, context):
        """Unregister the draw handler

        Args:
            context (bpy.context): context
        """
        bpy.types.SpaceView3D.draw_handler_remove(self.draw_handle, "WINDOW")
        self.draw_handle = None

    def handle_widget_events(self, event):
        """Handle mouse and keyboard events.

        Args:
            event (bpy.types.Event): Mouse or keyboard event

        Returns:
            Bool: Whether the event was handled
        """
        result = False
        for widget in self.widgets:
            if widget.handle_event(event):
                result = True
        return result

    def on_invoke(self, context, event):
        pass

    def finish(self, context):
        self.unregister_handlers(context)
        return {"FINISHED"}

    def draw_callback_px(self, op, context):
        for widget in self.widgets:
            widget.draw()
