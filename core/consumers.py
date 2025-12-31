"""
WebSocket consumers for real-time game updates.
Replaces Firestore onSnapshot functionality.
"""

import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models import Room, Player
from .serializers import RoomDetailSerializer


class RoomConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for real-time room updates.
    Replaces Firestore onSnapshot functionality.
    """

    async def connect(self):
        self.room_code = self.scope['url_route']['kwargs']['room_code']
        self.room_group_name = f'room_{self.room_code}'

        # Get user from session (set by middleware)
        self.user = self.scope.get('user')

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # Mark player online if user exists
        if self.user:
            await self.set_player_online(True)

        # Send initial room state
        room_data = await self.get_room_data()
        if room_data:
            await self.send_json({
                'type': 'room_state',
                'data': room_data
            })
        else:
            await self.send_json({
                'type': 'error',
                'message': 'Room not found'
            })

    async def disconnect(self, close_code):
        # Mark player offline
        if self.user:
            await self.set_player_online(False)

        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

        # Broadcast player left
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'room_update',
                'action': 'player_left'
            }
        )

    async def receive_json(self, content):
        """
        Handle incoming WebSocket messages.
        Clients can send actions like ping/heartbeat.
        """
        action = content.get('action')

        if action == 'ping':
            await self.send_json({'type': 'pong'})

        elif action == 'heartbeat':
            if self.user:
                await self.set_player_online(True)

    async def room_update(self, event):
        """
        Called when room state changes.
        Broadcasts updated room data to all connected clients.
        """
        room_data = await self.get_room_data()
        if room_data:
            await self.send_json({
                'type': 'room_state',
                'data': room_data,
                'action': event.get('action', 'update')
            })

    @database_sync_to_async
    def get_room_data(self):
        """Fetch serialized room data."""
        try:
            room = Room.objects.prefetch_related(
                'players', 'submissions'
            ).get(room_code=self.room_code)

            return RoomDetailSerializer(room, context={
                'user': self.user
            }).data
        except Room.DoesNotExist:
            return None

    @database_sync_to_async
    def set_player_online(self, is_online):
        """Update player online status."""
        try:
            player = Player.objects.get(
                user=self.user,
                room__room_code=self.room_code
            )
            player.is_online = is_online
            player.save(update_fields=['is_online'])
        except Player.DoesNotExist:
            pass


def broadcast_room_update(room_code, action='update'):
    """
    Utility function to broadcast room updates from views.
    Called after any room state change.
    """
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'room_{room_code}',
        {
            'type': 'room_update',
            'action': action
        }
    )
