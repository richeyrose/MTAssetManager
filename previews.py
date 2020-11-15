import os
import bpy
from .preferences import get_prefs


def render_material_preview(self, context, image_path, scene_path, scene_name, material, preview_obj_name):
    """Render a preview of the passed in material and saves it.

    Args:
        context (bpy.context): context
        image_path (str): Where to save preview image
        scene_path (str): Path to preview scene .blend file
        scene_name (str): name of preview scene to use
        material (bpy.types.material): material to render
        preview_obj_name (str): name of preview object to use for render
    """
    prefs = get_prefs()
    # link preview scene we're going to use for render
    if scene_name not in bpy.data.scenes:
        with bpy.data.libraries.load(scene_path) as (data_from, data_to):
            if scene_name not in data_from.scenes:
                self.report(
                    {'WARNING'},
                    "Preview scene " + scene_name + " not found. Preview render aborted")
                return
            else:
                data_to.scenes = [scene_name]

    preview_scene = bpy.data.scenes[scene_name]
    orig_scene = context.window.scene

    # switch scene
    context.window.scene = preview_scene

    # link preview obj to preview scene
    obj_path = os.path.join(
        prefs.default_assets_path,
        "previews",
        "objects",
        preview_obj_name + ".blend")

    if os.path.exists(obj_path):
        with bpy.data.libraries.load(obj_path) as (data_from, data_to):
            if preview_obj_name not in data_from.objects:
                self.report(
                    {'WARNING'},
                    "Preview object not found. Preview render aborted")
                return
            else:
                data_to.objects = [preview_obj_name]

    preview_obj = data_to.objects[0]
    context.collection.objects.link(preview_obj)

    # add material to object if not on it already
    if material.name not in preview_obj.data.materials:
        preview_obj.data.materials.append(material)
        material_index = list(preview_obj.material_slots.keys()).index(material.name)

        #TODO add material only to appropriate area
        # add material to entire object
        for poly in preview_obj.data.polygons:
            poly.material_index = material_index

    # reset preview object location
    preview_obj.location = (0, 0, 0)

    render = context.scene.render

    # save current render settings
    orig_engine = render.engine
    orig_film = render.film_transparent
    orig_res_x = render.resolution_x
    orig_res_y = render.resolution_y
    orig_filepath = render.filepath
    orig_feature_set = context.scene.cycles.feature_set
    orig_render_device = context.scene.cycles.device

    # new render settings
    render.engine = 'CYCLES'
    context.scene.cycles.feature_set = 'EXPERIMENTAL'
    if prefs.use_GPU is True:
        context.scene.cycles.device = 'GPU'

    render.film_transparent = True
    render.resolution_x = 512
    render.resolution_y = 512
    render.filepath = image_path

    # render image of mesh
    bpy.ops.render.render(write_still=True)

    # reset render engine
    render.engine = orig_engine
    render.film_transparent = orig_film
    render.resolution_x = orig_res_x
    render.resolution_y = orig_res_y
    render.filepath = orig_filepath
    context.scene.cycles.feature_set = orig_feature_set
    context.scene.cycles.device = orig_render_device

    # unlink preview object
    context.collection.objects.unlink(preview_obj)

    # switch back to original scene
    context.window.scene = orig_scene

    # load rendered image into scene
    bpy.data.images.load(image_path, check_existing=True)
    return


def render_object_preview(self, context, image_path, scene_path, scene_name, obj):
    """Render a preview of the passed in object and saves it.

    Args:
        context (bpy.context): context
        image_path (str): Where to save preview image
        scene_path (str): Path to preview scene .blend file
        scene_name (str): name of preview scene to use
        obj (bpy.types.Object): object to render
    """
    # link preview scene we're going to use for render
    if scene_name not in bpy.data.scenes:
        previews_path = os.path.join(
            scene_path)
        with bpy.data.libraries.load(previews_path) as (data_from, data_to):
            if scene_name not in data_from.scenes:
                self.report(
                    {'WARNING'},
                    "Preview scene " + scene_name + " not found. Preview render aborted")
                return
            data_to.scenes = [scene_name]

    preview_scene = bpy.data.scenes[scene_name]
    render_object = obj
    orig_scene = context.window.scene

    # copy object and apply all modifiers
    depsgraph = context.evaluated_depsgraph_get()
    obj_eval = render_object.evaluated_get(depsgraph)
    mesh_from_eval = bpy.data.meshes.new_from_object(obj_eval)
    obj_copy = bpy.data.objects.new("dupe", mesh_from_eval)

    # switch scene
    context.window.scene = preview_scene

    # link copy to scene
    context.collection.objects.link(obj_copy)

    # move object's origin to center
    ctx = {
        'object': obj_copy,
        'active_object': obj_copy,
        'selected_objects': [obj_copy]
    }

    bpy.ops.object.origin_set(ctx, type='ORIGIN_GEOMETRY', center='MEDIAN')

    # move object to world origin
    obj_copy.location = (0, 0, 0)

    # scale object so it fits in view of camera
    obj_bounds = obj_copy.matrix_world.to_quaternion() @ obj_copy.dimensions
    abs_bounds = list(map(abs, obj_bounds))
    ratio = 2 / max(abs_bounds)

    obj_copy.scale *= ratio

    # set render settings
    render = context.scene.render

    # save current render settings
    orig_engine = render.engine
    orig_film = render.film_transparent
    orig_res_x = render.resolution_x
    orig_res_y = render.resolution_y
    orig_filepath = render.filepath

    # new render settings
    render.engine = 'BLENDER_EEVEE'
    render.film_transparent = True
    render.resolution_x = 512
    render.resolution_y = 512
    render.filepath = image_path

    # render image of mesh
    bpy.ops.render.render(write_still=True)

    # reset render engine
    render.engine = orig_engine
    render.film_transparent = orig_film
    render.resolution_x = orig_res_x
    render.resolution_y = orig_res_y
    render.filepath = orig_filepath

    # unlink copy
    context.collection.objects.unlink(obj_copy)

    # switch back to original scene
    context.window.scene = orig_scene

    # load rendered image into scene
    bpy.data.images.load(image_path, check_existing=True)
    return
