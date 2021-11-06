import os
import shutil
import bpy
import json
from bpy.props import StringProperty, BoolProperty, PointerProperty
from ..preferences import get_prefs
from ..system import makedir, abspath

class MT_OT_Asset_Converter(bpy.types.Operator):
    bl_idname = "file.mt_asset_converter"
    bl_label = "Convert Old Assets"
    bl_description = "Converts old MakeTile assets to the new asset system."

    old_assets_path: StringProperty(
        name="Old Assets Path",
        subtype="DIR_PATH",
        description="Path to the folder containing your data folder."
    )


    def execute(self, context):
        prefs = get_prefs()
        src_path = self.old_assets_path
        data_path = os.path.join(src_path, "data")
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
            old_assets_path = os.path.join(src_path, "OldAssets")
            try:
                os.mkdir(old_assets_path)
            except FileExistsError as err:
                self.report({'INFO'}, str(err))
            except OSError as err:
                self.report({'INFO'}, str(err))
                return {'CANCELLED'}


        # for each description:
            # append the asset
            # save it as an asset using the new operators into a file in a subfolder based on the category in the asset desc
            # move the old asset file and preview into an "Old Assets" folder
            # update the asset description in the .json file.
            for desc in descs:
                if desc['Type'] == 'OBJECTS':
                    # append asset to file
                    try:
                        with bpy.data.libraries.load(desc["FilePath"]) as (data_from, data_to):
                            data_to.objects = [desc['Slug']]
                        asset = data_to.objects[0]
                    except OSError as err:
                        self.report({'INFO'}, str(err))
                        continue

                    try:
                        preview_img = bpy.data.images.load(desc['PreviewImagePath'])
                    except RuntimeError as err:
                        self.report({'INFO'}, str(err))
                        preview_img = None

                    ctx = context.copy()
                    ctx['active_object'] = asset
                    ctx['selected_objects'] = [asset]
                    ctx['selected_editable_objects'] = [asset]

                    bpy.ops.object.add_selected_objects_to_library(
                        ctx,
                        dirpath=os.path.join(assets_path, desc['Category']),
                        preview_img = preview_img.name,
                        name=desc['Name'],
                        desc=desc['Description'],
                        author=desc['Author'],
                        tags=",".join(desc['Tags']))

                    # clean up current file
                    bpy.data.objects.remove(asset)
                    bpy.data.images.remove(preview_img)

                    # # move old asset file to Old Assets Folder
                    # try:
                    #     shutil.move(desc["FilePath"], old_assets_path)
                    # except OSError as err:
                    #     self.report({'INFO'}, str(err))
                    return {'FINISHED'} # REMOVE ME


                elif desc['Type'] == 'MATERIALS':
                    pass
                elif desc['Type'] == 'COLLECTIONS':
                    pass



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
