import os
import shutil
import bpy
import json
from bpy.props import StringProperty, BoolProperty, PointerProperty
from ..enums import default_licenses
from ..preferences import get_prefs
from ..system import makedir, abspath
from ..save_asset.add_to_library import MT_Save_To_Library

class MT_OT_Asset_Converter(bpy.types.Operator, MT_Save_To_Library):
    bl_idname = "file.mt_asset_converter"
    bl_label = "Convert Old Assets"
    bl_description = "Converts old MakeTile assets to the new asset system."

    data_path: StringProperty(
        name="Data Path",
        subtype="DIR_PATH",
        description="Path to your 'data' folder"
    )

    target_path: StringProperty(
        name="Target Path",
        subtype="DIR_PATH",
        description="Directory to save converted assets in."
    )

    archive_path: StringProperty(
        name="Archive Path",
        subtype="DIR_PATH",
        description="Directory to archive old assets in. Leave blank to leave in place."
    )

    def execute(self, context):
        prefs = get_prefs()
        props = context.scene.mt_am_props
        data_path = self.data_path
        user_assets_path = prefs.user_assets_path

        # create a list of all descriptions
        descs = []
        filenames = ['collections.json', 'materials.json', 'objects.json']

        for filename in filenames:
            filepath = os.path.join(data_path, filename)
            if os.path.exists(filepath):
                with open(filepath) as json_file:
                    descs.extend(json.load(json_file))

        if descs:
            # create directory to save converted assets in if user hasn't specified one.
            try:
                if not self.target_path:
                    os.makedirs(os.path.join(user_assets_path, "ConvertedAssets"), exist_ok=True)
                    self.target_path = os.path.join(user_assets_path, "ConvertedAssets")
            except OSError as err:
                self.report({'INFO'}, str(err))
                return {'CANCELLED'}

            for desc in descs:
                # append the asset to the current file
                asset_type = str(desc['Type']).lower()
                try:
                    with bpy.data.libraries.load(desc["FilePath"]) as (data_from, data_to):
                        setattr(data_to, asset_type, [desc['Slug']])
                    asset = getattr(data_to, asset_type)[0]
                    asset.name = desc['Name']
                except OSError as err:
                    self.report({'INFO'}, str(err))
                    continue
                # append the preview image tot he current file
                try:
                    preview_img = bpy.data.images.load(desc['PreviewImagePath'])
                except RuntimeError as err:
                    self.report({'INFO'}, str(err))
                    preview_img = None

                # Check if the license in the asset metadata exists and create a new one if not
                asset_license = desc['License']
                if asset_license in [license[1] for license in default_licenses]:
                    license_id = [license[0] for license in default_licenses if license[1] == asset_license][0]
                elif asset_license in [license['name'] for license in prefs.user_licenses]:
                    license_id = asset_license
                else:
                    new_license = prefs.user_licenses.add()
                    new_license.name = asset_license
                    license_id = asset_license

                kwargs = {
                    "desc": desc['Description'],
                    "author": desc['Author'],
                    "tags": desc['Tags'],
                    "license": license_id}

                asset_desc = self.construct_asset_description(
                    props,
                    asset,
                    save_path=os.path.join(self.target_path, desc['Category']),
                    **kwargs)

                asset_desc['imagepath'] = desc['PreviewImagePath']

                # save asset data for Blender asset browser
                self.mark_as_asset(asset, asset_desc, desc['Tags'])

                self.add_asset_to_library(
                    asset,
                    asset_desc,
                    preview_img,
                    del_preview=False)

                # clean up current file
                getattr(bpy.data, asset_type).remove(asset)
                if preview_img:
                    bpy.data.images.remove(preview_img)

                # move old file to archive
                if self.archive_path:
                    try:
                        shutil.move(desc["FilePath"], self.archive_path)
                    except OSError as err:
                        self.report({'INFO'}, str(err))
        #TODO live scan of folder to update bar
        props.assets_updated = True
        return {'FINISHED'}

    def load_categories(assets_path):
        """Load categories from .json file."""
        categories = []
        json_path = os.path.join(
            assets_path,
            "data",
            "categories.json"
        )

        if os.path.exists(json_path):
            with open(json_path) as json_file:
                categories = json.load(json_file)

        return categories



