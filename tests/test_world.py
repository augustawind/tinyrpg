import pyglet
from mock import *

from tests.util import dummy_image
from tinyrpg.world import *

class TestEntity(object):

    def TestClass_AllArgsGiven_SetExpectedInstanceAttrs(self):
        image = dummy_image()
        name = 'Dude'
        walkable = False
        action = object()
        facing = (1, 0)
        id = 'thedude'
        x = 1
        y = 2
        z = 3
        entity = Entity(image, name, walkable, action, facing, id, x, y, z)
        assert entity.name == name
        assert entity.walkable == walkable
        assert entity.action == action
        assert entity.facing == facing
        assert entity.id == id
        assert entity.tile_x == x
        assert entity.tile_y == y
        assert entity.tile_z == z

    def TestClass_NoKwargsGiven_SetExpectedInstanceAttrs(self):
        image = dummy_image()
        entity = Entity(image)
        assert entity.name == ''
        assert entity.walkable == False
        assert entity.action == None
        assert entity.facing == (0, -1)
        assert entity.id == None
        assert entity.tile_x == 0
        assert entity.tile_y == 0
        assert entity.tile_z == 0


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
            room.add_portals.assert_called_once_with(portals)

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

    def iter_entities(self, entities):
        for y, row in enumerate(entities):
            for x, cell in enumerate(row):
                for z, entity in enumerate(cell):
                    if entity:
                        yield entity, x, y, z

    def TestIterEntities_ForEachEntityThatTestsTrue_YieldEntityAndCoords(self):
        name = portals = MagicMock()
        entities = [
            [[Mock()], [Mock()]],
            [[None], [Mock()]]]

        room = Room(name, entities, portals)
        iter_ents = room._iter_entities()

        for entity, x, y, z in self.iter_entities(entities):
            yielded = next(iter_ents) 
            assert yielded == (entity, x, y, z)

    def TestUpdateEntity_ValidZCoordGiven_SetGroupOrderToZ(self):
        mockarg = MagicMock()
        room = Room('disco hall', mockarg, mockarg)

        entity = Mock(spec=Entity)
        x = 1
        y = 2
        z = 3
        room._update_entity(entity, x, y, z)
        entity.update.assert_called_with(
            x, y, z, room.origin_x, room.origin_y, room.tile_width,
            room.tile_height, room.batch)

    def TestUpdate_CallUpdateEntityOnAllEntities(self):
        entities = [[[Mock()]],
                    [[Mock()]]]
        portals = MagicMock()
        room = Room('jazz lounge', entities, portals)

        with patch.object(room, '_update_entity'):
            room.update()
            for entity, x, y, z in self.iter_entities(entities):
                room._update_entity.assert_any_call(entity, x, y, z)
    
    def TestIsWalkable_AllEntitiesAtGivenXYAreWalkable_ReturnTrue(self):
        walkable_ent = Mock(walkable=True)
        entities = [[[walkable_ent, walkable_ent]]]
        portals = MagicMock()
        room = Room('hip hop hut', entities, portals)

        assert room.is_walkable(0, 0)

    def TestIsWalkable_EntityAtGivenXYIsUnwalkable_ReturnFalse(self):
        walkable_ent = Mock(walkable=True)
        unwalkable_ent = Mock(walkable=False)
        entities = [[[walkable_ent, unwalkable_ent]]]
        portals = MagicMock()
        room = Room('house house', entities, portals)

        assert not room.is_walkable(0, 0)

    def TestIsWalkable_GivenXYOutOfBounds_ReturnFalse(self):
        entities = [[[Mock()]]]
        portals = MagicMock()
        room = Room('reggae shack', entities, portals)

        assert not room.is_walkable(0, 1)

    def TestAddPortals_MappingHasHashableVals_UpdatePortalsWith2WayMap(self):
        entities = MagicMock()
        portals = {}
        room = Room('generic room', entities, portals)

        new_portals = {'another room': (1, 1), 'some other room': (2, 5)}
        room.add_portals(new_portals)
        indexed_portals = new_portals.copy()
        indexed_portals.update((v, k) for (k, v) in new_portals.iteritems())
        assert room.portals == indexed_portals

    def TestAddEntity_(self):pass

    def TestPopEntity_(self):pass

    def TestStepEntity_(self):pass

    def TestPortalEntity_(self):pass
