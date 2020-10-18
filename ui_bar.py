import math
import gpu
import bgl
import bpy

from  gpu_extras.batch import batch_for_shader
from .preferences import get_prefs


class MT_UI_AM_Widget:
    def __init__(self, x, y, width, height):
        self.x = x  # x origin
        self.y = y  # y origin
        self.width = width
        self.height = height
        self._bg_color = (0.8, 0.8, 0.8, 1.0)
        self._hovered = False  # whether the mouse is over the widget
        self._mouse_down = False
        self.context = None

    def draw(self):
        self.shader.bind()
        # set color of widget
        self.shader.uniform_float("color", self.bg_color)

        # draw the panel
        bgl.glEnable(bgl.GL_BLEND)
        self.batch_panel.draw(self.shader)
        bgl.glDisable(bgl.GL_BLEND)

    def init(self, context):
        self.context = context
        self.update(self.x, self.y)

    @property
    def bg_color(self):
        """Get background color.

        Returns:
            tuple[4]: RGBA
        """
        return self._bg_color

    @bg_color.setter
    def bg_color(self, value):
        self._bg_color = value

    def set_location(self, x, y):
        """Set the origin of the widget.

        Args:
            x (int): x origin
            y (int): y origin
        """
        self.x = x
        self.y = y
        self.update(x, y)

    def update(self, x, y):
        """Set the shader properties.

        Args:
            x (int): x origin
            y (int): y origin
        """
        self.x = x
        self.y = y
        # bottom left, top left, top right, bottom right
        indices = ((0, 1, 2), (0, 2, 3))
        verts = (
            (self.x, self.y),
            (self.x, self.y + self.height),
            (self.x + self.width, self.y + self.height),
            (self.x + self.width, self.y))

        self.shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
        self.batch_panel = batch_for_shader(self.shader, 'TRIS', {"pos": verts}, indices=indices)

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

    def is_hovered(self, mouse_x, mouse_y):
        """Return True if mouse is over widget

        Args:
            mouse_x (int): mouse x location
            mouse_y (int): mouse y location

        Returns:
            Bool: bool
        """
        x = self.x
        y = self.y
        width = self.width
        height = self.height

        if mouse_x >= x and mouse_x <= (x + width) and mouse_y >= y and mouse_y <= (y + height):
            return True
        else:
            return False

    def mouse_enter(self, event, x, y):
        pass

    def mouse_leave(self, event, x, y):
        pass

    def mouse_down(self, x, y):
        pass

    def mouse_up(self, x, y):
        pass


class MT_UI_AM_Asset_Bar(MT_UI_AM_Widget):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height)
        self.prefs = get_prefs()
        self._show_assets = False
        self._first_asset_index = 0  # the first asset to show
        self._last_asset_index = 0  # the last asset to show
        self._current_assets = None
        self.widgets = []

    def init(self, context):
        self.context = context
        self.set_asset_bar_dimensions()
        self.bg_color = self.prefs.asset_bar_bg_color
        self.update(self.x, self.y)

    def draw(self):
        self.set_asset_bar_dimensions()
        self.update(self.x, self.y)
        super().draw()

    @property
    def first_asset_index(self):
        return self._first_asset_index

    @property
    def last_asset_index(self):
        return self._last_asset_index

    @property
    def show_assets(self):
        return self._show_assets

    @first_asset_index.setter
    def first_asset_index(self, value):
        self._first_asset_index = value

    @property
    def current_assets(self):
        return self._current_assets

    @current_assets.setter
    def current_assets(self, value):
        self._current_assets = value

    def set_asset_bar_dimensions(self):
        area = self.context.area  # the 3D viewport
        regions = area.regions  # Regions in the 3D viewport

        toolbar = None  # the left toolbar
        ui = None  # N panel
        hud = None  # info panel

        for region in regions:
            if region.type == 'TOOLS':
                toolbar = region
            if region.type == 'UI':
                ui = region
            if region.type == 'HUD':
                hud = region

        # set the width of the asset bar to the width of the 3d viewport - 10px
        self.width = abs(area.width - 10)

        # set the height of the asset bar to the height of each asset item
        self.height = self.prefs.asset_item_dimensions

        # if N panel is showing resize asset bar so it doesn't overlap
        if ui.height >= area.height - self.height:
            self.width = abs(self.width - ui.width)

        # if left toolbar is showing resize asset bar so it doesn't overlap
        if toolbar.height >= area.height - self.height:
            self.width = abs(self.width - toolbar.width)

        self.x = 5
        self.y = 5

        # if HUD is showing resize bar and set origin
        if hud is not None:
            if hud.x > 0:
                self.width = abs(self.width - hud.width - 5)
                self.x = self.x + hud.width + 5

        # if left toolbar is showing set origin
        if toolbar.height >= area.height - self.height:
            self.x = self.x + toolbar.width

        # if asset bar width is greater than width of single asset show assets
        if self.width >= self.prefs.asset_item_dimensions:
            self._show_assets = True
        else:
            self._show_assets = False

        # set index of last asset to show based on bar width
        last_asset_index = self._first_asset_index + (math.floor(self.width / self.prefs.asset_item_dimensions)) -1
        if last_asset_index < 0:
            self._last_asset_index = 0
        else:
            self._last_asset_index = last_asset_index


class MT_AM_UI_Asset_Thumb(MT_UI_AM_Widget):
    def __init__(self, x, y, width, height, asset, bar, index):
        super().__init__(x, y, width, height)
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
        self._bar = bar
        self._index = index  # index number in bar.current_assets
        self._draw = False

        context = bpy.context
        self._preview_image = self.get_preview_image(context)


    def get_preview_image(self, context):
        bar_props = context.scene.mt_bar_props
        filename = self._preview_image_path.rsplit('\\', 1)[1]
        if filename in bpy.data.images.keys():
            return bpy.data.images[filename]
        else:
            return bar_props['missing_preview_image']

    def update(self, x, y):
        self.x = x
        self.y = y

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
        # Check if there is space to draw asset in asset bar
        if self._bar.show_assets and self._index >= self._bar.first_asset_index and self._index <= self._bar.last_asset_index:
            self._draw = True
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
        else:
            self._draw = False

    def init(self, context):
        self.x = self._bar.x
        self.y = self._bar.y
        # set x origin of asset
        self.x = self.x + (self.width * (self._index + self._bar.first_asset_index))

    def mouse_down(self, x, y):
        # only handle events if we are drawing thumbnail
        if self._draw:
            if self._hovered:
                print(self._name)
        return False