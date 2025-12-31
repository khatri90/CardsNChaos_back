"""
WebRTC Signaling Consumer for Video Calls.
Handles peer-to-peer video call signaling within game rooms.
"""

import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone

from .models import Room, Player, VideoCallParticipant, VideoCallSignal


class VideoCallConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for WebRTC signaling.
    Handles offer/answer/ICE candidate exchange for video calls.
    """

    async def connect(self):
        self.room_code = self.scope['url_route']['kwargs']['room_code']
        self.video_group_name = f'video_{self.room_code}'

        # Get user from session (set by middleware)
        self.user = self.scope.get('user')

        if not self.user:
            await self.close(code=4001)
            return

        # Verify player is in the room
        self.player = await self.get_player()
        if not self.player:
            await self.close(code=4002)
            return

        # Join video call group
        await self.channel_layer.group_add(
            self.video_group_name,
            self.channel_name
        )

        await self.accept()

        # Send current participants list
        participants = await self.get_participants()
        await self.send_json({
            'type': 'participants_list',
            'participants': participants
        })

        # Deliver any pending signals
        pending_signals = await self.get_pending_signals()
        for signal in pending_signals:
            await self.send_json({
                'type': 'signal',
                'signal_type': signal['signal_type'],
                'from_player_id': signal['from_player_id'],
                'from_player_name': signal['from_player_name'],
                'data': signal['data']
            })

    async def disconnect(self, close_code):
        if hasattr(self, 'player') and self.player:
            # Remove from video call participants
            await self.leave_video_call()

            # Notify others that this participant left
            await self.channel_layer.group_send(
                self.video_group_name,
                {
                    'type': 'participant_left',
                    'player_id': str(self.player.user.id),
                    'player_name': self.player.name
                }
            )

        # Leave video group
        await self.channel_layer.group_discard(
            self.video_group_name,
            self.channel_name
        )

    async def receive_json(self, content):
        """
        Handle incoming WebSocket messages for video signaling.
        """
        action = content.get('action')

        if action == 'join':
            # Join the video call
            await self.join_video_call(
                video_enabled=content.get('video_enabled', True),
                audio_enabled=content.get('audio_enabled', True)
            )

            # Broadcast to others that a new participant joined
            await self.channel_layer.group_send(
                self.video_group_name,
                {
                    'type': 'participant_joined',
                    'player_id': str(self.player.user.id),
                    'player_name': self.player.name,
                    'player_avatar': self.player.avatar,
                    'video_enabled': content.get('video_enabled', True),
                    'audio_enabled': content.get('audio_enabled', True)
                }
            )

        elif action == 'leave':
            # Leave the video call
            await self.leave_video_call()

            await self.channel_layer.group_send(
                self.video_group_name,
                {
                    'type': 'participant_left',
                    'player_id': str(self.player.user.id),
                    'player_name': self.player.name
                }
            )

        elif action == 'offer':
            # WebRTC offer - send to specific peer
            target_player_id = content.get('target_player_id')
            if target_player_id:
                await self.send_signal_to_peer(
                    target_player_id=target_player_id,
                    signal_type='offer',
                    signal_data=content.get('sdp')
                )

        elif action == 'answer':
            # WebRTC answer - send to specific peer
            target_player_id = content.get('target_player_id')
            if target_player_id:
                await self.send_signal_to_peer(
                    target_player_id=target_player_id,
                    signal_type='answer',
                    signal_data=content.get('sdp')
                )

        elif action == 'ice_candidate':
            # ICE candidate - send to specific peer
            target_player_id = content.get('target_player_id')
            if target_player_id:
                await self.send_signal_to_peer(
                    target_player_id=target_player_id,
                    signal_type='ice_candidate',
                    signal_data=content.get('candidate')
                )

        elif action == 'toggle_video':
            # Toggle video on/off
            video_enabled = content.get('enabled', True)
            await self.update_media_state(video_enabled=video_enabled)

            await self.channel_layer.group_send(
                self.video_group_name,
                {
                    'type': 'media_state_changed',
                    'player_id': str(self.player.user.id),
                    'video_enabled': video_enabled
                }
            )

        elif action == 'toggle_audio':
            # Toggle audio on/off
            audio_enabled = content.get('enabled', True)
            await self.update_media_state(audio_enabled=audio_enabled)

            await self.channel_layer.group_send(
                self.video_group_name,
                {
                    'type': 'media_state_changed',
                    'player_id': str(self.player.user.id),
                    'audio_enabled': audio_enabled
                }
            )

        elif action == 'toggle_screen_share':
            # Toggle screen sharing
            screen_sharing = content.get('enabled', False)
            await self.update_media_state(screen_sharing=screen_sharing)

            await self.channel_layer.group_send(
                self.video_group_name,
                {
                    'type': 'screen_share_changed',
                    'player_id': str(self.player.user.id),
                    'screen_sharing': screen_sharing
                }
            )

        elif action == 'heartbeat':
            # Update heartbeat timestamp
            await self.update_heartbeat()

    async def send_signal_to_peer(self, target_player_id, signal_type, signal_data):
        """
        Send a WebRTC signal to a specific peer.
        """
        # Store signal for potential async delivery
        await self.store_signal(target_player_id, signal_type, signal_data)

        # Send via group (the target will filter by player_id)
        await self.channel_layer.group_send(
            self.video_group_name,
            {
                'type': 'relay_signal',
                'target_player_id': target_player_id,
                'from_player_id': str(self.player.user.id),
                'from_player_name': self.player.name,
                'signal_type': signal_type,
                'data': signal_data
            }
        )

    # ============== Channel Layer Event Handlers ==============

    async def participant_joined(self, event):
        """Broadcast when a participant joins the video call."""
        # Don't send to self
        if event['player_id'] != str(self.player.user.id):
            await self.send_json({
                'type': 'participant_joined',
                'player_id': event['player_id'],
                'player_name': event['player_name'],
                'player_avatar': event.get('player_avatar', ''),
                'video_enabled': event.get('video_enabled', True),
                'audio_enabled': event.get('audio_enabled', True)
            })

    async def participant_left(self, event):
        """Broadcast when a participant leaves the video call."""
        if event['player_id'] != str(self.player.user.id):
            await self.send_json({
                'type': 'participant_left',
                'player_id': event['player_id'],
                'player_name': event['player_name']
            })

    async def relay_signal(self, event):
        """Relay WebRTC signal to target peer."""
        # Only send to the intended target
        if event['target_player_id'] == str(self.player.user.id):
            await self.send_json({
                'type': 'signal',
                'signal_type': event['signal_type'],
                'from_player_id': event['from_player_id'],
                'from_player_name': event['from_player_name'],
                'data': event['data']
            })
            # Mark signal as delivered
            await self.mark_signal_delivered(
                event['from_player_id'],
                event['signal_type']
            )

    async def media_state_changed(self, event):
        """Broadcast media state changes."""
        if event['player_id'] != str(self.player.user.id):
            await self.send_json({
                'type': 'media_state_changed',
                'player_id': event['player_id'],
                'video_enabled': event.get('video_enabled'),
                'audio_enabled': event.get('audio_enabled')
            })

    async def screen_share_changed(self, event):
        """Broadcast screen share state changes."""
        if event['player_id'] != str(self.player.user.id):
            await self.send_json({
                'type': 'screen_share_changed',
                'player_id': event['player_id'],
                'screen_sharing': event['screen_sharing']
            })

    # ============== Database Operations ==============

    @database_sync_to_async
    def get_player(self):
        """Get the player object for this user in this room."""
        try:
            return Player.objects.select_related('user').get(
                user=self.user,
                room__room_code=self.room_code
            )
        except Player.DoesNotExist:
            return None

    @database_sync_to_async
    def get_participants(self):
        """Get all current video call participants."""
        participants = VideoCallParticipant.objects.filter(
            room__room_code=self.room_code,
            is_connected=True
        ).select_related('player', 'player__user')

        return [
            {
                'player_id': str(p.player.user.id),
                'player_name': p.player.name,
                'player_avatar': p.player.avatar,
                'video_enabled': p.video_enabled,
                'audio_enabled': p.audio_enabled,
                'screen_sharing': p.screen_sharing
            }
            for p in participants
        ]

    @database_sync_to_async
    def join_video_call(self, video_enabled=True, audio_enabled=True):
        """Add player to video call participants."""
        room = Room.objects.get(room_code=self.room_code)
        participant, created = VideoCallParticipant.objects.update_or_create(
            room=room,
            player=self.player,
            defaults={
                'video_enabled': video_enabled,
                'audio_enabled': audio_enabled,
                'is_connected': True,
                'last_heartbeat': timezone.now()
            }
        )
        return participant

    @database_sync_to_async
    def leave_video_call(self):
        """Remove player from video call participants."""
        VideoCallParticipant.objects.filter(
            room__room_code=self.room_code,
            player=self.player
        ).update(is_connected=False)

    @database_sync_to_async
    def update_media_state(self, video_enabled=None, audio_enabled=None, screen_sharing=None):
        """Update player's media state."""
        update_fields = {}
        if video_enabled is not None:
            update_fields['video_enabled'] = video_enabled
        if audio_enabled is not None:
            update_fields['audio_enabled'] = audio_enabled
        if screen_sharing is not None:
            update_fields['screen_sharing'] = screen_sharing

        if update_fields:
            VideoCallParticipant.objects.filter(
                room__room_code=self.room_code,
                player=self.player
            ).update(**update_fields)

    @database_sync_to_async
    def update_heartbeat(self):
        """Update the heartbeat timestamp."""
        VideoCallParticipant.objects.filter(
            room__room_code=self.room_code,
            player=self.player
        ).update(last_heartbeat=timezone.now())

    @database_sync_to_async
    def store_signal(self, target_player_id, signal_type, signal_data):
        """Store a signal for potential async delivery."""
        try:
            room = Room.objects.get(room_code=self.room_code)
            to_player = Player.objects.get(
                user__id=target_player_id,
                room=room
            )

            VideoCallSignal.objects.create(
                room=room,
                from_player=self.player,
                to_player=to_player,
                signal_type=signal_type,
                signal_data=signal_data
            )
        except (Room.DoesNotExist, Player.DoesNotExist):
            pass

    @database_sync_to_async
    def get_pending_signals(self):
        """Get undelivered signals for this player."""
        signals = VideoCallSignal.objects.filter(
            room__room_code=self.room_code,
            to_player=self.player,
            delivered=False
        ).select_related('from_player', 'from_player__user').order_by('created_at')

        result = [
            {
                'signal_type': s.signal_type,
                'from_player_id': str(s.from_player.user.id),
                'from_player_name': s.from_player.name,
                'data': s.signal_data
            }
            for s in signals
        ]

        # Mark as delivered
        signals.update(delivered=True, delivered_at=timezone.now())

        return result

    @database_sync_to_async
    def mark_signal_delivered(self, from_player_id, signal_type):
        """Mark a specific signal as delivered."""
        VideoCallSignal.objects.filter(
            room__room_code=self.room_code,
            to_player=self.player,
            from_player__user__id=from_player_id,
            signal_type=signal_type,
            delivered=False
        ).update(delivered=True, delivered_at=timezone.now())


def broadcast_video_event(room_code, event_type, data):
    """
    Utility function to broadcast video events from views.
    """
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'video_{room_code}',
        {
            'type': event_type,
            **data
        }
    )
