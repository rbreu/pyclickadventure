#!/usr/bin/env python

import os.path, sys
from os.path import join
import pygame
from pygame.locals import QUIT

sys.path.append(join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
import pyclickadventure as pyv


pyv.init((720, 576), 'My Awesome Game',
         #background_music='bach-menuett.mp3',
         icon=join('img', 'icon.png'))


# Rooms
village = pyv.Room(join('img', 'village.png'))
house = pyv.Room(join('img', 'house.png'),
                 exit_left=(village, 'Go outside'))

# Items -- house

frame_empty = pyv.Item(
    image=join('img', 'frame_empty.png'),
    topleft=(85, 185),
    name='Frame',
    description='An empty frame.',
    take_allow=False,
    manipulate_allow=False)

frame_with_circle = pyv.Item(
    image=join('img', 'frame_with_circle.png'),
    topleft=(85, 185),
    name='Frame',
    description='A frame with a red circle. It looks very pretty.',
    take_allow=False,
    manipulate_allow=False)

house.add(frame_empty)


# Items -- Village

black_thingy = pyv.Item(
    image=join('img', 'black_thingy.png'),
    topleft=(100, 400),
    name='Black thing',
    description='A mysterious black thing.',
    manipulate_allow=False,
    manipulate_attempt="I don't know what to do with this.")

def use_item_callback(room, this, other):
    pyv.inventory.remove_item(this)
    room.remove(other)
    room.add(frame_with_circle)
    room.status_message = 'The circle looks very pretty inside the frame!'

red_circle = pyv.Item(
    image=join('img', 'red_circle.png'),
    topleft=(400, 450),
    name='Red circle',
    description='A red circle. It looks pretty.',
    manipulate_allow=False,
    manipulate_attempt="I don't know what to do with this.",
    use_item_callbacks=[(frame_empty, use_item_callback)])

bird = pyv.Item(
    image=join('img', 'bird.png'),
    topleft=(300, 100),
    name='Bird',
    description="A flying bird. I wonder were it's headed.",
    take_allow=False,
    take_attempt="I can't catch the bird.")

door_closed = pyv.Item(
    image=join('img', 'door_closed.png'),
    topleft=(246, 278),
    name='Door',
    description='The door is closed.',
    take_allow=False,
    manipulate_allow=True)

door_open = pyv.Item(
    image=join('img', 'door_open.png'),
    topleft=(246, 278),
    name='Door',
    description='The door is open.',
    take_allow=False,
    manipulate_allow=False,
    enter=house)

def manipulate_callback(room):
    room.remove(door_closed)
    room.status_message = 'The door opens easily.'
    room.add(door_open)
door_closed.manipulate_callback = manipulate_callback

village.add([black_thingy, red_circle, bird, door_closed])


# Main program
mainloop = pyv.MainLoop(village)
mainloop.run()
