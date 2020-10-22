import gpu
import bgl
import bpy

from gpu_extras.batch import batch_for_shader
from .ui_widget import MT_UI_AM_Widget
from .preferences import get_prefs


class MT_AM_UI_Drag_Thumb(MT_UI_AM_Widget):
    """Draggable thumbnail of asset used for spawning into scene."""
    def __init__(self, x, y, width, height, asset):
        self.x = x
        self.y = y
        self.width = asset.width
        self.height = asset.height
        self.asset = asset

        super().__init__(x, y, width, height)
        self._dragging = True

        self._preview_image = asset.preview_image

    def handle_event(self, event):
        x = event.mouse_region_x
        y = event.mouse_region_y

        if event.type == 'LEFTMOUSE':
            if event.value == 'PRESS':
                self._mouse_down = True
                return self.mouse_down(x, y)
            elif event.value == 'RELEASE':
                self._mouse_down = False
                return self.mouse_up(x, y)

        elif event.type == 'MOUSEMOVE':
            self.mouse_move(x, y)
            hovered = self.is_hovered(x, y)
            # begin hover
            if not self._hovered and hovered:
                self._hovered = True
                self.mouse_enter(event, x, y)
            # end hover
            elif self._hovered and not hovered:
                self._hovered = False
                self.mouse_leave(event, x, y)

            return False

        return False

    def mouse_move(self, x, y):
        if self._dragging:
            self._set_origin(x, y)

    def mouse_up(self, x, y):
        if self._dragging:
            self._dragging = False
            self.asset._asset_bar.op.assets.remove(self)
        return False

    def _set_origin(self, x, y):
        self.x = x
        self.y = y
        self.update(x, y)
