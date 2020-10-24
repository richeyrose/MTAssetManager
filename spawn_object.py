import bpy
from .raycast import mouse_raycast


def spawn_object(self, context, x, y):
    coord = (x, y)
    has_hit, snapped_location, snapped_normal, snapped_rotation, face_index, obj, matrix = mouse_raycast(context, coord)

    print(has_hit)
