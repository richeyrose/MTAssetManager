import math
import bpy
from .preferences import get_prefs
from .ui_widget import MT_UI_AM_Widget
from .ui_nav_arrow import MT_UI_AM_Left_Nav_Arrow, MT_UI_AM_Right_Nav_Arrow

#TODO #4 add pop over preview with larger image and meta data
class MT_UI_AM_Asset_Bar(MT_UI_AM_Widget):
    """The asset bar UI element."""
    def __init__(self, x, y, width, height, op):
        super().__init__(x, y, width, height)
        self.prefs = get_prefs()
        self._show_assets = False
        self._first_asset_index = 0  # the first asset to show
        self._last_asset_index = 0  # the last asset to show
        self.offset = 0
        self.nav_arrows = []
        self.assets = []
        self.drag_thumbs = []
        self.op = op

    def init(self, context):
        """Initialise the asset bar.

        Args:
            context (bpy.context): context
        """
        # initialise the asset bar
        self.context = context
        self.set_asset_bar_dimensions()
        self.bg_color = self.prefs.asset_bar_bg_color
        self.update(self.x, self.y)

        # initialise the nav arrows
        left_nav = MT_UI_AM_Left_Nav_Arrow(50, 50, 300, 200, self)
        right_nav = MT_UI_AM_Right_Nav_Arrow(50, 50, 300, 200, self)
        self.nav_arrows = [left_nav, right_nav]
        for arrow in self.nav_arrows:
            arrow.init(context)

    def draw(self):
        """Draw the asset bar.
        """
        # draw asset bar
        self.set_asset_bar_dimensions()
        self.update(self.x, self.y)
        super().draw()

        # draw nav arrows
        for arrow in self.nav_arrows:
            arrow.draw()

        # draw assets
        for asset in self.assets:
            asset.draw()

        # draw draggable thumbnail
        for thumb in self.drag_thumbs:
            thumb.draw()

    @property
    def first_asset_index(self):
        return self._first_asset_index

    @property
    def last_asset_index(self):
        return self._last_asset_index

    @last_asset_index.setter
    def last_asset_index(self, value):
        self._last_asset_index = value

    @property
    def show_assets(self):
        return self._show_assets

    @first_asset_index.setter
    def first_asset_index(self, value):
        self._first_asset_index = value

    def deselect_all(self):
        """Deselect all assets.
        """
        for asset in self.assets:
            asset.selected = False

    def increment_asset_index(self, value):
        """Increment the index of the first and last asset to display in bar.

        Args:
            value (int): amount to increment by
        """
        self._first_asset_index = self._first_asset_index + value
        self._last_asset_index = self._last_asset_index - value

    def handle_event(self, event):
        """Handle Keyboard and Mouse events.

        Args:
            event (bpy.types.Event): Mouse or Keyboard event

        Returns:
            Bool: True if no more event processing should be done by other elements, otherwise False.
        """
        x = event.mouse_region_x
        y = event.mouse_region_y

        result = False
        # handle scrolling
        if event.type == 'WHEELUPMOUSE':
            result = self.wheel_up()

        elif event.type == 'WHEELDOWNMOUSE':
            result = self.wheel_down()

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
            result = False

        # handle right click
        elif event.type == 'RIGHTMOUSE':
            if event.value == 'PRESS':
                if self.right_mouse_down(0, 0):
                    result = True

        # handle nav arrow events
        for arrow in self.nav_arrows:
            if arrow.handle_event(event):
                result = True

        # handle asset events
        for asset in self.assets:
            if asset.handle_event(event):
                result = True

        # handle draggable thumb events
        for thumb in self.drag_thumbs:
            if thumb.handle_event(event):
                result = True

        return result

    def right_mouse_down(self, x, y):
        """Draw paste asset menu on right click.

        Args:
            x (float): mouse x
            y (float): mouse y

        Returns:
            bool: Whether we are drawing menu.
        """
        for asset in self.assets:
            if asset.hovered:
                return False
        if self.hovered:
            bpy.ops.wm.call_menu(name=MT_AM_Paste_Asset_Menu.bl_idname)
            return True
        return False

    def wheel_up(self):
        """Handle wheel up event.

        Scrolls the assets in the asset bar.

        Returns:
            Bool: Return True if hovered
        """
        if self.hovered:
            if self.first_asset_index > 0:
                self.increment_asset_index(-1)
            # make sure we set any other widgets hovered state to false
            for asset in self.assets:
                asset.hovered = False
            return True
        return False

    def wheel_down(self):
        """Handle wheel down event.

        Scrolls the assets in the asset bar.

        Returns:
            Bool: Return True if hovered.
        """
        if self.hovered:
            self.increment_asset_index(1)
            for asset in self.assets:
                # make sure we set any other widgets hovered state to false
                asset.hovered = False
            return True
        return False

    def set_asset_bar_dimensions(self):
        """Set the dimensions of the asset bar.

        The asset bar needs to resize dynamically depending on both the size of the 3d viewport
        and the various elements such as the "N" bar and toolbar which are being displayed
        """
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
        if self.width >= self.prefs.asset_item_dimensions + (self.prefs.asset_bar_nav_button_width * 2):
            self._show_assets = True
        else:
            self._show_assets = False

        # set index of last asset to show based on bar width
        self._last_asset_index = self._first_asset_index + (
            math.floor((self.width - (self.prefs.asset_bar_nav_button_width * 2)) / self.prefs.asset_item_dimensions)) - 1


class MT_AM_Paste_Asset_Menu(bpy.types.Menu):
    """Paste Asset menu for asset bar."""
    bl_label = "Paste Asset"
    bl_idname = "AM_MT_paste_asset_menu"

    def draw(self, context):
        """Draw the menu."""
        layout = self.layout
        layout.operator("object.mt_paste_asset")
