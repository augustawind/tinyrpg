import pyglet
from mock import *

from tests.util import dummy_image
from tinyrpg.world import *

class TestEntity(object):

    def TestClass_SetExpectedInstanceAttrs(self):
        image = dummy_image()
        name = 'Dude'
        walkable = False
        action = object()
        facing = (1, 0)
        id = 'thedude'
        entity = Entity(image, name, walkable, action, facing, id)
        assert entity.name == name
        assert entity.walkable == walkable
        assert entity.action == action
        assert entity.facing == facing
        assert entity.id == id


class TestRoom(object):

    def TestClass_AllArgsGiven_SetExpectedInstanceAttrs(self):
        name = 'The Room'
        entities = portals = MagicMock()
        origin_x = 15
        origin_y = 25
        tile_width = 8
        tile_height = 16
        room = Room(name, entities, portals, origin_x, origin_y, tile_width,
                    tile_height)

        assert room.name == name
        assert room.batch is None
        assert room.origin_x == origin_x
        assert room.origin_y == origin_y
        assert room.tile_width == tile_width
        assert room.tile_height == tile_height

    def TestClass_TileAndOriginArgsOmitted_SetToGlobalConstants(self):
        name = entities = portals = MagicMock()
        room = Room(name, entities, portals)

        assert room.origin_x == ORIGIN_X
        assert room.origin_y == ORIGIN_Y
        assert room.tile_width == TILE_WIDTH
        assert room.tile_height == TILE_HEIGHT

    def TestClass_CallAddPortalsOnGivenPortals(self):
        name = entities = MagicMock()
        portals = MagicMock()
        with patch.object(Room, 'add_portals'):
            room = Room(name, entities, portals)
            room.add_portals.assert_called_once_with(**portals)

    def TestClass_SetInitialBatchToNone(self):
        mockargs = [MagicMock()] * 3

    def TestClass_IndexEntitiesByIdAttr(self):
        e0 = Mock(id=0)
        e1 = Mock(id=1)
        e2 = Mock(id=2)
        e3 = Mock(id=3)
        entities = [
            [[e1, e2], []],
            [[e3], [e0]]]

        name = portals = MagicMock()
        room = Room(name, entities, portals)
        assert room.uniques == {1: e1, 2: e2, 3: e3}

    def TestIterEntities_ForEachEntityThatTestsTrue_YieldEntityAndCoords(self):
        name = portals = MagicMock()
        entities = [
            [[Mock()], [Mock()]],
            [[None], [Mock()]]]

        room = Room(name, entities, portals)
        iter_ents = room._iter_entities()

        for y, row in enumerate(entities):
            for x, cell in enumerate(row):
                for z, entity in enumerate(cell):
                    if entity:
                        yielded = next(iter_ents) 
                        assert yielded == (entity, x, y, z)
