"""build rooms from entities, and worlds from rooms"""

import pyglet
from pyglet.graphics import OrderedGroup
from pyglet.window import key

from tinyrpg import gui
from tinyrpg.base import GameMode

__all__ = ['ORIGIN_X', 'ORIGIN_Y', 'TILE_WIDTH', 'TILE_HEIGHT',
           'Entity', 'Room', 'World']

# Default coordinates of the bottom left corner of the world display
# relative to the bottom left corner of the window
ORIGIN_X = 10
ORIGIN_Y = 124
# Default width and height of each tile, in pixels
TILE_WIDTH = 24
TILE_HEIGHT = 24

class Entity(pyglet.sprite.Sprite):
    """A tangible thing in the game world.
    
    :Ivariables:
        name : str
            Name of the entity for display to the player.
        walkable : bool
            ``True`` if the entity can be walked upon; ``False`` if the
            entity obstructs movement.
        action : callable
            Object to be called if the entity is engaged with.
        facing : sequence
            A 2-tuple or list describing the direction the entity
            initially faces.
        id : object
            If given, can be used by a `crystals.world.Room` object
            to index specific entities by id.
    """

    def __init__(self, image, name='', walkable=False, action=None,
                 facing=(0, -1), id=None, tile_x=0, tile_y=0, tile_z=0):
        """Return an Entity instance.
        
        :Parameters:
            image : pyglet.image.AbstractImage or pyglet.image.Animation
                Image to represent the entity.
            tile_x : int
                X coordinate of initial tile. Defaults to ``0``.
            tile_y : int
                Y coordinate of initial tile. Defaults to ``0``.
            tile_z : int
                Z coordinate of initial tile. Defaults to ``0``.

        All other parameters are optional and give initial values for
        instance attributes.
        """
        super(Entity, self).__init__(image)

        self.name = name
        self.walkable = walkable
        self.facing = facing
        self.action = action
        self.id = id

        self._tile_x = tile_x
        self._tile_y = tile_y
        self._tile_z = tile_z

    @property
    def tile_x(self):
        """X tile position of the Entity."""
        return self._tile_x
    @property
    def tile_y(self):
        """Y tile position of the Entity."""
        return self._tile_y
    @property
    def tile_z(self):
        """Z tile position of the Entity."""
        return self._tile_z
    @property
    def tile_pos(self):
        """Swizzle for ``tile_x, tile_y, tile_z``."""
        return self._tile_x, self._tile_y, self._tile_z

    def update(self, x, y, z, offset_x=0, offset_y=0, tile_width=1,
               tile_height=1, batch=None):
        """Update the entity to reflect the given positional information
        and batch.
        
        :Parameters:
            x : int
                X tile position of the entity.
            y : int
                Y tile position of the entity.
            z : int
                Z tile position of the entity.
            offset_x : int
                Horizontal placement offset, in pixels.
            offset_y : int
                Vertical placement offset, in pixels.
            tile_width : int
                Width to give each tile, in pixels.
            tile_height : int
                Height to give each tile, in pixels.
            batch: ``pyglet.graphics.Batch`` or ``None``
                Add entity to this batch.
        """
        self._tile_x = x
        self._tile_y = y
        self._tile_z = z

        self.x = self._tile_x * tile_width + origin_x
        self.y = self._tile_y * tile_height + origin_y
        self.group = OrderedGroup(self._tile_z)
        self.batch = batch


