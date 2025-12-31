"""
REST API views for CardsNChaos.
"""

import uuid

from rest_framework import views, viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from django.utils import timezone

from .models import AnonymousUser, Pack, Card, Room, Player, Submission
from .serializers import (
    PackSerializer, CardSerializer, CardCreateSerializer,
    RoomSerializer, RoomDetailSerializer, RoomCreateSerializer,
    JoinRoomSerializer, SubmitCardSerializer, PickWinnerSerializer,
    UpdateSettingsSerializer, ImportCardsSerializer
)
from .authentication import AnonymousSessionAuthentication
from .game_logic import GameEngine
from .consumers import broadcast_room_update


# ============== Authentication ==============

class AnonymousAuthView(views.APIView):
    """
    Creates or retrieves anonymous user session.
    Replaces Firebase Anonymous Auth.

    If client provides a stored_uid from localStorage, we try to recover
    that user and associate it with the current session. This handles
    cases where the session cookie expired but the user still has their
    UID in localStorage.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        # Ensure session exists
        if not request.session.session_key:
            request.session.create()

        session_key = request.session.session_key
        stored_uid = request.data.get('stored_uid')

        user = None
        created = False
        recovered = False

        # Try to recover user from stored_uid if provided
        if stored_uid:
            try:
                user = AnonymousUser.objects.get(id=stored_uid)
                # Update their session_key to the current session
                if user.session_key != session_key:
                    # Check if another user already has this session_key
                    existing_session_user = AnonymousUser.objects.filter(
                        session_key=session_key
                    ).exclude(id=stored_uid).first()

                    if existing_session_user:
                        # Delete the session-based user if they have no game data
                        # (the stored_uid user is the "real" one with game history)
                        if not existing_session_user.players.exists():
                            existing_session_user.delete()
                        else:
                            # Both users have game data - orphan the session user
                            # with a unique placeholder session key
                            existing_session_user.session_key = f"orphaned_{uuid.uuid4()}"
                            existing_session_user.save(update_fields=['session_key'])

                    user.session_key = session_key
                    user.save(update_fields=['session_key'])
                    recovered = True
            except AnonymousUser.DoesNotExist:
                # stored_uid was invalid, will create new user below
                pass

        # If we couldn't recover, get or create by session
        if user is None:
            user, created = AnonymousUser.objects.get_or_create(
                session_key=session_key
            )

        return Response({
            'uid': str(user.id),
            'session_key': session_key,
            'created': created,
            'recovered': recovered
        })


class SessionStatusView(views.APIView):
    """
    Get current session status.
    """
    authentication_classes = [AnonymousSessionAuthentication]

    def get(self, request):
        return Response({
            'uid': str(request.user.id),
            'authenticated': True
        })


# ============== Room Management ==============

class RoomListCreateView(views.APIView):
    """
    POST: Create a new room (host creates room).
    """
    authentication_classes = [AnonymousSessionAuthentication]

    def post(self, request):
        serializer = RoomCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user

        # Generate unique room code
        room_code = Room.generate_room_code()

        # Get pack
        pack_id = serializer.validated_data.get('pack_id', 'standard')
        pack = Pack.objects.filter(id=pack_id, enabled=True).first()

        # Create room
        room = Room.objects.create(
            room_code=room_code,
            host=user,
            pack=pack,
            max_rounds=serializer.validated_data.get('max_rounds', 10),
            status='WAITING',
            phase='WAITING'
        )

        # Create host as first player
        Player.objects.create(
            user=user,
            room=room,
            name=serializer.validated_data['host_name'],
            avatar=serializer.validated_data['avatar'],
            is_host=True,
            is_online=True
        )

        return Response({
            'room_code': room_code,
            'room': RoomSerializer(room).data
        }, status=status.HTTP_201_CREATED)


class RoomDetailView(views.APIView):
    """
    GET: Get room details.
    """
    authentication_classes = [AnonymousSessionAuthentication]

    def get(self, request, room_code):
        try:
            room = Room.objects.prefetch_related(
                'players', 'submissions'
            ).get(room_code=room_code.upper())
        except Room.DoesNotExist:
            return Response(
                {'error': 'Room not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(RoomDetailSerializer(room, context={
            'user': request.user
        }).data)


class JoinRoomView(views.APIView):
    """
    POST: Join an existing room.
    """
    authentication_classes = [AnonymousSessionAuthentication]

    def post(self, request, room_code):
        serializer = JoinRoomSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            room = Room.objects.get(room_code=room_code.upper())
        except Room.DoesNotExist:
            return Response(
                {'error': 'Room not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if room.status != 'WAITING':
            return Response(
                {'error': 'Game already started'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if room.players.count() >= 8:
            return Response(
                {'error': 'Room is full'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = request.user

        # Check if already in room
        existing_player = Player.objects.filter(user=user, room=room).first()
        if existing_player:
            existing_player.is_online = True
            existing_player.name = serializer.validated_data['player_name']
            existing_player.avatar = serializer.validated_data['avatar']
            existing_player.save()
            broadcast_room_update(room_code.upper())
            return Response({'message': 'Rejoined room'})

        # Create new player
        Player.objects.create(
            user=user,
            room=room,
            name=serializer.validated_data['player_name'],
            avatar=serializer.validated_data['avatar'],
            is_host=False,
            is_online=True
        )

        # Broadcast update via WebSocket
        broadcast_room_update(room_code.upper())

        return Response({'message': 'Joined room successfully'})


class LeaveRoomView(views.APIView):
    """
    POST: Leave a room.
    """
    authentication_classes = [AnonymousSessionAuthentication]

    def post(self, request, room_code):
        try:
            room = Room.objects.get(room_code=room_code.upper())
            player = Player.objects.get(user=request.user, room=room)
        except (Room.DoesNotExist, Player.DoesNotExist):
            return Response({'error': 'Not found'}, status=404)

        player.is_online = False
        player.save()

        broadcast_room_update(room_code.upper())

        return Response({'message': 'Left room'})


class StartGameView(views.APIView):
    """
    POST: Start the game (host only).
    """
    authentication_classes = [AnonymousSessionAuthentication]

    def post(self, request, room_code):
        try:
            room = Room.objects.get(room_code=room_code.upper())
        except Room.DoesNotExist:
            return Response({'error': 'Room not found'}, status=404)

        # Verify host
        if room.host != request.user:
            return Response({'error': 'Only host can start'}, status=403)

        players = room.players.filter(is_online=True)
        if players.count() < 3:
            return Response(
                {'error': 'Need at least 3 players'},
                status=400
            )

        try:
            # Initialize game using GameEngine
            engine = GameEngine(room)
            engine.start_game()
        except ValueError as e:
            return Response({'error': str(e)}, status=400)

        # Broadcast update
        broadcast_room_update(room_code.upper(), action='game_started')

        return Response({'message': 'Game started'})


class UpdateRoomSettingsView(views.APIView):
    """
    PATCH: Update room settings (host only).
    """
    authentication_classes = [AnonymousSessionAuthentication]

    def patch(self, request, room_code):
        serializer = UpdateSettingsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            room = Room.objects.get(room_code=room_code.upper())
        except Room.DoesNotExist:
            return Response({'error': 'Room not found'}, status=404)

        # Verify host
        if room.host != request.user:
            return Response({'error': 'Only host can update settings'}, status=403)

        if room.status != 'WAITING':
            return Response({'error': 'Cannot change settings during game'}, status=400)

        # Update settings
        if 'pack_id' in serializer.validated_data:
            pack = Pack.objects.filter(
                id=serializer.validated_data['pack_id'],
                enabled=True
            ).first()
            if pack:
                room.pack = pack

        if 'max_rounds' in serializer.validated_data:
            room.max_rounds = serializer.validated_data['max_rounds']

        room.save()

        broadcast_room_update(room_code.upper())

        return Response({'message': 'Settings updated'})


# ============== Game Actions ==============

class SubmitCardView(views.APIView):
    """
    POST: Submit a white card.
    """
    authentication_classes = [AnonymousSessionAuthentication]

    def post(self, request, room_code):
        serializer = SubmitCardSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            room = Room.objects.get(room_code=room_code.upper())
            player = Player.objects.get(user=request.user, room=room)
        except (Room.DoesNotExist, Player.DoesNotExist):
            return Response({'error': 'Not found'}, status=404)

        try:
            engine = GameEngine(room)
            engine.submit_card(player, serializer.validated_data['card_text'])
        except ValueError as e:
            return Response({'error': str(e)}, status=400)

        # Broadcast update
        broadcast_room_update(room_code.upper())

        return Response({'message': 'Card submitted'})


class PickWinnerView(views.APIView):
    """
    POST: Czar picks the winning card.
    """
    authentication_classes = [AnonymousSessionAuthentication]

    def post(self, request, room_code):
        serializer = PickWinnerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            room = Room.objects.get(room_code=room_code.upper())
            player = Player.objects.get(user=request.user, room=room)
        except (Room.DoesNotExist, Player.DoesNotExist):
            return Response({'error': 'Not found'}, status=404)

        # Verify czar
        if str(player.user.id) != str(room.czar_id):
            return Response({'error': 'Only czar can pick'}, status=403)

        try:
            engine = GameEngine(room)
            engine.pick_winner(serializer.validated_data['winner_id'])
        except ValueError as e:
            return Response({'error': str(e)}, status=400)

        # Broadcast update
        broadcast_room_update(room_code.upper(), action='winner_picked')

        return Response({'message': 'Winner picked'})


class HandleTimeoutView(views.APIView):
    """
    POST: Handle round timeout.
    """
    authentication_classes = [AnonymousSessionAuthentication]

    def post(self, request, room_code):
        try:
            room = Room.objects.get(room_code=room_code.upper())
        except Room.DoesNotExist:
            return Response({'error': 'Room not found'}, status=404)

        engine = GameEngine(room)
        engine.handle_timeout()

        broadcast_room_update(room_code.upper())

        return Response({'message': 'Timeout handled'})


# ============== Card Pack Management ==============

class PackViewSet(viewsets.ModelViewSet):
    """
    Full CRUD for packs.
    """
    queryset = Pack.objects.all()
    serializer_class = PackSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = Pack.objects.all()
        enabled_only = self.request.query_params.get('enabled', None)
        if enabled_only == 'true':
            queryset = queryset.filter(enabled=True)
        return queryset

    @action(detail=True, methods=['patch'])
    def toggle(self, request, pk=None):
        """Toggle pack enabled status."""
        pack = self.get_object()
        pack.enabled = not pack.enabled
        pack.save()
        return Response(PackSerializer(pack).data)


class CardViewSet(viewsets.ModelViewSet):
    """
    Full CRUD for cards.
    """
    queryset = Card.objects.all()
    serializer_class = CardSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = Card.objects.all()
        pack_id = self.request.query_params.get('pack_id')
        card_type = self.request.query_params.get('type')

        if pack_id and pack_id != 'all':
            queryset = queryset.filter(pack_id=pack_id)
        if card_type:
            queryset = queryset.filter(card_type=card_type)

        return queryset

    def create(self, request, *args, **kwargs):
        serializer = CardCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            pack = Pack.objects.get(id=serializer.validated_data['pack_id'])
        except Pack.DoesNotExist:
            return Response({'error': 'Pack not found'}, status=404)

        card = Card.objects.create(
            text=serializer.validated_data['text'],
            card_type=serializer.validated_data['type'],
            pack=pack
        )

        return Response(CardSerializer(card).data, status=status.HTTP_201_CREATED)


class SyncDatabaseView(views.APIView):
    """
    Sync database with static card data.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        from django.core.management import call_command
        from io import StringIO

        out = StringIO()
        call_command('seed_cards', stdout=out)

        return Response({'message': out.getvalue()})


class ImportCardsView(views.APIView):
    """
    Bulk import cards from JSON.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ImportCardsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        pack_id = serializer.validated_data['pack_id']
        cards_data = serializer.validated_data['cards']

        try:
            pack = Pack.objects.get(id=pack_id)
        except Pack.DoesNotExist:
            return Response({'error': 'Pack not found'}, status=404)

        count = 0

        for text in cards_data.get('black', []):
            Card.objects.get_or_create(
                text=text,
                card_type='black',
                pack=pack
            )
            count += 1

        for text in cards_data.get('white', []):
            Card.objects.get_or_create(
                text=text,
                card_type='white',
                pack=pack
            )
            count += 1

        return Response({'imported': count})
