""""""

import pyglet
from pyglet.graphics import OrderedGroup
from pyglet.window import key

from tinyrpg import gui
from tinyrpg.base import GameMode

__all__ = ['Entity', 'Room', 'World']

TILE_SIZE = 24 # Width and height of each tile, in pixels
ORIGIN_X = 10  # X and Y coordinates of the bottom left corner
ORIGIN_Y = 124 # of room display, in pixels


class Entity(pyglet.sprite.Sprite):
    """A tangible thing in the game world."""

    def __init__(self, name, walkable, image, action=None, facing=(0, -1),  
                 id=None):
        super(Entity, self).__init__(image)

        self.name = name
        self.walkable = walkable
        self._facing = facing
        self.action = action
        self.id = id


class Room(list):

    def __init__(self, name, entities):
        super(Room, self).__init__(entities)
        self.name = name
        self.batch = None

        # Index unique entities by instance attribute `id`
        self.uniques = {}
        for entity, x, y, z in self._iter_entities():
            if entity.id:
                self.uniques[entity.id] = entity

    def _iter_entities(self):
        for y in xrange(len(self)):
            for x in xrange(len(self[y])):
                for z, entity in enumerate(self[y][x]):
                    if entity:
                        yield entity, x, y, z

    def _update_entity(self, entity, x, y, z):
        """Update the entity's rendered position to reflect (x, y, z),
        and set the entity's batch to self.batch.
        """
        newx = x * TILE_SIZE + ORIGIN_X
        newy = y * TILE_SIZE + ORIGIN_Y
        entity.set_position(newx, newy)
        entity.group = OrderedGroup(z)
        entity.batch = self.batch

    def update(self):
        """Update the room, preparing it for rendering."""
        for entity, x, y, z in self._iter_entities():
            self._update_entity(entity, x, y, z)

    def is_walkable(self, x, y):
        """Return True if, for every layer, (x, y) is in bounds and is
        either None or a walkable entity, else return False.
        """
        if (x < 0 or x >= len(self[0])) or (y < 0 or y >= len(self)):
            return False
        for e in self[y][x]:
            if e != None and not e.walkable:
                return False
        return True

    def get_coords(self, entity):
        """Return x, y, and z coordinates of the given entity in the room."""
        x = (entity.x - ORIGIN_X) / TILE_SIZE
        y = (entity.y - ORIGIN_Y) / TILE_SIZE
        if entity.group is None:
            z = None
        else:
            z = entity.group.order
        return x, y, z
    
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

    def _place_entity(self, entity, x, y, z):
        """Assign coordinate point (x, y, z) to `entity`."""
        self[y][x][z] = entity
        self._update_entity(entity, x, y, z)

    def add_entity(self, entity, x, y, z=None):
        """Add the given entity at (x, y, z).
        
        If z is None or out of range, attempt to add the entity to an
        empty cell with the lowest z value at (x, y).  If none are found,
        append the entity to the top of the stack.  Otherwise, if no
        entity exists at (x, y, z) place it there, else insert the
        entity at ``z + 1``.
        """
        depth = len(self[y][x])

        if z is None:
            z = depth - 1
        else:
            z = min(depth - 1, z)

        if self[y][x][z]:
            z += 1
            if z == depth:
                self[y][x].append(None)
            else:
                self[y][x].insert(z, None)
                for i, ent in enumerate(self[y][x][z + 1:]):
                    if ent:
                        self._place_entity(ent, x, y, z + 1 + i)

        self._place_entity(entity, x, y, z)
    
    def pop_entity(self, x, y, z):
        """Remove and return the entity at (x, y, z)."""
        entity = self[y][x][z]
        self[y][x][z] = None
        return entity


class StaticWorld(dict):
    """A collection of rooms linked by portals."""

    def __init__(self, rooms, portals, start):
        dict.__init__(self, rooms)

        self._portals_dest2xy = dict.fromkeys(portals, {})
        self._portals_xy2dest = dict.fromkeys(portals, {})
        for from_room, portal in portals.iteritems():
            for dest, xy in portal.iteritems():
                self._portals_dest2xy[from_room][dest] = xy
                self._portals_xy2dest[from_room][xy] = dest

        self._focus = None
        self.batch = None
        self.set_focus(start)



class World(GameMode):
    """Game mode where the player explores a world and interacts with
    its entities.
    """

    def __init__(self, window, rooms, portals, start, player, plot):
        GameMode.__init__(self, window)
        dict.__init__(self, rooms)

        self.player = player
        self.plot = plot
        self.plot.send(self)

        self.batch = pyglet.graphics.Batch()
        
        ib_padding = 10
        ib_x = ib_y = ib_padding
        ib_width = window.width - (ib_padding * 2)
        ib_height = 100
        ib_style = dict(font_size=10, line_spacing=20)
        self.infobox = gui.InfoBox(
            ib_x, ib_y, ib_width, ib_height, self.batch, show_box=True,
            style=ib_style)

        self._portals_dest2xy = dict.fromkeys(portals, {})
        self._portals_xy2dest = dict.fromkeys(portals, {})
        for from_room, portal in portals.iteritems():
            for dest, xy in portal.iteritems():
                self._portals_dest2xy[from_room][dest] = xy
                self._portals_xy2dest[from_room][xy] = dest

        self.inputdict = {
            key.MOTION_LEFT: (self.step_player, -1, 0),
            key.MOTION_RIGHT: (self.step_player, 1, 0),
            key.MOTION_DOWN: (self.step_player, 0, -1),
            key.MOTION_UP: (self.step_player, 0, 1),
            key.SPACE: (self.interact,),
        }

        self.action_args = {
            'Alert': (self.infobox,),
            'Talk': (self.infobox,),
            'UpdatePlot': (self.plot,),
        }

        self._focus = None
        self.set_focus(start)

    @property
    def focus(self):
        return self._focus

    @property
    def portals_dest2xy(self):
        return self._portals_dest2xy

    @property
    def portals_xy2dest(self):
        return self._portals_xy2dest

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

    def portal_entity(self, entity, x, y):
        """If a portal exists at (x, y), transfer entity from its
        current room to the destination room of the portal.
        """
        destname = self.portals_xy2dest[self.focus.name][(x, y)]
        z = self.focus.get_coords(entity)[2]
        self.pop_entity(x, y, z)
        x, y = self.portals_dest2xy[destname][self.focus.name]
        self.add_entity(entity, x, y, z, destname)

    def step_entity(self, entity, xstep, ystep):
        """Step the given entity (`xstep`, `ystep`) tiles from her
        current position, if the target destination is walkable.

        If the move succeeds, return True. Else, return False.
        """

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
        if self.portals_xy2dest[from_room].get((x, y)):
            self.portal_player(x, y)

    def portal_player(self, x, y):
        """Transfer the player to the destination of the portal at
        (x, y), then set that room as the focus.
        """
        self.portal_entity(self.player, x, y)
        from_room = self.focus.name
        dest = self.portals_xy2dest[from_room][(x, y)]
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
        if key not in self.inputdict:
            return
        self.inputdict[key][0](*self.inputdict[key][1:])
