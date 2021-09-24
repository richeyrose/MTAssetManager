import math
import bpy
from bpy.types import PropertyGroup
from bpy.props import StringProperty, BoolProperty, EnumProperty, PointerProperty, CollectionProperty
from .preferences import get_prefs



class MT_PT_AM_Props(PropertyGroup):
    def update_library_path(self, context):
        prefs = get_prefs()
        self.current_path = self.library_path
        prefs.library_path = self.library_path

    assets_updated: BoolProperty(
        name="Assets Updated",
        default=False,
        description="Set to true when you add, remove or update an asset"
    )

    current_path: StringProperty(
        name="Current Path",
        subtype='DIR_PATH',
        description="Path to the current asset folder."
    )

    parent_path: StringProperty(
        name="Parent Path",
        subtype='DIR_PATH',
        description="Path to the parent of the current asset folder."
    )

    library_path: StringProperty(
        name="Library Path",
        subtype='DIR_PATH',
        description="Library Path.",
        update=update_library_path
    )

    cut: bpy.props.BoolProperty(
        name="Cut",
        default=False,
        description="Whether we are in asset cut mode."
    )

    # _categories = []
    # _child_cats = []
    # _objects = []
    # _materials = []
    # _collections = []
    # _current_asset_desc = None
    _asset_bar = []
    # _copied_assets = None
    # _active_category = None

    # @property
    # def active_category(self):
    #     return MT_PT_AM_Props._active_category

    # @active_category.setter
    # def active_category(self, value):
    #     MT_PT_AM_Props._active_category = value

    # @property
    # def copied_assets(self):
    #     return MT_PT_AM_Props._copied_assets

    # @copied_assets.setter
    # def copied_assets(self, value):
    #     MT_PT_AM_Props._copied_assets = value

    @property
    def asset_bar(self):
        return MT_PT_AM_Props._asset_bar

    @asset_bar.setter
    def asset_bar(self, value):
        MT_PT_AM_Props._asset_bar = value

    # @property
    # def current_asset_desc(self):
    #     return MT_PT_AM_Props._current_asset_desc

    # @current_asset_desc.setter
    # def current_asset_desc(self, value):
    #     MT_PT_AM_Props._current_asset_desc = value

    # @property
    # def categories(self):
    #     return MT_PT_AM_Props._categories

    # @categories.setter
    # def categories(self, value):
    #     MT_PT_AM_Props._categories = value

    # @property
    # def child_cats(self):
    #     return MT_PT_AM_Props._child_cats

    # @child_cats.setter
    # def child_cats(self, value):
    #     MT_PT_AM_Props._child_cats = value

    # @property
    # def objects(self):
    #     return MT_PT_AM_Props._objects

    # @objects.setter
    # def objects(self, value):
    #     MT_PT_AM_Props._objects = value

    # @property
    # def materials(self):
    #     return MT_PT_AM_Props._materials

    # @materials.setter
    # def materials(self, value):
    #     MT_PT_AM_Props._materials = value

    # @property
    # def collections(self):
    #     return MT_PT_AM_Props._collections

    # @collections.setter
    # def collections(self, value):
    #     MT_PT_AM_Props._collections = value


class MT_PT_AM_Bar_Props(PropertyGroup):
    visible: bpy.props.BoolProperty(
        name="Visible",
        description="Whether asset bar is visible.",
        default=False
    )

    item_margin: bpy.props.IntProperty(
        name="Item Margin",
        default=5,
        description="Margin around each item in asset bar"
    )

    end_margin: bpy.props.IntProperty(
        name="End Margin",
        default=25,
        description="Marging to leave at end of asset bar for forward and back buttons"
    )

    first_visible_asset: bpy.props.IntProperty(
        name="First visible asset",
        description="The index of the first asset that is visible in the asset bar",
        default=0
    )

    last_visible_asset: bpy.props.IntProperty(
        name="Last Visible asset",
        description="Index of the last asset that is visible in the asset bar",
        default=0
    )


class MT_PT_AM_Object_Spawn_Props(PropertyGroup):
    randomize_rotation: bpy.props.BoolProperty(
        name='Randomize Rotation',
        description="randomize rotation at placement",
        default=False)

    randomize_rotation_amount: bpy.props.FloatProperty(
        name="Randomization Max Angle",
        description="maximum angle for random rotation",
        default=math.pi / 36,
        min=0,
        max=2 * math.pi,
        subtype='ANGLE')

    offset_rotation_amount: bpy.props.FloatProperty(
        name="Offset Rotation",
        description="offset rotation, hidden prop",
        default=0,
        min=0,
        max=360,
        subtype='ANGLE')

    offset_rotation_step: bpy.props.FloatProperty(
        name="Offset Rotation Step",
        description="offset rotation, hidden prop",
        default=math.pi / 2,
        min=0,
        max=180,
        subtype='ANGLE')


def register():
    bpy.types.Scene.mt_am_props = bpy.props.PointerProperty(
        type=MT_PT_AM_Props
    )

    bpy.types.Scene.mt_bar_props = bpy.props.PointerProperty(
        type=MT_PT_AM_Bar_Props
    )

    bpy.types.Scene.mt_am_spawn_props = bpy.props.PointerProperty(
        type=MT_PT_AM_Object_Spawn_Props
    )

    # Custom asset properties
    bpy.types.AssetMetaData.mt_license = EnumProperty(
        items=[
            ("ARR", "All Rights Reserved", ""),
            ("CCBY", "Attribution (CC BY)", ""),
            ("CCBYSA", "Attribution-ShareAlike (CC BY-SA)", ""),
            ("CCBYND", "Attribution-NoDerivs (CC BY-ND)", ""),
            ("CCBYNC", "Attribution-NonCommercial (CC BY-NC)", ""),
            ("CCBYNCSA", "Attribution-NonCommercial-ShareAlike (CC BY-NC-SA)", ""),
            ("CCBYNCND", "Attribution-NonCommercial-NoDerivs (CC BY-NC-ND)", "")],
        name="License",
        description="License for asset use",
        default="ARR")

    bpy.types.AssetMetaData.mt_author = StringProperty(
        name="Author",
        description="Creator of the asset",
        default="")

    bpy.types.AssetMetaData.mt_URI = StringProperty(
        name="URI",
        default="")

    bpy.types.Object.mt_preview_img = PointerProperty(
        name="Preview Image",
        type=bpy.types.Image,
        description="Preview Image to use in MT Asset Browser."
    )

    bpy.types.Collection.mt_preview_img = PointerProperty(
        name="Preview Image",
        type=bpy.types.Image,
        description="Preview Image to use in MT Asset Browser."
    )

    bpy.types.Material.mt_preview_img = PointerProperty(
        name="Preview Image",
        type=bpy.types.Image,
        description="Preview Image to use in MT Asset Browser."
    )

def unregister():
    del bpy.types.Material.mt_preview_img
    del bpy.types.Collection.mt_preview_img
    del bpy.types.Object.mt_preview_img
    del bpy.types.AssetMetaData.mt_URI
    del bpy.types.AssetMetaData.mt_author
    del bpy.types.AssetMetaData.mt_license
    del bpy.types.Scene.mt_am_spawn_props
    del bpy.types.Scene.mt_bar_props
    del bpy.types.Scene.mt_am_props