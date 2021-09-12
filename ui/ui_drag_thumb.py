import gpu
import bgl

from gpu_extras.batch import batch_for_shader
from .ui_widget import MT_UI_AM_Widget
from ..spawn import spawn_object, spawn_collection, spawn_material


class MT_AM_UI_Drag_Thumb(MT_UI_AM_Widget):
    """Draggable thumbnail of asset used for spawning into scene."""
    def __init__(self, x, y, width, height, asset, asset_bar, op):
        self.x = x
        self.y = y
        self.width = asset.width
        self.height = asset.height
        self.asset = asset
        self.asset_bar = asset_bar
        self.op = op

        super().__init__(x, y, self.width, self.height)

        self._dragging = True
        self.drag_offset_x = 0
        self.drag_offset_y = 0

        self._preview_image = asset.preview_image

    def init(self, context):
        self.context = context
        self.drag_offset_x = self.x - self.asset.x
        self.drag_offset_y = self.y - self.asset.y
        self._set_origin(self.x, self.y)
        self.update(self.x, self.y)

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
            if not self.hovered and hovered:
                self.hovered = True
                self.mouse_enter(event, x, y)
            # end hover
            elif self.hovered and not hovered:
                self.hovered = False
                self.mouse_leave(event, x, y)

            return False

        return False

    def mouse_move(self, x, y):
        if self._dragging:
            self._set_origin(x, y)
            self.update(self.x, self.y)

    def mouse_up(self, x, y):
        """Handle mouse up event.

        If we are not hovered over the asset bar we spawn the asset corresponding to the
        dragged thumbnail at the cursor.

        Args:
            x (float): mouse x
            y (float): mouse y

        Returns:
            bool: Whether event was handled
        """
        if self._dragging:
            self._dragging = False
            self.asset.remove_drag_thumb(self)
            if not self.asset_bar.hovered:
                # spawn asset at cursor location
                asset_desc = self.asset.asset_desc
                if asset_desc['Type'] == 'OBJECTS':
                    if spawn_object(self.context, self.asset.asset_desc, x, y):
                        return True
                elif asset_desc['Type'] == 'COLLECTIONS':
                    if spawn_collection(self.context, self.asset.asset_desc, x, y):
                        return True
                else:
                    if spawn_material(self.context, self.asset.asset_desc, x, y):
                        return True
        return False

    def _set_origin(self, x, y):
        self.x = x - self.drag_offset_x
        self.y = y - self.drag_offset_y

    def update(self, x, y):
        indices = ((0, 1, 2), (2, 1, 3))

        coords = [
            (self.x, self.y),
            (self.x + self.width, self.y),
            (self.x, self.y + self.height),
            (self.x + self.width, self.y + self.height)]

        # UV Tiling
        crop = (0, 0, 1, 1)

        uvs = [(crop[0], crop[1]),
               (crop[2], crop[1]),
               (crop[0], crop[3]),
               (crop[2], crop[3])]

        self.shader = gpu.shader.from_builtin('2D_IMAGE')
        self.batch_panel = batch_for_shader(
            self.shader,
            'TRIS',
            {"pos": coords, "texCoord": uvs},
            indices=indices)

    def draw(self):
        """Draw thumbnail image.
        """
        # batch shader
        self.update(self.x, self.y)

        gpu.state.blend_set('ALPHA')
        self.shader.bind()
        tex = gpu.texture.from_image(self._preview_image)
        self.shader.uniform_sampler("image", tex)
        self.batch_panel.draw(self.shader)