class Room(object):
    """The component parts of a world."""

    def __init__(self, name, entities, portals, origin_x=ORIGIN_X,
                 origin_y=ORIGIN_Y, tile_width=TILE_WIDTH,
                 tile_height=TILE_HEIGHT):
        self.name = name
        self._entities = entities
        self.portals = {}
        self.add_portals(portals)
        self.batch = None

        # Index unique entities by instance attribute `id`
        self.uniques = {}
        for entity, x, y, z in self._iter_entities():
            if entity.id:
                self.uniques[entity.id] = entity

        self.origin_x = origin_x
        self.origin_y = origin_y
        self.tile_width = tile_width
        self.tile_height = tile_height
    
    def _iter_entities(self):
        for y, row in enumerate(self._entities):
            for x, cell in enumerate(row):
                for z, entity in enumerate(cell):
                    if entity:
                        yield entity, x, y, z

    def _update_entity(self, entity, x, y, z):
        """Update the entity to appear at the given coordinates.
        
        :Parameters:
            `entity` : `Entity`
                The entity to update.
            `x` : `int`
                x coordinate of the entity.
            `y` : int
                y coordinate of the entity.
            `z` : int
                z coordinate of the entity.

        This method should be called every time a position in the room
        is assigned to a new Entity.
        """
        entity.update(x, y, z, self.origin_x, self.origin_y, self.tile_width,
                      self.tile_height, self.batch)

    def update(self):
        """Update all entities in the room, preparing it for rendering."""
        for entity, x, y, z in self._iter_entities():
            self._update_entity(entity, x, y, z)

    def is_walkable(self, x, y):
        """Return True if the given position is walkable.

        :rtype: bool

        A position in the room is walkable if its x and y coordinates
        are in bounds and all entities at that x and y are walkable.
        """
        return(0 <= y < len(self._entities) and
               0 <= x < len(self._entities[y]) and
               all(e is None or e.walkable for e in self._entities[y][x]))

    def add_portals(self, portals):
        """Add and index the given portals.

        :param portals: A mapping of destination rooms to
                        ``(x, y)`` coordinate tuples.
        """
        self.portals.update(portals)
        self.portals.update((v, k) for k, v in portals.items())

    def _place_entity(self, entity, x, y, z):
        """Assign coordinate point (x, y, z) to `entity`."""
        self._entities[y][x][z] = entity

    def add_entity(self, entity, x, y, z=None):
        """Add the given entity at (x, y, z).
        
        If z is None or out of range, attempt to add the entity to an
        empty cell with the lowest z value at (x, y).  If none are found,
        append the entity to the top of the stack.  Otherwise, if no
        entity exists at (x, y, z) place it there, else insert the
        entity at ``z + 1``.
        """
        depth = len(self._entities[y][x])
        z = depth - 1 if z is None else min(depth - 1, z)

        if self._entities[y][x][z]:
            z += 1
            if z == depth:
                self._entities[y][x].append(None)
            else:
                self._entities[y][x].insert(z, None)
                for i, ent in enumerate(self._entities[y][x][z + 1:]):
                    if ent:
                        self._place_entity(ent, x, y, z + 1 + i)

        self._place_entity(entity, x, y, z)
        self._update_entity(entity, x, y, z)
    
    def pop_entity(self, x, y, z):
        """Remove and return the entity at (x, y, z)."""
        entity = self._entities[y][x][z]
        self._entities[y][x][z] = None
        return entity
    
    def step_entity(self, entity, xstep, ystep, z=None):
        """Move given entity a given distance from its current position.

        If the new position isn't walkable, nothing happens.

        :Parameters:
            entity : Entity or str
                The entity to move. If a string is given, use the
                unique entity with that id.
            xstep : int
                X distance to move. Positive values move the entity
                right and negative values left.
            ystep : int
                Y distance to move. Positive values move the entity up
                and negative values down.

        :returns: True if the move succeeded, False otherwise.
        :rtype: bool
        """
        if type(entity) is str:
            entity = self.uniques[entity]

        entity.facing = (xstep / abs(xstep) if xstep else 0,
                         ystep / abs(ystep) if ystep else 0)

        newx = entity.tile_x + xstep
        newy = entity.tile_y + ystep
        if not self.is_walkable(newx, newy):
            return False

        if z is None:
            z = entity.tile_z
        self.pop_entity(x, y, z)
        self.add_entity(entity, newx, newy, z)
        return True

    def portal_entity(self, entity, x, y):
        """Portal the entity from its current given position.

        :Parameters:
            entity : Entity
                The entity to portal.
            x : int
                X coordinate to portal from.
            y : int
                Y coordinate to portal from.
        
        The given coordinates must host both the given entity and a
        portal.
        """
        from_room = self.focus.name
        dest = self.portals[(x, y)]
        self.pop_entity(x, y, entity.tile_z)
        x, y = self.portals[self.focus.name]


class World(GameMode):
    """Player explores a collection of `Room` objects."""

    def __init__(self, window, rooms, player, plot):
        super(World, self).__init__(window)

        self._rooms = rooms
        self.player = player
        self.plot = plot
        self.plot.start(self)

        ib_padding = 10
        ib_x = ib_y = ib_padding
        ib_width = window.width - (ib_padding * 2)
        ib_height = 100
        ib_style = dict(font_size=10, line_spacing=20)
        self.infobox = gui.InfoBox(
            ib_x, ib_y, ib_width, ib_height, self.batch, show_box=True,
            style=ib_style)

        self.key_switch = {
            key.MOTION_LEFT: (self.step_player, -1, 0),
            key.MOTION_RIGHT: (self.step_player, 1, 0),
            key.MOTION_DOWN: (self.step_player, 0, -1),
            key.MOTION_UP: (self.step_player, 0, 1),
            key.SPACE: (self.interact,),
        }

        self._focus = None
        self.set_focus(start)

    @property
    def focus(self):
        """The currently focused room."""
        return self._focus
    
    def __getitem__(self, key):
        return self._rooms[key]

    def set_focus(self, room=''):
        """Set the focus to the room with the given key, rendering it.

        :param room: Name of a room in the world.
        :type room: str
        
        If rooms tests false, just redraw the currently focused room.
        """
        if self.focus:
            self.focus.batch = None
            self.focus.update()

        room = self[room] if room else self.focus
        room.batch = self.batch
        room.update()
        self._focus = room

    def step_player(self, xstep, ystep):
        """Move the player a given distance from its current position.

        :Parameters:
            xstep : int
                X distance to move. Positive values move the entity
                right and negative values left.
            ystep : int
                Y distance to move. Positive values move the entity up
                and negative values down.

        If successful and the new position hosts a portal, portal
        the player.
        """
        if not self.step_entity(self.player, xstep, ystep):
            return

        from_room = self.focus.name
        x, y, z = self.player.tile_pos
        if (x, y) in self.focus.portals:
            self.portal_player(x, y)

    def portal_player(self, x, y):
        """Portal the player from its position at the given coordinates.
        
        The given coordinates should"""
        if not self.portal_entity(self.player, x, y):
            return
        from_room = self.focus.name
        dest = self.portals[from_room][(x, y)]
        self.set_focus(dest)

    def interact(self):
        """If an interactable entity is in front of the player, make
        her interact with it. Else, do nothing.
        """
        x, y, z = self.player.tile_pos
        x += self.player.facing[0]
        y += self.player.facing[1]
        for entity in self.focus[y][x]:
            if entity and entity.action:
                entity.action(self, entity)

    def on_key_press(self, key, modifiers):
        """Process user input."""
        if key not in self.key_switch:
            return
        self.key_switch[key][0](*self.key_switch[key][1:])
