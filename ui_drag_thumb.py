import gpu
import bgl
import bpy

from gpu_extras.batch import batch_for_shader
from .ui_widget import MT_UI_AM_Widget
from .preferences import get_prefs
from .spawn import spawn_object, spawn_collection, spawn_material

class MT_AM_UI_Drag_Thumb(MT_UI_AM_Widget):
    """Draggable thumbnail of asset used for spawning into scene."""
    def __init__(self, x, y, width, height, asset, op):
        self.x = x
        self.y = y
        self.width = asset.width
        self.height = asset.height
        self.asset = asset
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
            self.update(self.x, self.y)

    def mouse_up(self, x, y):
        if self._dragging:
            self._dragging = False
            self.spawn_at_cursor(x, y)
            self.asset.remove_drag_thumb(self)
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

        # send image to gpu if it isn't there already
        if self._preview_image.gl_load():
            raise Exception()

    def draw(self):
        # draw thumbnail image
        # batch shader
        self.update(self.x, self.y)

        # texture identifier on gpu
        texture_id = self._preview_image.bindcode

        bgl.glEnable(bgl.GL_BLEND)
        # bind texture to image unit 0
        bgl.glActiveTexture(bgl.GL_TEXTURE0)
        bgl.glBindTexture(bgl.GL_TEXTURE_2D, texture_id)

        self.shader.bind()
        # tell shader to use the image that is bound to image unit 0
        self.shader.uniform_int("image", 0)
        self.batch_panel.draw(self.shader)
        bgl.glDisable(bgl.GL_BLEND)

    def spawn_at_cursor(self, x, y):
        asset_desc = self.asset.asset_desc
        if asset_desc['Type'] == 'OBJECTS':
            spawn_object(self, self.context, self.asset.asset_desc, x, y, self.op)
        elif asset_desc['Type'] == 'COLLECTIONS':
            spawn_collection(self, self.context, self.asset.asset_desc, x, y, self.op)
        elif asset_desc['Type'] == 'MATERIALS':
            spawn_material(self, self.context, self.asset.asset_desc, x, y, self.op)
