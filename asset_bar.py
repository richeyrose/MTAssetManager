import bpy
from math import floor
from bpy.types import Operator
from bpy.props import StringProperty, BoolProperty
from .preferences import get_prefs
from .categories import get_child_cats, get_parent_cat_slug, get_category
from .assets import get_assets_by_cat, append_preview_images
from .ui_bgl import draw_rect, draw_image
from .draw_operator import MT_OT_AM_Draw_Operator
from .ui_bar import MT_UI_AM_Asset_Bar, MT_AM_UI_Asset_Thumb

class MT_OT_AM_Asset_Bar(MT_OT_AM_Draw_Operator, Operator):
    bl_idname = "view3d.mt_asset_bar"
    bl_label = "MakeTile Asset Bar UI"
    bl_options = {'REGISTER'}

    category_slug: StringProperty(
        name="Category",
        default="None",
    )

    asset_bar = None

    def invoke(self, context, event):
        prefs = get_prefs()
        am_props = context.scene.mt_am_props
        bar_props = context.scene.mt_bar_props
        # update properties
        context.scene.mt_am_props.parent_category = am_props.active_category
        context.scene.mt_am_props.active_category = self.category_slug

        # set child_cats
        for cat in am_props['child_cats']:
            if cat['Slug'] == am_props.active_category:
                am_props['child_cats'] = cat['Children']
                break

        # get assets in active_category
        active_category = am_props.active_category

        if active_category:
            current_assets = get_assets_by_cat(active_category)
            append_preview_images(current_assets)

        if MT_OT_AM_Asset_Bar.asset_bar:
            # set asset bar assets to current assets
            MT_OT_AM_Asset_Bar.asset_bar.current_assets = current_assets
            MT_OT_AM_Asset_Bar.asset_bar.first_asset_index = 0

        # Check if we are already drawing asset bar and add it if not
        args = (self, context)
        if not MT_OT_AM_Asset_Bar.asset_bar:
            # initialise bar
            asset_bar = MT_OT_AM_Asset_Bar.asset_bar = MT_UI_AM_Asset_Bar(50, 50, 300, 200)  # The main asset bar
            asset_bar.current_assets = current_assets
            widgets = []
            for asset in current_assets:
                widget = MT_AM_UI_Asset_Thumb(50, 50, prefs.asset_item_dimensions, prefs.asset_item_dimensions, asset)
                widgets.append(widget)
            widgets.append(asset_bar)
            self.init_widgets(context, widgets)
            self.register_handlers(args, context)
            context.window_manager.modal_handler_add(self)

        return {'RUNNING_MODAL'}

    def unregister_handlers(self, context):
        super().unregister_handlers(context)
        MT_OT_AM_Asset_Bar.asset_bar = None


    def draw_callback_asset_bar(self, context):
        """Draw the asset bar.

        Args:
            context (bpy.types.context): context
        """
        prefs = get_prefs()
        area = context.area  # the 3d viewport

        if area.type == 'VIEW_3D':
            # Get dimensions of entire bar
            vis_props = get_asset_bar_dimensions(context, prefs)
            # get color of outer rectangle
            vis_props['color'] = prefs.asset_bar_bg_color
            # draw outer rectangle
            draw_rect(vis_props)
            # draw asset bar items
            draw_asset_bar_items(context, prefs, vis_props)
            # draw asset bar header bar
            draw_asset_bar_header(prefs, vis_props)

            # draw forward and back scroll buttons


def draw_asset_bar_header(prefs, vis_props):
    """Draw the header for the asset bar.

    Args:
        prefs ('MTAssetManager.preferences.MT_AM_Prefs'): preferences
        vis_props (dict{x: int, y: int, width: int, height: int, color: bpy_float[4]}): [description]
    """
    header_props = vis_props.copy()
    header_props['y'] = vis_props['y'] + prefs.asset_item_dimensions
    header_props['height'] = prefs.asset_bar_header_height
    header_props['color'] = prefs.asset_bar_header_color
    draw_rect(header_props)


