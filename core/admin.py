"""
Django admin configuration for CardsNChaos.
"""

from django.contrib import admin
from .models import AnonymousUser, Pack, Card, Room, Player, Submission


@admin.register(AnonymousUser)
class AnonymousUserAdmin(admin.ModelAdmin):
    list_display = ['id', 'session_key', 'created_at', 'last_seen']
    search_fields = ['id', 'session_key']
    readonly_fields = ['id', 'created_at', 'last_seen']


@admin.register(Pack)
class PackAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'enabled', 'card_count', 'created_at']
    list_filter = ['enabled']
    search_fields = ['id', 'name']

    def card_count(self, obj):
        return obj.cards.count()
    card_count.short_description = 'Cards'


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ['id', 'text_preview', 'card_type', 'pack', 'created_at']
    list_filter = ['card_type', 'pack']
    search_fields = ['text']

    def text_preview(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Text'


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['room_code', 'host', 'status', 'phase', 'current_round', 'player_count', 'created_at']
    list_filter = ['status', 'phase']
    search_fields = ['room_code']
    readonly_fields = ['room_code', 'created_at']

    def player_count(self, obj):
        return obj.players.count()
    player_count.short_description = 'Players'


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ['name', 'room', 'score', 'is_host', 'is_online', 'joined_at']
    list_filter = ['is_host', 'is_online', 'room']
    search_fields = ['name', 'room__room_code']


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ['player', 'room', 'round_number', 'card_text_preview', 'submitted_at']
    list_filter = ['room', 'round_number']
    search_fields = ['card_text']

    def card_text_preview(self, obj):
        return obj.card_text[:30] + '...' if len(obj.card_text) > 30 else obj.card_text
    card_text_preview.short_description = 'Card'
