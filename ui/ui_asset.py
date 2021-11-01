import os
import gpu
import bpy
import blf

from gpu_extras.batch import batch_for_shader
from .ui_widget import MT_UI_AM_Widget
from .ui_drag_thumb import MT_AM_UI_Drag_Thumb
from ..preferences import get_prefs
from bpy.types import Object, Material, Collection

class MT_AM_UI_Asset(MT_UI_AM_Widget):
    def __init__(self, x, y, width, height, asset, asset_bar, index, op):
        super().__init__(x, y, width, height)
        self.asset = asset
        self._metadata = asset.asset_data
        self._name = asset.name

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
        self.type_icon = self.get_type_icon(self.context)
        self.prefs = get_prefs()
        self._drag_thumb = None

    def get_preview_image(self, context):
        """Return the preview image for an asset. If no preview image is found returns a generic
        no preview image found image.

        Args:
            context (bpy.context): context

        Returns:
            bpy.types.Image: Image
        """
        bar_props = context.scene.mt_bar_props
        if self.asset.mt_preview_img:
            return self.asset.mt_preview_img
        else:
            return bar_props.missing_preview_icon

    def get_type_icon(self, context):
        bar_props = context.scene.mt_bar_props
        if type(self.asset) == Collection:
            return bar_props.collection_icon
        elif type(self.asset) == Material:
            return bar_props.material_icon
        elif type(self.asset) == Object:
            return bar_props.object_icon
        else:
            return bar_props.missing_preview_icon


    def handle_event(self, event):
        """Handle Mouse Events.

        Args:
            event (event): mouse event

        Returns:
            bool: Whether the event was handled
        """
        x = event.mouse_region_x
        y = event.mouse_region_y

        if event.type == 'LEFTMOUSE':
            if event.value == 'PRESS':
                if event.shift:
                    return self.shift_click()
                elif event.ctrl:
                    return self.ctrl_click()
                else:
                    self._mouse_down = True
                    return self.mouse_down(x, y)
            elif event.value == 'RELEASE':
                self._mouse_down = False
                return self.mouse_up(x, y)

        # elif event.type == 'RIGHTMOUSE':
        #     if event.value == 'PRESS':
        #         self._right_mouse_down = True
        #         return self.right_mouse_down(x, y)
        #     elif event.value == 'RELEASE':
        #         self._right_mouse_down = False
        #         return self.right_mouse_up(x, y)

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

    def update_icon(self):
        self._set_origin()

        indices = ((0, 1, 2), (2, 1, 3))

        x = self.x + self.width - 20
        y = self.y + self.height - 20
        coords = [
            (x, y),
            (x + 20, y),
            (x, y + 20),
            (x + 20, y + 20)]

        # UV Tiling
        crop = (0, 0, 1, 1)

        uvs = [(crop[0], crop[1]),
               (crop[2], crop[1]),
               (crop[0], crop[3]),
               (crop[2], crop[3])]

        self.shader = gpu.shader.from_builtin('2D_IMAGE')

        self.batch_icon = batch_for_shader(
            self.shader,
            'TRIS',
            {"pos": coords, "texCoord": uvs},
            indices=indices)

    def update_thumb(self):
        """Update thumbnail location.

        Args:
            context (bpy.context): [description]
            x ([type]): [description]
            y ([type]): [description]
        """
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

    def update_text_box(self, x, y):
        self._set_origin()
        # bottom left, top left, top right, bottom right
        indices = ((0, 1, 2), (0, 2, 3))
        verts = (
            (self.x, self.y),
            (self.x, self.y + 20),
            (self.x + self.width, self.y + 20),
            (self.x + self.width, self.y))

        self.text_box_shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
        self.text_box = batch_for_shader(
            self.text_box_shader,
            'TRIS',
            {"pos": verts},
            indices=indices)

    def draw(self):
        """Draw Asset Thumnails.
        """
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
                gpu.state.blend_set('ALPHA')
                self.select_panel.draw(self.select_shader)
                gpu.state.blend_set('NONE')

            # draw thumbnail image
            self.update_thumb()
            gpu.state.blend_set('ALPHA')
            self.shader.bind()
            image = self._preview_image
            tex = gpu.texture.from_image(image)
            self.shader.uniform_sampler("image", tex)
            self.batch_panel.draw(self.shader)

            # draw asset type icon in top right
            self.update_icon()
            gpu.state.blend_set('ALPHA')
            self.shader.bind()
            image = self.type_icon
            tex = gpu.texture.from_image(image)
            self.shader.uniform_sampler("image", tex)
            self.batch_icon.draw(self.shader)

            # draw text box at bottom of thumbnail
            self.update_text_box(self.x, self.y)
            self.text_box_shader.bind()
            self.text_box_shader.uniform_float("color", (0, 0, 0, 0.8))
            gpu.state.blend_set('ALPHA')
            self.text_box.draw(self.text_box_shader)

            # draw asset name at bottom of thumbnail
            text = self.asset.name
            text_dims = blf.dimensions(0, text)
            box_dims = self.width - 10
            if text_dims[0] <= box_dims:
                text_start = self.x + (self.width / 2) - (text_dims[0] / 2)
            else:
                text_start = self.x + 10

            blf.position(0, text_start, self.y + 5, 0)
            blf.size(0, 14, 72)
            blf.color(0, 1, 1, 1, 0.8)
            blf.enable(0, blf.CLIPPING)
            blf.clipping(0, self.x, self.y, self.x + self.width - 5, self.y + self.height - 5)
            blf.draw(0, self.asset.name)
            blf.disable(0, blf.CLIPPING)

            # draw hovered transparency
            if self.hovered:
                self.update_hover(self.x, self.y)
                self.hover_shader.bind()
                self.hover_shader.uniform_float(
                    "color",
                    (self.prefs.asset_bar_item_hover_color))
                gpu.state.blend_set('ALPHA')
                self.hover_panel.draw(self.hover_shader)



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

    # def right_mouse_down(self, x, y):
    #     if self._draw and self.hovered:
    #         # store current asset description for edit asset metadata operator
    #         bpy.context.scene.mt_am_props.current_asset_desc = self.asset_desc
    #         if not self.selected:
    #             self.asset_bar.deselect_all()
    #             self.selected = True
    #         bpy.ops.wm.call_menu(name=MT_AM_Edit_Asset_Menu.bl_idname)
    #         return True
    #     return False

    def delete_assets(self):
        """Call appropriate delete asset operator if we are hovered over asset bar."""
        if self.hovered:
            selected_assets = [asset for asset in self.asset_bar.assets if asset.selected]
            if selected_assets:
                bpy.ops.object.delete_selected_assets_from_library('INVOKE_DEFAULT')
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

# class MT_AM_Edit_Asset_Menu(bpy.types.Menu):
#     bl_label = "Edit Asset"
#     bl_idname = "AM_MT_edit_asset_menu"

#     def draw(self, context):
#         props = context.scene.mt_am_props
#         layout = self.layout

#         layout.operator_context = 'INVOKE_DEFAULT'

#         layout.operator("object.mt_cut_asset")
#         # layout.operator("object.mt_copy_asset")
#         layout.operator("object.mt_paste_asset")
#         layout.operator("object.delete_selected_assets_from_library")

#         layout.separator()

#         asset_desc = bpy.context.scene.mt_am_props.current_asset_desc
#         op = layout.operator("object.mt_am_edit_asset_metadata")
#         op.Name = asset_desc["Name"]
#         op.filepath = asset_desc["filepath"]
#         op.PreviewImagePath = asset_desc["PreviewImagePath"]
#         op.desc = asset_desc["desc"]
#         op.URI = asset_desc["URI"]
#         op.author = asset_desc["author"]
#         op.License = asset_desc["License"]
#         op.tags = ", ".join(asset_desc["tags"])



