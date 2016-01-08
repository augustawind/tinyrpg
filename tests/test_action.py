from unittest.mock import *
from nose.tools import raises

from tinyrpg.action import *
from tinyrpg.world import Entity, World


class TestActionIter(object):

    def TestCall_NumCallsIsLTNumActions_CallOnlyNextAction(self):
        action1 = Mock(spec=AbstractAction)
        action2 = Mock(spec=AbstractAction, side_effect=AssertionError)
        actioniter = ActionIter(action1, action2)
        world, entity = object(), object()

        actioniter(world, entity)
        action1.assert_called_once_with(world, entity)

    def TestCall_NumCallsIsGTENumActions_CallFinalAction(self):
        action = Mock(spec=AbstractAction)
        actioniter = ActionIter(action)
        world, entity = object(), object()

        actioniter(world, entity)
        actioniter(world, entity)
        assert action.call_count == 2


class TestActionLoop(object):

    def TestCall_NumCallsExceedsNumActions_LoopAround(self):
        actions = [Mock(spec=AbstractAction) for i in range(3)]
        actionloop = ActionLoop(*actions)
        world, entity = object(), object()

        for i in range(5):
            actionloop(world, entity)

        assert actions[0].call_count == 2
        assert actions[1].call_count == 2
        assert actions[2].call_count == 1


class TestActionCycle(object):

    def TestCall_NumCallsLTNumActions_CallOnlyNextAction(self):
        action1 = Mock(spec=AbstractAction)
        action2 = Mock(spec=AbstractAction, side_effect=AssertionError)
        actioncycle = ActionCycle(2, action1, action2)
        world, entity = object(), object()

        actioncycle(world, entity)
        action1.assert_called_once_with(world, entity)

    def TestCall_NumCallsExceedsNumActions_LoopAround(self):
        actions = [Mock(spec=AbstractAction) for i in range(3)]
        actioncycle = ActionCycle(2, *actions)
        world, entity = object(), object()

        for i in range(5):
            actioncycle(world, entity)

        assert actions[0].call_count == 2
        assert actions[1].call_count == 2
        assert actions[2].call_count == 1


class TestActionSequence(object):

    def TestCall_CallAllActions(self):
        actions = [Mock(spec=AbstractAction) for i in range(2)]
        actionseq = ActionSequence(*actions)
        world, entity = object(), object()

        for i in range(3):
            actionseq(world, entity)
        assert actions[0].call_count == 3
        assert actions[1].call_count == 3


class TestResetAction(object):

    def TestCall_SetEntityActionToGivenAction(self):
        newaction = Mock(spec=AbstractAction)
        resetaction = ResetAction(newaction)
        world = object()
        entity = Mock()

        resetaction(world, entity)
        assert entity.action is newaction

    def TestCall_CallGivenActionWithGivenWorldAndEntity(self):
        newaction = Mock(spec=AbstractAction)
        resetaction = ResetAction(newaction)
        world = object()
        entity = Mock()

        resetaction(world, entity)
        newaction.assert_called_once_with(world, entity)


class TestUpdatePlot(object):

    def TestCall_UpdateGivenWorldWithGivenPlotUpdates(self):
        updates = (Mock(), Mock())
        updateplot = UpdatePlot(*updates)
        world = Mock()
        entity = object()

        updateplot(world, entity)
        world.plot.update.assert_called_once_with(*updates)


class TestAlert(object):

    def TestCall_WriteGivenTextToGivenWorldInfobox(self):
        text = "Danger approaches!"
        alert = Alert(text)
        world = Mock()
        entity = object()

        alert(world, entity)
        world.infobox.write.assert_called_once_with(text)


class TestTalk(object):

    def TestCall_WriteTextPrefixedByEntityNameToWorldInfobox(self):
        text = "Nice to meet you."
        talk = Talk(text)
        world = Mock()
        entity = Mock()

        name = "Earl"
        entity.name = name
        sep = '==> '
        talk.sep = sep

        talk(world, entity)
        world.infobox.write.assert_called_once_with(name + sep + text)


class TestMove(object):

    def TestCall_StepGivenEntityGivenDistance(self):
        xstep = 3
        ystep = 2
        move = Move(xstep, ystep)

        world = Mock(spec=World)
        entity = object() 

        move(world, entity)
        world.focus.step_entity.assert_called_once_with(entity, xstep, ystep)
