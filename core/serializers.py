"""
DRF serializers for CardsNChaos models.
"""

from rest_framework import serializers
from .models import Pack, Card, Room, Player, Submission


class PackSerializer(serializers.ModelSerializer):
    card_count = serializers.SerializerMethodField()

    class Meta:
        model = Pack
        fields = ['id', 'name', 'description', 'enabled', 'card_count', 'created_at', 'updated_at']

    def get_card_count(self, obj):
        return {
            'black': obj.cards.filter(card_type='black').count(),
            'white': obj.cards.filter(card_type='white').count()
        }


class CardSerializer(serializers.ModelSerializer):
    pack_id = serializers.CharField(source='pack.id', read_only=True)
    type = serializers.CharField(source='card_type')

    class Meta:
        model = Card
        fields = ['id', 'text', 'type', 'pack_id', 'created_at']


class CardCreateSerializer(serializers.Serializer):
    text = serializers.CharField()
    type = serializers.ChoiceField(choices=['black', 'white'])
    pack_id = serializers.CharField()


class PlayerSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='user.id')

    class Meta:
        model = Player
        fields = ['id', 'name', 'avatar', 'score', 'is_host', 'is_online', 'hand']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Only show hand to the player themselves
        request_user = self.context.get('user')
        if request_user and str(instance.user.id) != str(request_user.id):
            data['hand'] = []
        return data


class SubmissionSerializer(serializers.ModelSerializer):
    player_id = serializers.CharField(source='player.user.id')

    class Meta:
        model = Submission
        fields = ['player_id', 'card_text']


class RoomSerializer(serializers.ModelSerializer):
    players = serializers.SerializerMethodField()
    pack_id = serializers.CharField(source='pack.id', allow_null=True)
    host_id = serializers.CharField(source='host.id')

    class Meta:
        model = Room
        fields = [
            'room_code', 'host_id', 'status', 'pack_id', 'max_rounds',
            'current_round', 'players', 'created_at'
        ]

    def get_players(self, obj):
        return obj.players.count()


class RoomDetailSerializer(serializers.ModelSerializer):
    """
    Full room state for WebSocket updates.
    Matches Firestore document structure.
    """
    players = serializers.SerializerMethodField()
    gameState = serializers.SerializerMethodField()
    hostId = serializers.CharField(source='host.id')
    packId = serializers.SerializerMethodField()
    roomCode = serializers.CharField(source='room_code')
    maxRounds = serializers.IntegerField(source='max_rounds')
    currentRound = serializers.IntegerField(source='current_round')
    createdAt = serializers.DateTimeField(source='created_at')

    class Meta:
        model = Room
        fields = [
            'roomCode', 'hostId', 'status', 'packId',
            'maxRounds', 'currentRound', 'createdAt',
            'players', 'gameState'
        ]

    def get_packId(self, obj):
        return obj.pack.id if obj.pack else None

    def get_players(self, obj):
        # Return as dictionary keyed by user ID (like Firestore)
        players = {}
        request_user = self.context.get('user')

        for player in obj.players.all():
            player_data = {
                'id': str(player.user.id),
                'name': player.name,
                'avatar': player.avatar,
                'score': player.score,
                'isHost': player.is_host,
                'isOnline': player.is_online,
                'hand': player.hand if request_user and str(player.user.id) == str(request_user.id) else []
            }
            players[str(player.user.id)] = player_data

        return players

    def get_gameState(self, obj):
        # Get current round submissions
        submissions = {}
        for sub in obj.submissions.filter(round_number=obj.current_round):
            submissions[str(sub.player.user.id)] = sub.card_text

        last_round_result = None
        if obj.last_round_winner_id:
            last_round_result = {
                'winnerId': str(obj.last_round_winner_id),
                'winnerName': obj.last_round_winner_name,
                'winningCard': obj.last_round_winning_card,
                'roundNumber': obj.last_round_number
            }

        return {
            'czarId': str(obj.czar_id) if obj.czar_id else None,
            'currentQuestion': obj.current_question,
            'submissions': submissions,
            'blackDeck': obj.black_deck,
            'whiteDeck': obj.white_deck,
            'roundExpiresAt': obj.round_expires_at.isoformat() if obj.round_expires_at else None,
            'phase': obj.phase,
            'lastRoundResult': last_round_result
        }


class RoomCreateSerializer(serializers.Serializer):
    host_name = serializers.CharField(max_length=50)
    avatar = serializers.CharField(max_length=10)
    pack_id = serializers.CharField(max_length=50, required=False, default='standard')
    max_rounds = serializers.IntegerField(min_value=1, max_value=999, required=False, default=10)


class JoinRoomSerializer(serializers.Serializer):
    player_name = serializers.CharField(max_length=50)
    avatar = serializers.CharField(max_length=10)


class SubmitCardSerializer(serializers.Serializer):
    card_text = serializers.CharField()


class PickWinnerSerializer(serializers.Serializer):
    winner_id = serializers.CharField()


class UpdateSettingsSerializer(serializers.Serializer):
    pack_id = serializers.CharField(required=False)
    max_rounds = serializers.IntegerField(min_value=1, max_value=999, required=False)


class ImportCardsSerializer(serializers.Serializer):
    pack_id = serializers.CharField()
    cards = serializers.DictField()
