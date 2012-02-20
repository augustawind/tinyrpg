"""load and configure game resources"""

from pyglet.resource import Loader
from pyglet.gl import (glEnable, glBindTexture, glTexParameteri, GL_TEXTURE_2D,
                       GL_TEXTURE_MAG_FILTER, GL_NEAREST)

glEnable(GL_TEXTURE_2D)

class Loader(Loader):
    """Load program resource files from disk."""

    @staticmethod
    def _scale_texture(texture, width, height):
        """Scale the given texture to the given size.
        
        :param texture: The texture to scale.
        :type texture: pyglet.image.Texture
        :param width int: New width of texture, in pixels.
        :param height int: New height of texture, in pixels.
        """
        glBindTexture(GL_TEXTURE_2D, texture.id)
        texture.width = width
        texture.height = height
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)

    def image(self, name, width=None, height=None, flip_x=False, flip_y=False,
              rotate=0):
        """Load an image with an optional transformation.

        Extends the parent method to optionally scale the image to the
        given width and height.  If not given, no scaling will occur.
        
        :param width int: New width of image, in pixels.
        :param height int: New height of image, in pixels.
        """
        image = super(Loader, self).image(name, flip_x, flip_y, rotate,
                                          scale_x, scale_y)
        if width and height:
            self._scale_texture(image.texture, width, height)
