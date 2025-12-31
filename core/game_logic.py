"""
Game logic engine for CardsNChaos.
Replaces game logic from game.js.
"""

import random
from datetime import timedelta
from django.utils import timezone
from django.db import transaction

from .models import Room, Player, Submission, Card


class GameEngine:
    """
    Centralized game logic handler.
    Replaces game logic scattered in Firebase game.js
    """

    SUBMISSION_TIME = 60  # seconds
    PICKING_TIME = 30  # seconds
    INITIAL_HAND_SIZE = 7

    def __init__(self, room: Room):
        self.room = room

    @transaction.atomic
    def start_game(self):
        """
        Initialize game state when host starts.
        Replaces startGame() in game.js
        """
        players = list(self.room.players.filter(is_online=True))

        # Fetch cards from database
        pack = self.room.pack
        black_cards = []
        white_cards = []

        if pack:
            black_cards = list(
                Card.objects.filter(pack=pack, card_type='black')
                .values_list('text', flat=True)
            )
            white_cards = list(
                Card.objects.filter(pack=pack, card_type='white')
                .values_list('text', flat=True)
            )

        # If no cards in DB, this is an error state
        if not black_cards or not white_cards:
            raise ValueError("No cards found for the selected pack")

        # Shuffle decks
        random.shuffle(black_cards)
        random.shuffle(white_cards)

        # Select random czar
        czar = random.choice(players)

        # Deal initial hands
        for player in players:
            hand = []
            for _ in range(self.INITIAL_HAND_SIZE):
                if white_cards:
                    hand.append(white_cards.pop())
            player.hand = hand
            player.save()

        # Draw first black card
        first_question = black_cards.pop() if black_cards else "No questions available!"

        # Set expiry 60s from now
        expiry = timezone.now() + timedelta(seconds=self.SUBMISSION_TIME)

        # Update room state
        self.room.status = 'PLAYING'
        self.room.current_round = 1
        self.room.czar_id = czar.user.id
        self.room.current_question = first_question
        self.room.black_deck = list(black_cards)
        self.room.white_deck = list(white_cards)
        self.room.phase = 'SUBMISSION'
        self.room.round_expires_at = expiry
        self.room.last_round_winner_id = None
        self.room.last_round_winner_name = None
        self.room.last_round_winning_card = None
        self.room.last_round_number = None
        self.room.save()

        # Clear any old submissions
        Submission.objects.filter(room=self.room).delete()

    def check_all_submitted(self):
        """
        Check if all non-czar players have submitted.
        Transition to PICKING phase if so.
        """
        players = self.room.players.filter(is_online=True)
        non_czar_count = players.exclude(user__id=self.room.czar_id).count()

        submission_count = Submission.objects.filter(
            room=self.room,
            round_number=self.room.current_round
        ).count()

        if submission_count >= non_czar_count and self.room.phase == 'SUBMISSION':
            self.room.phase = 'PICKING'
            self.room.round_expires_at = timezone.now() + timedelta(seconds=self.PICKING_TIME)
            self.room.save()

    @transaction.atomic
    def submit_card(self, player: Player, card_text: str):
        """
        Handle card submission from a player.
        """
        if self.room.phase != 'SUBMISSION':
            raise ValueError("Not in submission phase")

        if str(player.user.id) == str(self.room.czar_id):
            raise ValueError("Czar cannot submit")

        if card_text not in player.hand:
            raise ValueError("Card not in hand")

        # Check if already submitted
        existing = Submission.objects.filter(
            room=self.room,
            player=player,
            round_number=self.room.current_round
        ).exists()

        if existing:
            raise ValueError("Already submitted this round")

        # Create submission
        Submission.objects.create(
            room=self.room,
            player=player,
            round_number=self.room.current_round,
            card_text=card_text
        )

        # Remove card from hand
        hand = player.hand
        hand.remove(card_text)
        player.hand = hand
        player.save()

        # Check if all submitted
        self.check_all_submitted()

    @transaction.atomic
    def pick_winner(self, winner_player_id: str):
        """
        Process winner selection by czar.
        Replaces pickWinner() in game.js
        """
        if self.room.phase == 'TRANSITIONING':
            return  # Already processing

        if self.room.phase == 'GAME_OVER':
            return

        try:
            winner = Player.objects.get(
                user__id=winner_player_id,
                room=self.room
            )
        except Player.DoesNotExist:
            raise ValueError("Winner not found")

        # Get winning submission
        try:
            submission = Submission.objects.get(
                room=self.room,
                player=winner,
                round_number=self.room.current_round
            )
            winning_card = submission.card_text
        except Submission.DoesNotExist:
            winning_card = "Unknown"

        # Update winner score
        winner.score += 1
        winner.save()

        # Store last round result
        self.room.last_round_winner_id = winner.user.id
        self.room.last_round_winner_name = winner.name
        self.room.last_round_winning_card = winning_card
        self.room.last_round_number = self.room.current_round

        # Check game over
        if self.room.max_rounds and self.room.current_round >= self.room.max_rounds:
            self.room.status = 'GAME_OVER'
            self.room.phase = 'GAME_OVER'
            self.room.save()
            return

        # Prepare next round
        self._advance_round()

    def _advance_round(self):
        """Prepare next round."""
        players = list(self.room.players.filter(is_online=True))

        # Rotate czar
        current_czar_index = next(
            (i for i, p in enumerate(players) if str(p.user.id) == str(self.room.czar_id)),
            0
        )
        next_czar = players[(current_czar_index + 1) % len(players)]

        # Draw next black card
        black_deck = list(self.room.black_deck)
        next_question = black_deck.pop() if black_deck else "Out of questions!"

        # Replenish hands
        white_deck = list(self.room.white_deck)
        for player in players:
            hand = list(player.hand)
            while len(hand) < self.INITIAL_HAND_SIZE and white_deck:
                hand.append(white_deck.pop())
            player.hand = hand
            player.save()

        # Update room
        self.room.current_round += 1
        self.room.czar_id = next_czar.user.id
        self.room.current_question = next_question
        self.room.black_deck = black_deck
        self.room.white_deck = white_deck
        self.room.phase = 'SUBMISSION'
        self.room.round_expires_at = timezone.now() + timedelta(seconds=self.SUBMISSION_TIME)
        self.room.save()

        # Clear submissions for new round
        Submission.objects.filter(
            room=self.room,
            round_number__lt=self.room.current_round
        ).delete()

    @transaction.atomic
    def handle_timeout(self):
        """
        Handle round timeout - auto-submit/auto-pick.
        Replaces handleRoundTimeout() in game.js
        """
        if self.room.phase == 'TRANSITIONING' or self.room.status == 'GAME_OVER':
            return

        # Check if time actually expired
        if self.room.round_expires_at and timezone.now() < self.room.round_expires_at:
            return

        players = list(self.room.players.filter(is_online=True))
        czar_id = self.room.czar_id
        submission_count = Submission.objects.filter(
            room=self.room,
            round_number=self.room.current_round
        ).count()
        players_count = len(players)

        # Phase 1: SUBMISSION - If not everyone (minus czar) has submitted
        if self.room.phase == 'SUBMISSION' and submission_count < players_count - 1:
            # Auto-submit for players who haven't
            for player in players:
                if str(player.user.id) == str(czar_id):
                    continue

                existing = Submission.objects.filter(
                    room=self.room,
                    player=player,
                    round_number=self.room.current_round
                ).exists()

                if not existing and player.hand:
                    random_card = random.choice(player.hand)
                    Submission.objects.create(
                        room=self.room,
                        player=player,
                        round_number=self.room.current_round,
                        card_text=random_card
                    )

                    hand = list(player.hand)
                    hand.remove(random_card)
                    player.hand = hand
                    player.save()

            # Transition to PICKING phase
            self.room.phase = 'PICKING'
            self.room.round_expires_at = timezone.now() + timedelta(seconds=self.PICKING_TIME)
            self.room.save()
            return

        # Phase 2: PICKING - Everyone submitted, but Czar hasn't picked
        if self.room.phase == 'PICKING':
            submissions = list(Submission.objects.filter(
                room=self.room,
                round_number=self.room.current_round
            ))

            if submissions:
                random_winner = random.choice(submissions)
                self.pick_winner(str(random_winner.player.user.id))
