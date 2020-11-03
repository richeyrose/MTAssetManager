import gpu
import bgl
import bpy

from  gpu_extras.batch import batch_for_shader

class MT_UI_AM_Widget:
    def __init__(self, x, y, width, height):
        self.x = x  # x origin
        self.y = y  # y origin
        self.width = width
        self.height = height
        self._bg_color = (0.8, 0.8, 0.8, 1.0)
        self.hovered = False  # whether the mouse is over the widget
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


    def update_hover(self, x, y):
        self._set_origin()
        # bottom left, top left, top right, bottom right
        indices = ((0, 1, 2), (0, 2, 3))
        verts = (
            (self.x, self.y),
            (self.x, self.y + self.height),
            (self.x + self.width, self.y + self.height),
            (self.x + self.width, self.y))

        self.hover_shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
        self.hover_panel = batch_for_shader(self.shader, 'TRIS', {"pos": verts}, indices=indices)

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
            if not self.hovered and hovered:
                self.hovered = True
                self.mouse_enter(event, x, y)
            # end hover
            elif self.hovered and not hovered:
                self.hovered = False
                self.mouse_leave(event, x, y)

            return False

        return False

    def is_hovered(self, mouse_x, mouse_y):
        """Return True if mouse is over widget.

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