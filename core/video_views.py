"""
REST API views for Video Call functionality.
"""

from rest_framework import views, status
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta

from .models import Room, Player, VideoCallParticipant, VideoCallSignal
from .authentication import AnonymousSessionAuthentication
from .video_consumer import broadcast_video_event


class VideoCallParticipantsView(views.APIView):
    """
    GET: Get list of current video call participants in a room.
    """
    authentication_classes = [AnonymousSessionAuthentication]

    def get(self, request, room_code):
        try:
            room = Room.objects.get(room_code=room_code.upper())
        except Room.DoesNotExist:
            return Response({'error': 'Room not found'}, status=404)

        # Get connected participants
        participants = VideoCallParticipant.objects.filter(
            room=room,
            is_connected=True
        ).select_related('player', 'player__user')

        participant_list = [
            {
                'player_id': str(p.player.user.id),
                'player_name': p.player.name,
                'player_avatar': p.player.avatar,
                'video_enabled': p.video_enabled,
                'audio_enabled': p.audio_enabled,
                'screen_sharing': p.screen_sharing,
                'joined_at': p.joined_at.isoformat()
            }
            for p in participants
        ]

        return Response({
            'room_code': room_code.upper(),
            'participant_count': len(participant_list),
            'participants': participant_list
        })


class VideoCallJoinView(views.APIView):
    """
    POST: Join a video call in a room.
    """
    authentication_classes = [AnonymousSessionAuthentication]

    def post(self, request, room_code):
        try:
            room = Room.objects.get(room_code=room_code.upper())
            player = Player.objects.get(user=request.user, room=room)
        except Room.DoesNotExist:
            return Response({'error': 'Room not found'}, status=404)
        except Player.DoesNotExist:
            return Response({'error': 'You are not in this room'}, status=403)

        video_enabled = request.data.get('video_enabled', True)
        audio_enabled = request.data.get('audio_enabled', True)

        # Create or update participant record
        participant, created = VideoCallParticipant.objects.update_or_create(
            room=room,
            player=player,
            defaults={
                'video_enabled': video_enabled,
                'audio_enabled': audio_enabled,
                'is_connected': True,
                'last_heartbeat': timezone.now()
            }
        )

        return Response({
            'message': 'Joined video call',
            'participant': {
                'player_id': str(player.user.id),
                'player_name': player.name,
                'video_enabled': participant.video_enabled,
                'audio_enabled': participant.audio_enabled
            }
        })


class VideoCallLeaveView(views.APIView):
    """
    POST: Leave a video call in a room.
    """
    authentication_classes = [AnonymousSessionAuthentication]

    def post(self, request, room_code):
        try:
            room = Room.objects.get(room_code=room_code.upper())
            player = Player.objects.get(user=request.user, room=room)
        except Room.DoesNotExist:
            return Response({'error': 'Room not found'}, status=404)
        except Player.DoesNotExist:
            return Response({'error': 'You are not in this room'}, status=403)

        # Mark as disconnected
        VideoCallParticipant.objects.filter(
            room=room,
            player=player
        ).update(is_connected=False)

        # Clean up old signals
        VideoCallSignal.objects.filter(
            room=room,
            from_player=player
        ).delete()

        return Response({'message': 'Left video call'})


class VideoCallMediaStateView(views.APIView):
    """
    PATCH: Update media state (video/audio/screen share).
    """
    authentication_classes = [AnonymousSessionAuthentication]

    def patch(self, request, room_code):
        try:
            room = Room.objects.get(room_code=room_code.upper())
            player = Player.objects.get(user=request.user, room=room)
        except Room.DoesNotExist:
            return Response({'error': 'Room not found'}, status=404)
        except Player.DoesNotExist:
            return Response({'error': 'You are not in this room'}, status=403)

        update_fields = {}
        if 'video_enabled' in request.data:
            update_fields['video_enabled'] = request.data['video_enabled']
        if 'audio_enabled' in request.data:
            update_fields['audio_enabled'] = request.data['audio_enabled']
        if 'screen_sharing' in request.data:
            update_fields['screen_sharing'] = request.data['screen_sharing']

        if update_fields:
            VideoCallParticipant.objects.filter(
                room=room,
                player=player
            ).update(**update_fields)

        return Response({'message': 'Media state updated', 'updated': update_fields})


