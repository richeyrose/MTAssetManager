# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import os
import re
import shutil
import bpy
from .system import makedir, abspath, get_addon_path, get_addon_name
from bpy.types import PropertyGroup, Operator
from bpy.props import (
    StringProperty,
    FloatVectorProperty,
    FloatProperty,
    IntProperty,
    BoolProperty,
    CollectionProperty,
    EnumProperty)

# class MT_Library(PropertyGroup):
#     name: StringProperty(
#         name="Name",
#         description="Library Name"
#     )

#     path: StringProperty(
#         name="Path",
#         subtype='DIR_PATH',
#         description="Path to Library."
#     )

default_licenses=[
    ("ARR", "All Rights Reserved", ""),
    ("CCBY", "Attribution (CC BY)", ""),
    ("CCBYSA", "Attribution-ShareAlike (CC BY-SA)", ""),
    ("CCBYND", "Attribution-NoDerivs (CC BY-ND)", ""),
    ("CCBYNC", "Attribution-NonCommercial (CC BY-NC)", ""),
    ("CCBYNCSA", "Attribution-NonCommercial-ShareAlike (CC BY-NC-SA)", ""),
    ("CCBYNCND", "Attribution-NonCommercial-NoDerivs (CC BY-NC-ND)", "")]

class MT_User_Licenses(PropertyGroup):
    name: StringProperty(
        name="Name",
        description="License Name"
    )
    description: StringProperty(
        name="Description"
    )

class MT_AM_Prefs(bpy.types.AddonPreferences):
    bl_idname = __package__
    addon_path = get_addon_path()
    user_path = os.path.expanduser('~')
    export_path = os.path.join(user_path, 'MakeTile')
    user_assets_path = os.path.join(user_path, 'MakeTile')
    default_assets_path = os.path.join(addon_path, "assets")

    def create_licenses_enums(self, context):
        enum_items = []
        if context is None:
            return enum_items

        # default licenses
        enum_items=default_licenses.copy()

        # User licenses
        user_licenses = self.user_licenses
        for li in user_licenses:
            enum = (li.name, li.name, li.description)
            enum_items.append(enum)
        return enum_items
    # def update_user_assetspath(self, context):
    #     """Update the user assets path."""
    #     new_path = makedir(abspath(self.user_assets_path))
    #     old_path = abspath(self.old_path)

    #     if new_path != old_path:
    #         print(" » Copying asset libraries from %s to %s" % (old_path, new_path))

    #         libs = sorted([f for f in os.listdir(old_path) if os.path.isdir(os.path.join(old_path, f))])

    #         for lib in libs:
    #             src = os.path.join(old_path, lib)
    #             dest = os.path.join(new_path, lib)

    #             if not os.path.exists(dest):
    #                 print(" » %s" % (lib))
    #                 shutil.copytree(src, dest)

    #         # set the new old_path
    #         self.old_path = new_path

    #         # reload assets
    #         reload_asset_libraries()

    default_assets_path: StringProperty(
        name="Default Asset Libraries",
        description="Path to Default Asset Libraries",
        subtype='DIR_PATH',
        default=default_assets_path
    )

    user_assets_path: StringProperty(
        name="User Asset Library",
        subtype='DIR_PATH',
        description="Path to User Asset Library",
        default=user_assets_path,
    )

    library_path: StringProperty(
        name="Current Library",
        default=user_assets_path,
        subtype='DIR_PATH')

    old_path: StringProperty(
        name="Old Path",
        subtype='DIR_PATH',
        default=os.path.join(user_path, "MakeTile")
    )

    asset_bar_bg_color: FloatVectorProperty(
        name="Asset Bar Color",
        size=4,
        subtype='COLOR',
        default=bpy.context.preferences.themes['Default'].preferences.space.panelcolors.back
    )

    asset_bar_header_color: FloatVectorProperty(
        name="Asset Bar Header Color",
        size=4,
        subtype='COLOR',
        default=bpy.context.preferences.themes['Default'].user_interface.wcol_regular.item
    )

    asset_bar_header_height: IntProperty(
        name="Asset Bar Header Height",
        default=32
    )

    asset_bar_text_color: FloatVectorProperty(
        name="Asset Bar Text Color",
        size=3,
        subtype='COLOR',
        default=bpy.context.preferences.themes['Default'].user_interface.wcol_regular.text
    )

    asset_bar_text_selected_color: FloatVectorProperty(
        name="Asset Bar Text Selected Color",
        size=3,
        default=bpy.context.preferences.themes['Default'].user_interface.wcol_regular.text_sel
    )

    asset_bar_item_color: FloatVectorProperty(
        name="Asset Bar Item Color",
        size=4,
        default=bpy.context.preferences.themes['Default'].user_interface.wcol_regular.item
    )

    asset_bar_item_hover_color: FloatVectorProperty(
        name="Asset Bar Item Hover Color",
        size=4,
        default=(1, 1, 1, 0.2)
    )

    asset_bar_item_image_transparency: FloatProperty(
        name="Asset Bar Item Transparency",
        default=1,
        min=0,
        max=1
    )

    asset_bar_inner_color: FloatVectorProperty(
        name="Asset Bar Inner Color",
        size=4,
        default=bpy.context.preferences.themes['Default'].user_interface.wcol_regular.inner
    )

    asset_bar_item_selected_color: FloatVectorProperty(
        name="Asset Bar Item Selected Color",
        size=4,
        default=bpy.context.preferences.themes['Default'].user_interface.wcol_regular.inner_sel
    )

    asset_bar_outline_color: FloatVectorProperty(
        name="Asset Bar Outline Color",
        size=3,
        default=bpy.context.preferences.themes['Default'].user_interface.wcol_regular.outline
    )

    asset_bar_nav_button_color: FloatVectorProperty(
        name="Asset Bar Nav Button Color",
        size=4,
        default=bpy.context.preferences.themes['Default'].user_interface.wcol_regular.item
    )

    asset_bar_nav_button_width: IntProperty(
        name="Asset Bar Nav Button Width",
        default=25,
        min=10
    )

    asset_bar_rows: IntProperty(
        name="Asset Bar Rows",
        description="How many rows of assets to display",
        default=1
    )

    asset_bar_roundness: FloatProperty(
        name="Asset bar roundness",
        min=0,
        max=1,
        default=bpy.context.preferences.themes['Default'].user_interface.wcol_regular.roundness
    )

    asset_item_dimensions: IntProperty(
        name="Asset Item Size",
        default=128,
        min=32,
        max=512
    )

    preview_scene: StringProperty(
        name="Preview Scene",
        default="Bright",
        description="Scene to use for rendering previews"
    )

    preview_render_size: IntProperty(
        name="Preview Size",
        default=512,
        min=32
    )

    use_GPU: BoolProperty(
        name="Use GPU",
        default=True,
        description="Use GPU for preview renders"
    )

    old_assets_path: StringProperty(
        name="Old Assets Path",
        description="Path where old style MakeTile assets are stored",
        subtype="DIR_PATH"
    )

    user_licenses: CollectionProperty(
        name="User Licenses",
        type=MT_User_Licenses
    )

    licenses: EnumProperty(
        name="Licenses",
        items=create_licenses_enums
    )

    def draw(self, context):
        props = context.scene.mt_am_props
        layout = self.layout
        layout.prop(self, 'user_assets_path')
        box = layout.box()
        box.prop(self, 'old_assets_path')
        op = box.operator('file.mt_asset_converter')
        op.data_path = self.old_assets_path

        layout.label(text="User Licenses:")

        # Draw list of user licenses
        layout.prop(self, 'user_licenses')
        for li in self.user_licenses:
            row = layout.row()
            row.prop(li, 'name')
            row.prop(li, 'description')
            op = row.operator('addons.mt_remove_user_license', text="", icon='REMOVE')
            op.name = li.name

        layout.label(text="Add New License:")
        row = layout.row()
        row.prop(props, 'new_license_name')
        row.prop(props, 'new_license_desc')
        op = layout.operator('addons.mt_add_user_license')
        op.name=props.new_license_name
        op.description=props.new_license_desc
        layout.prop(self, 'licenses')

