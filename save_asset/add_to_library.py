"""Contains helper functions for adding assets to MakeTile library..."""
import os
from pathlib import Path
import bpy
from bpy.props import StringProperty, EnumProperty, PointerProperty
from ..utils import slugify, tagify, find_and_rename
from ..preferences import create_license_enums

class MT_Save_To_Library:
    """Mixin for save operators."""

    preview_img: StringProperty(
        name="Preview Image Name"
    )

    name: StringProperty(
        name="Name",
        default=""
    )

    desc: StringProperty(
        name="Description",
        default=""
    )

    author: StringProperty(
        name="Author",
        default=""
    )

    license: EnumProperty(
        items=create_license_enums,
        name="License",
        description="License for asset use")

    tags: StringProperty(
        name="Tags",
        description="Comma seperated list",
        default=""
    )

    def draw_save_props_menu(self, context):
        """Draw a pop up menu for entering properties.

        Args:
            context (bpy.Context): context
        """
        layout = self.layout
        layout.prop(self, 'desc')
        layout.prop(self, 'author')
        layout.prop(self, 'license')
        layout.prop(self, 'tags')


    def add_asset_to_library(self, asset, asset_desc, preview_img = None):
        """Add the passed in asset to the asset library.

        Args:
            context (bpy.Context): context
            asset (bpy.types.object, material, collection): the asset to add
            asset_type (enum in {OBJECTS, COLLECTIONS, MATERIALS}): asset type

        Returns:
            dict: asset_desc
        """
        imagepath = asset_desc['imagepath']
        assetpath = os.path.join(asset_desc['filepath'], asset_desc['filename'])

        if preview_img:
            # save asset preview image to asset
            asset.mt_preview_img = preview_img
            preview_img.pack()


        # save asset in individual file
        if not os.path.exists(asset_desc['filepath']):
            os.makedirs(asset_desc['filepath'])

        ids = {asset}

        if preview_img:
            ids.add(preview_img)

        bpy.data.libraries.write(
            assetpath,
            ids,
            fake_user=True)

        # # delete external image
        if os.path.exists(imagepath):
            os.remove(imagepath)

        self.report({'INFO'}, asset.name + " added to Library.")

        return asset_desc


    def construct_asset_description(self, props, asset, save_path=None, **kwargs):
        if not save_path:
            asset_save_path = props.current_path
        else:
            asset_save_path = save_path

        # create a unique (within this directory) slug for our file
        slug = slugify(asset.name)

        # list of .blend file stem names in asset_save_path:
        try:
            blends = [f for f in os.listdir(asset_save_path) if os.path.isfile(os.path.join(asset_save_path, f)) and f.endswith(".blend")]
            stems = [Path(blend).stem for blend in blends]
        except FileNotFoundError:
            os.makedirs(asset_save_path)
            stems=[]

        # check if slug already exists and increment and rename if not.
        if stems:
            slug = find_and_rename(slug, stems)

        # construct dict for saving to .json cache file
        asset_desc = {
            "slug": slug,
            "filename": slug + '.blend',
            "filepath": asset_save_path,
            "imagepath": os.path.join(asset_save_path, slug + '.png')}

        for key, value in kwargs.items():
            asset_desc[key] = value

        return asset_desc


    def mark_as_asset(self, asset, asset_desc, tags):
        """Save asset as blender asset for blender's internal asset browser.

        Args:
            asset (ID data block): Asset
            asset_desc (dict): asset description
            tags (list[str]): list of tags
        """

        # Clear any existing asset data and then mark as asset
        asset.asset_clear()
        asset.asset_mark()
        asset_data = asset.asset_data

        # set asset preview
        ctx = {'id': asset}
        imagepath = asset_desc['imagepath']
        if os.path.isfile(imagepath):
            bpy.ops.ed.lib_id_load_custom_preview(ctx, filepath=imagepath)

        # set asset description
        asset_data.description = asset_desc['desc']

        # set asset tags
        for tag in tags:
            if tag:
                asset_data.tags.new(tag, skip_if_exists=True)

        # set author
        asset_data.author = asset_desc['author']

        # set custom license prop
        asset_data.mt_license = asset_desc['license']