class VideoCallICEServersView(views.APIView):
    """
    GET: Get TURN/STUN server configuration for WebRTC.
    """
    authentication_classes = [AnonymousSessionAuthentication]

    def get(self, request):
        # Return ICE server configuration
        # In production, you would use your own TURN server or a service like Twilio
        ice_servers = [
            # Public STUN servers (free, for NAT traversal)
            {'urls': 'stun:stun.l.google.com:19302'},
            {'urls': 'stun:stun1.l.google.com:19302'},
            {'urls': 'stun:stun2.l.google.com:19302'},
            {'urls': 'stun:stun3.l.google.com:19302'},
            {'urls': 'stun:stun4.l.google.com:19302'},
            # OpenRelay TURN servers (free, for relay when P2P fails)
            {
                'urls': 'turn:openrelay.metered.ca:80',
                'username': 'openrelayproject',
                'credential': 'openrelayproject'
            },
            {
                'urls': 'turn:openrelay.metered.ca:443',
                'username': 'openrelayproject',
                'credential': 'openrelayproject'
            },
            {
                'urls': 'turn:openrelay.metered.ca:443?transport=tcp',
                'username': 'openrelayproject',
                'credential': 'openrelayproject'
            },
        ]

        return Response({
            'ice_servers': ice_servers,
            'ice_transport_policy': 'all'  # 'all' or 'relay'
        })


class VideoCallCleanupView(views.APIView):
    """
    POST: Clean up stale video call participants (admin/cron job).
    Removes participants who haven't sent a heartbeat in 2 minutes.
    """
    authentication_classes = [AnonymousSessionAuthentication]

    def post(self, request, room_code=None):
        cutoff_time = timezone.now() - timedelta(minutes=2)

        if room_code:
            # Clean up specific room
            stale_count = VideoCallParticipant.objects.filter(
                room__room_code=room_code.upper(),
                is_connected=True,
                last_heartbeat__lt=cutoff_time
            ).update(is_connected=False)
        else:
            # Clean up all rooms
            stale_count = VideoCallParticipant.objects.filter(
                is_connected=True,
                last_heartbeat__lt=cutoff_time
            ).update(is_connected=False)

        # Clean up old signals (older than 5 minutes)
        signal_cutoff = timezone.now() - timedelta(minutes=5)
        signals_deleted, _ = VideoCallSignal.objects.filter(
            created_at__lt=signal_cutoff
        ).delete()

        return Response({
            'message': 'Cleanup completed',
            'stale_participants_disconnected': stale_count,
            'old_signals_deleted': signals_deleted
        })


class VideoCallSignalView(views.APIView):
    """
    POST: Send a WebRTC signal via REST API (fallback for when WebSocket is not available).
    GET: Get pending signals for the current user.
    """
    authentication_classes = [AnonymousSessionAuthentication]

    def get(self, request, room_code):
        """Get pending signals for this user."""
        try:
            room = Room.objects.get(room_code=room_code.upper())
            player = Player.objects.get(user=request.user, room=room)
        except Room.DoesNotExist:
            return Response({'error': 'Room not found'}, status=404)
        except Player.DoesNotExist:
            return Response({'error': 'You are not in this room'}, status=403)

        # Get undelivered signals
        signals = VideoCallSignal.objects.filter(
            room=room,
            to_player=player,
            delivered=False
        ).select_related('from_player', 'from_player__user').order_by('created_at')

        signal_list = [
            {
                'id': str(s.id),
                'signal_type': s.signal_type,
                'from_player_id': str(s.from_player.user.id),
                'from_player_name': s.from_player.name,
                'data': s.signal_data,
                'created_at': s.created_at.isoformat()
            }
            for s in signals
        ]

        # Mark as delivered
        signals.update(delivered=True, delivered_at=timezone.now())

        return Response({
            'signals': signal_list,
            'count': len(signal_list)
        })

    def post(self, request, room_code):
        """Send a signal to another player."""
        try:
            room = Room.objects.get(room_code=room_code.upper())
            player = Player.objects.get(user=request.user, room=room)
        except Room.DoesNotExist:
            return Response({'error': 'Room not found'}, status=404)
        except Player.DoesNotExist:
            return Response({'error': 'You are not in this room'}, status=403)

        target_player_id = request.data.get('target_player_id')
        signal_type = request.data.get('signal_type')
        signal_data = request.data.get('data')

        if not all([target_player_id, signal_type, signal_data]):
            return Response(
                {'error': 'Missing required fields: target_player_id, signal_type, data'},
                status=400
            )

        if signal_type not in ['offer', 'answer', 'ice_candidate', 'renegotiate']:
            return Response({'error': 'Invalid signal_type'}, status=400)

        try:
            to_player = Player.objects.get(
                user__id=target_player_id,
                room=room
            )
        except Player.DoesNotExist:
            return Response({'error': 'Target player not found'}, status=404)

        # Create signal
        signal = VideoCallSignal.objects.create(
            room=room,
            from_player=player,
            to_player=to_player,
            signal_type=signal_type,
            signal_data=signal_data
        )

        return Response({
            'message': 'Signal sent',
            'signal_id': str(signal.id)
        }, status=201)