def draw_asset_bar_items(context, prefs, vis_props):
    am_props = context.scene.mt_am_props
    bar_props = context.scene.mt_bar_props
    assets = am_props['current_assets']
    bar_width = vis_props['width']
    image_width = vis_props['height']
    item_margin = bar_props.item_margin
    end_margin = bar_props.end_margin

    display_area = bar_width - (end_margin * 2)  # area in which items can be displayed
    item_width = image_width + (item_margin / 2)  # used for calculating how many thumbnails to show

    # set display properties asset images
    image_props = {
        'x': vis_props['x'] + end_margin + item_margin,
        'y': vis_props['y'],
        'width': image_width,
        'height': vis_props['height'],
        'transparency': prefs.asset_bar_item_image_transparency
    }

    # set display properties of hover and selected overlays
    hover_props = image_props.copy()
    selected_props = image_props.copy()

    hover_props['color'] = prefs.asset_bar_item_hover_color
    selected_props['color'] = prefs.asset_bar_item_selected_color
    selected_props['color'][3] = 0.5

    # calculate number of asset thumbnails to display
    num_thumbs = floor(display_area / item_width)
    # set last_visible_asset property
    last_visible_asset = bar_props.last_visible_asset = bar_props.first_visible_asset + num_thumbs

    i = bar_props.first_visible_asset
    while i < last_visible_asset:
        if i < len(assets):
            asset = assets[i]
            image_filename = asset['PreviewImagePath'].rsplit('\\', 1)[1]
            if image_filename in bpy.data.images.keys():
                image_props['image'] = bpy.data.images[image_filename]
            else:
                image_props['image'] = bar_props['missing_preview_image']

            draw_image(image_props)

            # increment image origin along x axis
            image_props['x'] = image_props['x'] + image_props['width'] + item_margin
        i += 1


def get_asset_bar_dimensions(context, prefs):
    """Return asset bar dimensions.

    Args:
        context (bpy.context): context

    Returns:
        dict{x: int, y: int, width: int, height: int}: asset bar dimensions
    """
    prefs = get_prefs()
    area = context.area  # the 3d viewport
    regions = area.regions  # the regions in the 3D viewport

    toolbar = None  # left toolbar
    ui = None  # N panel
    hud = None  # info panel that pops up when you use a tool

    for region in regions:
        if region.type == 'TOOLS':
            toolbar = region
        if region.type == 'UI':
            ui = region
        if region.type == 'HUD':
            hud = region

    # set the width of the asset bar to the width of the 3d viewport - 10px
    assetbar_width = area.width - 10

    # set the height of the asset bar to the height of each asset item
    assetbar_height = prefs.asset_item_dimensions

    # if N panel is showing resize asset bar so it doesn't overlap
    if ui.height >= area.height - assetbar_height:
        assetbar_width = assetbar_width - ui.width

    # if left toolbar is showing resize asset bar so it doesn't overlap
    if toolbar.height >= area.height - assetbar_height:
        assetbar_width = assetbar_width - toolbar.width

    origin_x = 5
    origin_y = 5

    # if HUD is showing resize bar and set origin
    if hud is not None:
        if hud.x > 0:
            assetbar_width = assetbar_width - hud.width - 5
            origin_x = origin_x + hud.width + 5

    # if left toolbar is showing set origin
    if toolbar.height >= area.height - assetbar_height:
        origin_x = origin_x + toolbar.width

    return {
        "x": origin_x,
        "y": origin_y,
        "width": assetbar_width,
        "height": assetbar_height}


class MT_OT_AM_Return_To_Parent(Operator):
    bl_idname = "view3d.mt_ret_to_parent"
    bl_label = "MakeTile return to parent"
    bl_description = "Move up a category level"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        props = context.scene.mt_am_props
        # get new parent category from current parent category
        new_parent_category = get_category(props['categories'], props.parent_category)

        # set child_cats to children of new_parent_category
        if new_parent_category:
            props['child_cats'] = new_parent_category['Children']
        else:
            props['child_cats'] = get_child_cats(props['categories'], new_parent_category)

        # set mt_am_props.active_category to old parent category
        context.scene.mt_am_props.active_category = props.parent_category
        # set mt_am_props.parent_category to new parent category
        context.scene.mt_am_props.parent_category = get_parent_cat_slug(props['categories'], props.parent_category)

        # reset asset index
        bar_props = context.scene.mt_bar_props
        bar_props.first_visible_asset = 0

        return {'FINISHED'}