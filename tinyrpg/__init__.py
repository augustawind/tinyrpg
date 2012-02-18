import pyglet

__all__ = ['run_game', 'action', 'base', 'gui', 'plot', 'resource', 'world']

def run_game(gamemode):
    """Run the game, activating the given GameMode."""
    gamemode.activate()
    pyglet.app.run()
