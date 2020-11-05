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
        self.selected = False

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

    def handle_event(self, event):
        x = event.mouse_region_x
        y = event.mouse_region_y

        if event.type == 'LEFTMOUSE':
            if event.value == 'PRESS':
                if event.shift:
                    return self.shift_click()
                elif event.ctrl:
                    return self.ctrl_click(x, y)
                else:
                    self._mouse_down = True
                    return self.mouse_down(x, y)
            elif event.value == 'RELEASE':
                self._mouse_down = False
                return self.mouse_up(x, y)

        elif event.type == 'RIGHTMOUSE':
            if event.value == 'PRESS':
                self._right_mouse_down = True
                return self.right_mouse_down()
            elif event.value == 'RELEASE':
                self._right_mouse_down = False
                return self.right_mouse_up(x, y)

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

        # handle delete events
        elif event.type in ['DEL', 'X'] and event.value == 'PRESS':
            return self.delete_assets()

        return False

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

            # draw selected transparency
            if self.selected:
                self.update_selected(self.x, self.y)
                self.select_shader.bind()
                self.select_shader.uniform_float("color", self.prefs.asset_bar_item_selected_color)
                bgl.glEnable(bgl.GL_BLEND)
                self.select_panel.draw(self.select_shader)
                bgl.glDisable(bgl.GL_BLEND)

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
            self.asset_bar.deselect_all()
            self.selected = True

            # spawn a draggable thumb nail we can place in the scene
            self._drag_thumb = MT_AM_UI_Drag_Thumb(x, y, self.width, self.height, self, self.asset_bar, self.op)
            self._drag_thumb.init(bpy.context)
            self.asset_bar.drag_thumbs.append(self._drag_thumb)
            return True

        return False

    def shift_click(self):
        """Implement standard shift click selection.

        Returns:
            [Bool]: Boolean. Whether event was handled
        """
        if self._draw and self.hovered:
            assets = self.asset_bar.assets
            first_selected_index = 0
            for asset in assets:
                if asset.selected:
                    first_selected_index = assets.index(asset)
                    break

            if self._index >= first_selected_index:
                if not self.selected:
                    for asset in assets[first_selected_index:self._index]:
                        asset.selected = True
                    self.selected = True
                    return True
                else:
                    for asset in assets:
                        asset.selected = False
                    for asset in assets[first_selected_index:self._index]:
                        asset.selected = True
                    self.selected = True
                    return True
            else:
                last_selected_index = 0
                for asset in reversed(assets):
                    if asset.selected:
                        last_selected_index = assets.index(asset)
                        break
                if not self.selected:
                    for asset in assets[self._index:last_selected_index]:
                        asset.selected = True
                    return True
                else:
                    for asset in assets:
                        asset.selected = False
                    for asset in assets[self._index:last_selected_index]:
                        asset.selected = True
                    return True
        return False

    def ctrl_click(self):
        """Implements standard ctrl click selection.

        Returns:
            Bool: Boolean. Whether event has been handled.
        """
        if self._draw and self.hovered:
            if self.selected:
                self.selected = False
            else:
                self.selected = True
            return True
        return False

    def right_mouse_down(self):
        if self._draw and self.hovered:
            # store current asset description
            bpy.context.scene.mt_am_props.current_asset_desc = self.asset_desc
            bpy.ops.wm.call_menu(name=MT_AM_Edit_Asset_Menu.bl_idname)
            return True
        return False

    def delete_assets(self):
        """Call appropriate delete asset operator if we are hovered over asset bar."""
        if self.hovered:
            selected_assets = [asset for asset in self.asset_bar.assets if asset.selected]
            if selected_assets:
                bpy.ops.object.delete_selected_assets_from_library('INVOKE_DEFAULT')
                return True
            else:
                bpy.context.scene.mt_am_props.current_asset_desc = self.asset_desc
                bpy.ops.object.delete_asset_from_library('INVOKE_DEFAULT')
                return True
        return False

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

class MT_AM_Edit_Asset_Menu(bpy.types.Menu):
    bl_label = "Edit Asset"
    bl_idname = "AM_MT_edit_asset_menu"

    def __init__(self):
        super().__init__()

    def draw(self, context):
        props = context.scene.mt_am_props
        selected_assets = [asset for asset in props.asset_bar.assets if asset.selected]
        layout = self.layout

        if selected_assets == []:
            layout.operator_context = 'INVOKE_DEFAULT'
            layout.operator("object.delete_asset_from_library")

        layout.operator_context = 'INVOKE_DEFAULT'
        layout.operator("object.delete_selected_assets_from_library")
        asset_desc = bpy.context.scene.mt_am_props.current_asset_desc

        layout.operator("object.mt_cut_asset")
        layout.operator("object.mt_copy_asset")
        layout.operator("object.mt_paste_asset")

        layout.operator_context = 'INVOKE_DEFAULT'
        op = layout.operator("object.mt_am_edit_asset_metadata")
        op.Name = asset_desc["Name"]
        op.FilePath = asset_desc["FilePath"]
        op.PreviewImagePath = asset_desc["PreviewImagePath"]
        op.Description = asset_desc["Description"]
        op.URI = asset_desc["URI"]
        op.Author = asset_desc["Author"]
        op.License = asset_desc["License"]
        op.Tags = ", ".join(asset_desc["Tags"])

