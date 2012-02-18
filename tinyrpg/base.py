"""bottom-level base abstractions"""

import pyglet

class GameMode(object):
    """Abstract class for top-level game objects with event handlers."""

    def __init__(self, window):
        self.window = window
        self.batch = pyglet.graphics.Batch()

    def __repr__(self):
        """For identification purposes."""
        return self.__class__.__name__

    def activate(self):
        """Push all event handlers onto the window."""
        self.window.push_handlers(self)

    def on_draw(self):
        """Clear the window and repaint the batch."""
        self.window.clear()
        self.batch.draw()
