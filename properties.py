import math
import os
import bpy
from bpy.types import PropertyGroup
from bpy.props import StringProperty, BoolProperty, EnumProperty, PointerProperty, CollectionProperty
from .preferences import get_prefs

class MT_PT_AM_Props(PropertyGroup):
    def library_enum_items(self, context):
        enum_items = []

        if context is None:
            return enum_items

        libs = context.preferences.filepaths.asset_libraries

        for lib in libs:
            if os.path.isdir(lib.path):
                enum_items.append((lib.name, lib.name, ""))

        return enum_items

    def update_library_path(self, context):
        prefs = get_prefs()
        self.current_path = self.library_path
        prefs.library_path = self.library_path

    def update_libraries_enum(self, context):
        self.library_path = self.current_path = context.preferences.filepaths.asset_libraries[self.libraries].path

    def update_assets(self, context):
        props = context.scene.mt_am_props
        props.assets_updated = True

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

    libraries: EnumProperty(
        name="Libraries",
        items=library_enum_items,
        update=update_libraries_enum
    )

    asset_sort_by: EnumProperty(
        name="Sort By",
        items=[
            ("ALPHABETICAL", "Alphabetical", "Sort Alphabetically"),
            ("MODIFIED", "Modified", "Sort by last Modified")],
        description="Property to sort by",
        default="ALPHABETICAL",
        update=update_assets
    )

    asset_reverse_sort: BoolProperty(
        name="Reverse",
        default=False,
        description="Reverse Sort",
        update=update_assets
    )

    asset_filter: EnumProperty(
        name="Filter",
        items=[
            ("OBJECT", "Object", "Filter by Object"),
            ("MATERIAL", "Material", "Filter by Material"),
            ("COLLECTION", "Collection", "Filter by Collection"),
            ("NONE", "None", "Remove Filter")],
        default="NONE",
        update=update_assets
    )

    cut: bpy.props.BoolProperty(
        name="Cut",
        default=False,
        description="Whether we are in asset cut mode."
    )

    _asset_bar = []

    @property
    def asset_bar(self):
        return MT_PT_AM_Props._asset_bar

    @asset_bar.setter
    def asset_bar(self, value):
        MT_PT_AM_Props._asset_bar = value


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

    object_icon: PointerProperty(
        type=bpy.types.Image,
        name="Object Icon",
        description="Icon to display on objects in asset bar."
    )

    collection_icon: PointerProperty(
        type=bpy.types.Image,
        name="Collection Icon",
        description="Icon to display on collections in asset bar."
    )

    material_icon: PointerProperty(
        type=bpy.types.Image,
        name="Material Icon",
        description="Icon to display on materials in asset bar."
    )

    missing_preview_icon: PointerProperty(
        type=bpy.types.Image,
        name="Missing Preview Icon",
        description="Icon to display when there is a missing preview image."
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
    del bpy.types.AssetMetaData.mt_license
    del bpy.types.Scene.mt_am_spawn_props
    del bpy.types.Scene.mt_bar_props
    del bpy.types.Scene.mt_am_props