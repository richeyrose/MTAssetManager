import gpu
from ..preferences import get_prefs
from .ui_widget import MT_UI_AM_Widget

class MT_UI_AM_Nav_Arrow(MT_UI_AM_Widget):
    def __init__(self, x, y, width, height, asset_bar):
        super().__init__(x, y, width, height)
        self._asset_bar = asset_bar
        self.prefs = get_prefs()
        self.context = None

    def init(self, context):
        self.context = context
        self.height = self._asset_bar.height
        self.width = self.prefs.asset_bar_nav_button_width
        self._set_origin()
        self.bg_color = self.prefs.asset_bar_nav_button_color
        self.update(self.x, self.y)

    def draw(self):
        self._set_origin()
        self.update(self.x, self.y)
        super().draw()

        # draw hovered transparency
        if self.hovered:
            self.update_hover(self.x, self.y)
            self.hover_shader.bind()
            self.hover_shader.uniform_float("color", self.prefs.asset_bar_item_hover_color)
            gpu.state.blend_set('ALPHA')
            self.hover_panel.draw(self.hover_shader)
            gpu.state.blend_set('NONE')

    def _set_origin(self):
        pass

class MT_UI_AM_Left_Nav_Arrow(MT_UI_AM_Nav_Arrow):
    def _set_origin(self):
        self.x = self._asset_bar.x
        self.y = self._asset_bar.y

    def mouse_down(self, x, y):
        if self.hovered:
            if self._asset_bar.first_asset_index > 0:
                self._asset_bar.increment_asset_index(-1)
        return False

class MT_UI_AM_Right_Nav_Arrow(MT_UI_AM_Nav_Arrow):
    def _set_origin(self):
        self.x = self._asset_bar.x + self._asset_bar.width - self.width
        self.y = self._asset_bar.y

    def mouse_down(self, x, y):
        if self.hovered:
            self._asset_bar.increment_asset_index(1)
        return False
