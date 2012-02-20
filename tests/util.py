from os.path import normpath

import pyglet

IMAGE_PATH = 'tests/res/images'

def dummy_image():
    return pyglet.image.load(normpath(IMAGE_PATH + '/sack.png'))
