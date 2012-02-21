"""build rooms from entities, and worlds from rooms"""

import pyglet
from pyglet.graphics import OrderedGroup
from pyglet.window import key

from tinyrpg import gui
from tinyrpg.base import GameMode

__all__ = ['TILE_WIDTH', 'TILE_HEIGHT', 'ORIGIN_X', 'ORIGIN_Y',
           'Entity', 'Room', 'World']

# Default width and height of each tile, in pixels
TILE_WIDTH = 24
TILE_HEIGHT = 24
# Default coordinates of the bottom left corner of the world display
# relative to the bottom left corner of the window
ORIGIN_X = 10
ORIGIN_Y = 124

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
                 facing=(0, -1), id=None):
        """Return an Entity instance.
        
        :Parameters:
            image : pyglet.image.AbstractImage or pyglet.image.Animation
                Image to represent the entity.

        All other parameters are optional and give initial values for
        instance attributes.
        """
        super(Entity, self).__init__(image)

        self.name = name
        self.walkable = walkable
        self.facing = facing
        self.action = action
        self.id = id


class Room(object):
    """The component parts of a world."""

    def __init__(self, name, entities, portals, origin_x=ORIGIN_X,
                 origin_y=ORIGIN_Y, tile_width=TILE_WIDTH,
                 tile_height=TILE_HEIGHT):
        self.name = name
        self._entities = entities
        self.portals = {}
        self.add_portals(**portals)
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
        """Visually update the entity to reflect its current state.
        
        :Parameters:
            `entity` : `Entity`
                The entity to update.
            `x` : `int`
                X coordinate of the entity.
            `y` : int
                Y coordinate of the entity.
            `z` : int
                Z coordinate of the entity.

        This method should be called every time a position in the room
        is assigned to a new Entity.
        """
        newx = x * self.tile_width + self.origin_x
        newy = y * self.tile_height + self.origin_y
        entity.set_position(newx, newy)
        entity.group = OrderedGroup(z)
        entity.batch = self.batch

    def update(self):
        """Update the room, preparing it for rendering."""
        for entity, x, y, z in self._iter_entities():
            self._update_entity(entity, x, y, z)

    def is_walkable(self, x, y):
        """Return True if the given position is walkable.

        A position in the room is walkable if its X and Y coordinates
        are in bounds and all entities at that X and Y are walkable.
        """
        if not (0 <= y < len(self._entities) and
                0 <= x < len(self._entities[y])):
            return False
        for e in self._entities[y][x]:
            if e != None and not e.walkable:
                return False
        return True

    @staticmethod
    def get_coords(entity):
        """Return X, Y, and Z coordinates of the given entity."""
        x = (entity.x - self.origin_x) / self.tile_width
        y = (entity.y - self.origin_y) / self.tile_height
        if entity.group is None:
            z = None
        else:
            z = entity.group.order
        return x, y, z

    def get_entity(self, x, y, z):
        """Return the entity at coordinate position (x, y, z), or None
        if no entity is present.
        """
        return self._entities[y][x][z]

    def add_portals(self, **portals):
        """Add and index the given portals.

        :param portals dict: A mapping of (x, y) coordinate tuples to
                             destination rooms.
        """
        for from_room, portal in portals.iteritems():
            for coords, dest in portal.iteritems():
                self.portals[coords] = dest
                self.portals[dest] = coords

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

        if z is None:
            z = depth - 1
        else:
            z = min(depth - 1, z)

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
    
    def step_entity(self, entity, xstep, ystep):
        """Move `entity` from its current position by (xstep, ystep),
        changing the direction of the entity to reflect the direction of
        the attempted move. 
        
        If `entity` is a string, move the unique entity with that id.
        Return True if the move was successful, else False.
        """
        if type(entity) is str:
            entity = self.get_entity(entity)

        entity.facing = (xstep / abs(xstep) if xstep else 0,
                      ystep / abs(ystep) if ystep else 0)

        x, y, z = self.get_coords(entity)
        newx = x + xstep
        newy = y + ystep
        if not self.is_walkable(newx, newy):
            return False

        self.pop_entity(x, y, z)
        self.add_entity(entity, newx, newy, z)
        return True

    def portal_entity(self, entity, x, y):
        """If a portal exists at (x, y), transfer entity from its
        current room to the destination room of the portal.
        """
        from_room = self.focus.name
        dest = self.portals[(x, y)]
        z = self.focus.get_coords(entity)[2]
        self.pop_entity(x, y, z)
        x, y = self.portals[self.focus.name]
        self.add_entity(entity, x, y, z, destname)


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
        return self._focus
    
    def __getitem__(self, key):
        return self._rooms[key]

    def set_focus(self, room=''):
        """Set the focus to room with name `room`, setting its batch to
        self.batch and updating its entities.
        """
        if self.focus:
            self.focus.batch = None
            self.focus.update()

        room = self[room] if room else self.focus
        room.batch = self.batch
        room.update()
        self._focus = room

    def step_player(self, xstep, ystep):
        """Step the player (`xstep`, `ystep`) tiles from her current
        position.

        If successful and the new position hosts a portal, portal
        the player.
        """
        success = self.step_entity(self.player, xstep, ystep)
        if not success:
            return

        from_room = self.focus.name
        x, y, z = self.focus.get_coords(self.player)
        if (x, y) in self.focus.portals:
            self.portal_player(x, y)

    def portal_player(self, x, y):
        """Transfer the player to the destination of the portal at
        (x, y), then set that room as the focus.
        """
        self.portal_entity(self.player, x, y)
        from_room = self.focus.name
        dest = self.portals[from_room][(x, y)]
        self.set_focus(dest)

    def interact(self):
        """If an interactable entity is in front of the player, make
        her interact with it. Else, do nothing.
        """
        x, y, z = self.focus.get_coords(self.player)
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
