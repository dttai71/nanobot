"""
Message bus module for decoupled channel-agent communication.

Stage: 04 - BUILD
"""

from nanobot.bus.events import InboundMessage, OutboundMessage
from nanobot.bus.queue import MessageBus

__all__ = ["MessageBus", "InboundMessage", "OutboundMessage"]
