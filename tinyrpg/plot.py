"""tools for implementing plot mechanics"""

def plot(world, state, triggers):
    while triggers:
        # Get state updates
        updates = (yield)
        if updates is None:
            continue

        # Update state
        if type(updates) in (tuple, set, frozenset, list):
            state.update(updates)
        else:
            state.add(updates)

        # Call trigger functions
        for req_state, value in triggers.items():
            if type(value) in (tuple, list):
                func, nextbranch = value
            else:
                func = value
                nextbranch = None

            if req_state <= state:
                func(world)
                del triggers[req_state]
                triggers.update(nextbranch)


class Plot(object):
    """Class wrapper for ``plot`` generator."""

    def __init__(self, state, triggers):
        """Initialize the plot.

        :param world: A ``World`` object.
        :type world: tinyrpg.world.World
        :param state set: Describes for the plot state.
        :param triggers dict: Maps tuples describing subsets of possible
                              plot states to trigger tuples describing
                              actions to take when given states exist.

        Each item in `triggers` must map either a callable or a 2-tuple
        containing a callable followed by a dict of nested triggers,
        to a tuple of plot state elements, e.g.::

            plt = plot({
                ('state1', 'state2'): (func1, {     # nested triggers
                    # nested triggers
                    ('state3',): func2,             # no nested triggers
                    ('state4', 'state9', 'state11'): (func3, {
                        # further nested triggers
                        ...}),
                    ...}),
                ('state5',): func4,
                ...})

        Updates are sent by passing a sequence or a set containing the
        new elements to the ``send`` method. Calls to ``next`` or 
        ``send(None)`` are ignored.
        """
        self.state = state
        self.triggers = self._format_triggers(triggers)
        self._plot = None

    @staticmethod
    def _format_triggers(triggers):
        return dict((frozenset(k), (v[0], _format_triggers(v[1])))
                    for k, v in triggers.iteritems())

    def start(self, world):
        self._plot = plot(world, state, triggers)
        self._plot.next()

    def update(self, *updates):
        """Update the plot state with `updates`, and call any trigger
        functions if their elements are now present.

        Updates are applied in the order given.
        """
        self._plot.send(updates)
