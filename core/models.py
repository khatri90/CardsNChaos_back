"""
Database models for CardsNChaos game.
Replaces Firebase Firestore collections.
"""

import uuid
import random
from django.db import models


class AnonymousUser(models.Model):
    """
    Replaces Firebase Anonymous Auth.
    Each session gets a unique anonymous user.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session_key = models.CharField(max_length=40, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['session_key']),
        ]

    def __str__(self):
        return f"AnonymousUser {self.id}"


class Pack(models.Model):
    """
    Card pack collection - replaces Firestore 'packs' collection.
    """
    id = models.CharField(max_length=50, primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default='')
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Card(models.Model):
    """
    Individual card - replaces Firestore 'cards' collection.
    """
    CARD_TYPES = [
        ('black', 'Black (Question)'),
        ('white', 'White (Answer)'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    text = models.TextField()
    card_type = models.CharField(max_length=5, choices=CARD_TYPES)
    pack = models.ForeignKey(Pack, on_delete=models.CASCADE, related_name='cards')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['pack', 'card_type']),
        ]

    def __str__(self):
        return f"{self.card_type}: {self.text[:50]}..."


class Room(models.Model):
    """
    Game room/session - replaces Firestore 'rooms' collection.
    """
    ROOM_STATUS = [
        ('WAITING', 'Waiting for players'),
        ('PLAYING', 'Game in progress'),
        ('GAME_OVER', 'Game finished'),
    ]

    GAME_PHASES = [
        ('WAITING', 'Waiting'),
        ('SUBMISSION', 'Card Submission'),
        ('PICKING', 'Czar Picking'),
        ('TRANSITIONING', 'Round Transition'),
        ('GAME_OVER', 'Game Over'),
    ]

    room_code = models.CharField(max_length=4, primary_key=True, unique=True)
    host = models.ForeignKey(AnonymousUser, on_delete=models.CASCADE, related_name='hosted_rooms')
    status = models.CharField(max_length=10, choices=ROOM_STATUS, default='WAITING')
    pack = models.ForeignKey(Pack, on_delete=models.SET_NULL, null=True, blank=True)
    max_rounds = models.IntegerField(default=10)
    current_round = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    # Game State
    czar_id = models.UUIDField(null=True, blank=True)
    current_question = models.TextField(null=True, blank=True)
    phase = models.CharField(max_length=15, choices=GAME_PHASES, default='WAITING')
    round_expires_at = models.DateTimeField(null=True, blank=True)

    # Decks stored as JSON arrays (card texts)
    black_deck = models.JSONField(default=list)
    white_deck = models.JSONField(default=list)

    # Last round result
    last_round_winner_id = models.UUIDField(null=True, blank=True)
    last_round_winner_name = models.CharField(max_length=50, null=True, blank=True)
    last_round_winning_card = models.TextField(null=True, blank=True)
    last_round_number = models.IntegerField(null=True, blank=True)

    @classmethod
    def generate_room_code(cls):
        """Generate unique 4-letter room code (excluding I, O for clarity)."""
        chars = "ABCDEFGHJKLMNPQRSTUVWXYZ"
        while True:
            code = ''.join(random.choices(chars, k=4))
            if not cls.objects.filter(room_code=code).exists():
                return code

    def __str__(self):
        return f"Room {self.room_code} ({self.status})"


class Player(models.Model):
    """
    Player in a room - extracted from nested 'players' object in Firestore.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(AnonymousUser, on_delete=models.CASCADE, related_name='players')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='players')
    name = models.CharField(max_length=50)
    avatar = models.CharField(max_length=10)
    score = models.IntegerField(default=0)
    is_host = models.BooleanField(default=False)
    is_online = models.BooleanField(default=True)
    hand = models.JSONField(default=list)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'room']
        indexes = [
            models.Index(fields=['room', 'is_online']),
        ]

    def __str__(self):
        return f"{self.name} in {self.room.room_code}"


class Submission(models.Model):
    """
    Card submission for a round - extracted from nested 'submissions' in Firestore.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='submissions')
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='submissions')
    round_number = models.IntegerField()
    card_text = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['room', 'player', 'round_number']

    def __str__(self):
        return f"{self.player.name}'s submission in round {self.round_number}"


class VideoCallParticipant(models.Model):
    """
    Tracks participants in a video call within a room.
    Used for WebRTC signaling and call state management.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='video_participants')
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='video_calls')

    # Media state
    video_enabled = models.BooleanField(default=True)
    audio_enabled = models.BooleanField(default=True)
    screen_sharing = models.BooleanField(default=False)

    # Connection state
    is_connected = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)
    last_heartbeat = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['room', 'player']
        indexes = [
            models.Index(fields=['room', 'is_connected']),
        ]

    def __str__(self):
        return f"{self.player.name} in video call ({self.room.room_code})"


class VideoCallSignal(models.Model):
    """
    Stores WebRTC signaling messages for asynchronous delivery.
    Used when a peer is temporarily disconnected.
    """
    SIGNAL_TYPES = [
        ('offer', 'WebRTC Offer'),
        ('answer', 'WebRTC Answer'),
        ('ice_candidate', 'ICE Candidate'),
        ('renegotiate', 'Renegotiation Request'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='video_signals')
    from_player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='sent_signals')
    to_player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='received_signals')

    signal_type = models.CharField(max_length=20, choices=SIGNAL_TYPES)
    signal_data = models.JSONField()  # Contains SDP or ICE candidate data

    created_at = models.DateTimeField(auto_now_add=True)
    delivered = models.BooleanField(default=False)
    delivered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['to_player', 'delivered']),
            models.Index(fields=['room', 'created_at']),
        ]
        ordering = ['created_at']

    def __str__(self):
        return f"{self.signal_type} from {self.from_player.name} to {self.to_player.name}"
