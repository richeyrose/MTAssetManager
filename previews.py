import os
import bpy
from .preferences import get_prefs



def render_object_preview(self, context, imagepath, scene_path, scene_name, obj):
    """Render a preview of the passed in object and saves it."""
    # link preview scene we're going to use for render
    if scene_name not in bpy.data.scenes:
        previews_path = os.path.join(
            scene_path)
        with bpy.data.libraries.load(previews_path) as (data_from, data_to):
            if scene_name not in data_from.scenes:
                self.report({'WARNING'}, "Preview scene " + scene_name + " not found. Preview render aborted")
                return None
            else:
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
    render.filepath = imagepath

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
    bpy.data.images.load(imagepath, check_existing=True)
