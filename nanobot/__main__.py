"""
Entry point for running nanobot as a module: python -m nanobot.

Stage: 04 - BUILD
"""

from nanobot.cli.commands import app

if __name__ == "__main__":
    app()
