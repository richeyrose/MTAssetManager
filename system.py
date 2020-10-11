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
import bpy


def abspath(path):
    """Return the absolute path."""
    return os.path.abspath(bpy.path.abspath(path))


def makedir(pathstring):
    """Make directory if it doesn't already exist and return it."""
    if not os.path.exists(pathstring):
        os.makedirs(pathstring)
    return pathstring


def get_addon_path():
    """return addon path."""
    return os.path.dirname(os.path.realpath(__file__))


def get_addon_name():
    """return file path name of calling file."""
    return os.path.basename(get_addon_path())