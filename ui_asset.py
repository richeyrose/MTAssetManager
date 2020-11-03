import gpu
import bgl
import bpy

from gpu_extras.batch import batch_for_shader
from .ui_widget import MT_UI_AM_Widget
from .ui_drag_thumb import MT_AM_UI_Drag_Thumb
from .preferences import get_prefs
from .app_handlers import load_missing_preview_image

class MT_AM_UI_Asset(MT_UI_AM_Widget):
    def __init__(self, x, y, width, height, asset, asset_bar, index, op):
        super().__init__(x, y, width, height)
        self._asset_desc = asset
        self._name = asset["Name"]
        self._slug = asset["Slug"]
        self._category = asset["Category"]
        self._filepath = asset["FilePath"]
        self._preview_image_path = asset["PreviewImagePath"]
        self._description = asset["Description"]
        self._URI = asset["URI"]
        self._author = asset["Author"]
        self._license = asset["License"]
        self._type = asset["Type"]
        self._tags = asset["Tags"]

        self.asset_bar = asset_bar
        self.op = op
        self._index = index  # index number in bar.current_assets

        self._drag_offset_x = 0
        self._drag_offset_y = 0
        self._dragging = False

        self._draw = False

        self.context = bpy.context
        self._preview_image = self.get_preview_image(self.context)

        self.prefs = get_prefs()
        self._drag_thumb = None

    def get_preview_image(self, context):
        bar_props = context.scene.mt_bar_props
        filename = self._preview_image_path.rsplit('\\', 1)[1]
        try:
            return bpy.data.images[filename]
        except KeyError:
            try:
                return bar_props['missing_preview_image']
            except KeyError:
                missing_image = context.scene.mt_bar_props['missing_preview_image'] = load_missing_preview_image()
                return missing_image

    def update(self, context, x, y):
        self._set_origin()

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
        try:
            if self._preview_image.gl_load():
                raise Exception()
        except ReferenceError:
            self._preview_image = self.get_preview_image(context)

    def draw(self):
        # Check if there is space to draw asset in asset bar
        if self.asset_bar.show_assets \
            and self._index >= self.asset_bar.first_asset_index \
                and self._index <= self.asset_bar.last_asset_index:

            self._draw = True

            # draw thumbnail image
            # batch shader
            self.update(self.context, self.x, self.y )

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

            # draw hovered transparency
            if self.hovered:
                self.update_hover(self.x, self.y)
                self.hover_shader.bind()
                self.hover_shader.uniform_float("color", self.prefs.asset_bar_item_hover_color)
                bgl.glEnable(bgl.GL_BLEND)
                self.hover_panel.draw(self.hover_shader)
                bgl.glDisable(bgl.GL_BLEND)
        else:
            self._draw = False

    def init(self, context):
        self.context = context
        self._set_origin()

    @property
    def asset_desc(self):
        return self._asset_desc

    @property
    def preview_image(self):
        return self._preview_image

    def mouse_down(self, x, y):
        # only handle events if we are drawing asset
        if self._draw and self.hovered:
            # spawn a draggable thumb nail we can place in the scene
            self._drag_thumb = MT_AM_UI_Drag_Thumb(x, y, self.width, self.height, self, self.asset_bar, self.op)
            self._drag_thumb.init(bpy.context)
            self.asset_bar.drag_thumbs.append(self._drag_thumb)
            return True

        return False

    def mouse_enter(self, event, x, y):
        pass

    def mouse_leave(self, event, x, y):
        pass

    def _set_origin(self):
        """Set origin of asset.

        Takes into account asset index, nav button width, asset bar width, and
        asset bar first_asset_index
        """
        self.x = self.asset_bar.x + self.prefs.asset_bar_nav_button_width + (
            self.width * (self._index)) - (self.asset_bar.first_asset_index * self.width)
        self.y = self.asset_bar.y

    def remove_drag_thumb(self, thumb):
        """Remove the draggable thumbnail from asset bar.

        Args:
            thumb (MT_AM_UI_Drag_Thumb): thumbnail
        """
        self.asset_bar.drag_thumbs.remove(thumb)
