import bpy
import numpy as np
import redis
import random
import queue
import time
import threading
import json
import ast


print("Starting script")
ducers_height = 0.14
# Clear existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define the dimensions of the array
sonic_surface = False
n_transducers = 10 if sonic_surface else 16
spacing = 10/1000 if sonic_surface else 11.2/1000 # Adjust this to control the spacing between cylinders

# Create a cylinder template

bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=5/1000, depth=7/1000, location=(0, 0, ducers_height))
cylinder_template = bpy.context.object

# Create the array of cylinders
for row in range(n_transducers):
    for col in range(n_transducers):
        # Create a new cylinder by duplicating the template
        new_cylinder = cylinder_template.copy()
        bpy.context.collection.objects.link(new_cylinder)
        new_cylinder.location.x = col * spacing
        new_cylinder.location.y = row * spacing

# Select and link the template to the scene
bpy.context.collection.objects.unlink(cylinder_template)
bpy.data.objects.remove(cylinder_template)
#bpy.ops.mesh.primitive_uv_sphere_add(radius=0.01, location=(0, 0, 1))
#ball = bpy.context.object
#ball.name = 'sphere'


# This function can safely be called in another thread.
# The function will be executed when the timer runs the next time.
location_queue = queue.Queue()

r = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)
# Create a pubsub instance and subscribe to the 'positions' channel
pubsub = r.pubsub()
pubsub.subscribe('positions')
#context = zmq.Context()
#socket = context.socket(zmq.SUB)
#socket.connect("tcp://localhost:5498")

# Subscribe to all messages
#socket.setsockopt_string(zmq.SUBSCRIBE, '')
max_locations = 0
def read_to_queue():
    for message in pubsub.listen():
        if message['type'] == 'message':
            try:
                positions_list = json.loads(message['data'])
            except Exception as e:
                continue
            location_queue.put(positions_list)


def use_locations_from_queue():
    while not location_queue.empty():
        global max_locations
        locations = location_queue.get()
        num_locations = len(locations)
        max_locations = max(max_locations, num_locations)
        for index, location in enumerate(locations):

            if not sonic_surface:
                location = [17.8/100- location[0], location[1], location[2]]
            else:
                location = [location[0], location[1], location[2]]
            name = "sphere_" + str(index)
            if obj:= bpy.context.scene.objects.get(name):
                obj.location = location
                obj.hide_set(False)
            else:
                bpy.ops.mesh.primitive_uv_sphere_add(radius=0.005, location=location)
                ball = bpy.context.object
                ball.name = 'sphere_' + str(index)
        for index in range(num_locations, max_locations):
            name = "sphere_" + str(index)
            if obj:= bpy.context.scene.objects.get(name):
                obj.hide_set(True)
        
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.update()
    return 0.01



bpy.app.timers.register(use_locations_from_queue)
my_thread = threading.Thread(target=read_to_queue, daemon=True)
my_thread.start()