class MT_AM_OT_Remove_User_License(Operator):
    bl_idname="addons.mt_remove_user_license"
    bl_label = "Remove License"

    name: StringProperty(
        name="Name"
    )

    def execute(self, context):
        prefs=get_prefs()
        prefs.user_licenses.remove(prefs.user_licenses.find(self.name))

        return{'FINISHED'}

class MT_AM_OT_Add_User_License(Operator):
    bl_idname = "addons.mt_add_user_license"
    bl_label = "Add License"

    name: StringProperty(
        name="Name",
        description="Characters other than Aa-Zz0-9()_- will be stripped"
    )

    description: StringProperty(
        name="Description"
    )

    @classmethod
    def poll(cls, context):
        return context.scene.mt_am_props.new_license_name

    def execute(self, context):
        prefs = get_prefs()
        props = context.scene.mt_am_props
        user_licenses = prefs.user_licenses
        name = re.sub(r'[^a-zA-Z0-9()-_ ]','', self.name)

        if name not in user_licenses.keys():
            new_license = user_licenses.add()
            new_license.name = name
            new_license.description = self.description

            # clear text boxes
            props.new_license_name=''
            props.new_license_desc = ''
            return{'FINISHED'}

        self.report(
            {'INFO'},
            "A license with this name already exists. Please rename license.")
        return{'CANCELLED'}

# TODO: Stub - reload_asset_libraries
def reload_asset_libraries():
    pass

def get_prefs():
    """returns MakeTile preferences"""
    return bpy.context.preferences.addons[get_addon_name()].preferences
