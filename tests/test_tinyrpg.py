from unittest.mock import *

import pyglet

from tinyrpg import *
from tinyrpg.base import GameMode

def TestRunGame_GamemodeHasActivateMethod_CallActivateAndRunEventLoop():
    gamemode = Mock(spec=GameMode)
    with patch.object(pyglet.app, 'run'):
        run_game(gamemode)
        gamemode.activate.assert_called_once_with()
        pyglet.app.run.assert_called_once_with()
