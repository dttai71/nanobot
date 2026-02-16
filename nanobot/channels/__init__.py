"""
Chat channels module with plugin architecture.

Stage: 04 - BUILD
"""

from nanobot.channels.base import BaseChannel
from nanobot.channels.manager import ChannelManager

__all__ = ["BaseChannel", "ChannelManager"]
