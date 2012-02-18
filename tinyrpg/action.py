"""classes that succintly describe entity actions"""

import abc
from itertools import *

__all__ = [
    'AbstractAction', 'ActionIter', 'ActionLoop', 'ActionCycle',
    'ActionSequence', 'ResetAction', 'UpdatePlot', 'Alert', 'Talk', 'Move']


class AbstractAction(object):
    """Abstract entity action class.
    
    All entity action classes should derive from this class.
    """

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __call__(self, world, entity):
        """Execute the action, given WorldMode object `world` and
        acting Entity object `entity`.

        :param world: the active WorldMode object
        :type world: crystals.app.Worldmode
        :param entity: the "acting" entity
        :type entity: crystals.world.Entity
        """


class ActionIter(AbstractAction):
    """On call, calls the next action in sequence.
    
    Once the end of the sequence has been reached, each call to
    AbstractActionIter calls the final action in the sequence.
    """

    def __init__(self, *actions):
        self._actions = chain(actions[:-1], repeat(actions[-1]))

    def __call__(self, world, entity):
        next(self._actions)(world, entity)


class ActionLoop(ActionIter):
    """On call, calls the next action in sequence, starting over at the
    beginning once the end of the sequence is reached.
    """

    def __init__(self, *actions):
        self._actions = cycle(actions)


class ActionCycle(AbstractAction):
    """On call, acts like AbstractActionIter, but iterates through the action
    sequence N times before resting on the final action.
    """

    def __init__(self, n, *actions):
        """Initialize the action. 

        :param n: Number of times to repeat the sequence, 2 or more.
        :type n: int
        :param actions: One or more action objects.
        """
        self._actions = chain(*repeat(actions, n))
        self._final_action = actions[-1]

    def __call__(self, world, entity):
        try:
            action = next(self._actions)
        except StopIteration:
            self._actions = repeat(self._final_action)
            action = next(self._actions)
        finally:
            action(world, entity)


class ActionSequence(AbstractAction):
    """On call, calls each given action in sequence."""

    def __init__(self, *actions):
        self._actions = actions

    def __call__(self, world, entity):
        for action in self._actions:
            action(world, entity)


class ResetAction(AbstractAction):
    """On call, overwrites the entity's action with the given action."""

    def __init__(self, action):
        self.action = action

    def __call__(self, world, entity):
        entity.action = self.action
        self.action(world, entity)


class UpdatePlot(AbstractAction):
    """On call, sends updates to the plot generator."""

    def __init__(self, *updates):
        self.updates = updates

    def __call__(self, world, entity):
        world.plot.update(*self.updates)


class Alert(AbstractAction):
    """On call, writes text to the infobox."""

    def __init__(self, text):
        self.text = text

    def __call__(self, world, entity):
        world.infobox.write(self.text)


class Talk(Alert):
    """On call, writes text to the infobox preceded by the name of the
    speaking entity.
    """

    sep = ': '

    def __call__(self, world, entity):
        text = entity.name + self.sep + self.text
        world.infobox.write(text)


class Move(AbstractAction):
    """On call, move the entity a given distance from its current location."""

    def __init__(self, xstep, ystep):
        """Initialize the action.

        :param xstep: number of tiles to move horizontally
        :type xstep: int
        :param ystep: number of tiles to move vertically
        :type ystep: int
        """
        self.step = (xstep, ystep)

    def __call__(self, world, entity):
        world.step_entity(entity, *self.step)

