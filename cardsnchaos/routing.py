"""
WebSocket URL routing for cardsnchaos project.
"""

from django.urls import re_path
from core import consumers
from core import video_consumer

websocket_urlpatterns = [
    # Game room state updates
    re_path(r'ws/room/(?P<room_code>\w+)/$', consumers.RoomConsumer.as_asgi()),

    # Video call signaling
    re_path(r'ws/video/(?P<room_code>\w+)/$', video_consumer.VideoCallConsumer.as_asgi()),
]
