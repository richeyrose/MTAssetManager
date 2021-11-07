import os
import shutil
import bpy
import json
from bpy.props import StringProperty, BoolProperty, PointerProperty
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
            # create subfolder in new_path where we will move our assets to
            try:
                os.mkdir(os.path.join(user_assets_path, "ConvertedAssets"))
            except FileExistsError as err:
                self.report({'INFO'}, str(err))
            except OSError as err:
                self.report({'INFO'}, str(err))
                return {'CANCELLED'}

            assets_path = os.path.join(user_assets_path, "ConvertedAssets")

            # create subfolder where we'll move our old asset file to once done
            old_assets_path = os.path.join(user_assets_path, "OldAssets")
            try:
                os.mkdir(old_assets_path)
            except FileExistsError as err:
                self.report({'INFO'}, str(err))
            except OSError as err:
                self.report({'INFO'}, str(err))
                return {'CANCELLED'}

        #TODO Rename asset using pretty name
        # for each description:
            # append the asset
            # save it as an asset using the new operators into a file in a subfolder based on the category in the asset desc
            # move the old asset file and preview into an "Old Assets" folder
            for desc in descs:
                asset_type = str(desc['Type']).lower()
                try:
                    with bpy.data.libraries.load(desc["FilePath"]) as (data_from, data_to):
                        setattr(data_to, asset_type, [desc['Slug']])
                    asset = getattr(data_to, asset_type)[0]
                    asset.name = desc['Name']
                except OSError as err:
                    self.report({'INFO'}, str(err))
                    continue
                try:
                    preview_img = bpy.data.images.load(desc['PreviewImagePath'])
                except RuntimeError as err:
                    self.report({'INFO'}, str(err))
                    preview_img = None


                kwargs = {
                    "desc": desc['Description'],
                    "author": desc['Author'],
                    "tags": desc['Tags'],
                    "license":'ARR'}

                asset_desc = self.construct_asset_description(
                    props,
                    asset,
                    save_path=os.path.join(assets_path, desc['Category']),
                    **kwargs)

                # save asset data for Blender asset browser
                self.mark_as_asset(asset, asset_desc, desc['Tags'])

                self.add_asset_to_library(
                    asset,
                    asset_desc,
                    preview_img)

                # clean up current file
                getattr(bpy.data, asset_type).remove(asset)
                bpy.data.images.remove(preview_img)


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



