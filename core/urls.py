"""
URL patterns for core API.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import video_views

router = DefaultRouter()
router.register(r'packs', views.PackViewSet, basename='pack')
router.register(r'cards', views.CardViewSet, basename='card')

urlpatterns = [
    # Authentication
    path('auth/anonymous/', views.AnonymousAuthView.as_view(), name='anonymous-auth'),
    path('auth/session/', views.SessionStatusView.as_view(), name='session-status'),

    # Room Management
    path('rooms/', views.RoomListCreateView.as_view(), name='room-list-create'),
    path('rooms/<str:room_code>/', views.RoomDetailView.as_view(), name='room-detail'),
    path('rooms/<str:room_code>/join/', views.JoinRoomView.as_view(), name='room-join'),
    path('rooms/<str:room_code>/leave/', views.LeaveRoomView.as_view(), name='room-leave'),
    path('rooms/<str:room_code>/start/', views.StartGameView.as_view(), name='room-start'),
    path('rooms/<str:room_code>/settings/', views.UpdateRoomSettingsView.as_view(), name='room-settings'),

    # Game Actions
    path('rooms/<str:room_code>/submit/', views.SubmitCardView.as_view(), name='submit-card'),
    path('rooms/<str:room_code>/pick-winner/', views.PickWinnerView.as_view(), name='pick-winner'),
    path('rooms/<str:room_code>/timeout/', views.HandleTimeoutView.as_view(), name='handle-timeout'),

    # Video Call Endpoints
    path('rooms/<str:room_code>/video/participants/', video_views.VideoCallParticipantsView.as_view(), name='video-participants'),
    path('rooms/<str:room_code>/video/join/', video_views.VideoCallJoinView.as_view(), name='video-join'),
    path('rooms/<str:room_code>/video/leave/', video_views.VideoCallLeaveView.as_view(), name='video-leave'),
    path('rooms/<str:room_code>/video/media-state/', video_views.VideoCallMediaStateView.as_view(), name='video-media-state'),
    path('rooms/<str:room_code>/video/signals/', video_views.VideoCallSignalView.as_view(), name='video-signals'),
    path('rooms/<str:room_code>/video/cleanup/', video_views.VideoCallCleanupView.as_view(), name='video-cleanup'),

    # Video Call Configuration
    path('video/ice-servers/', video_views.VideoCallICEServersView.as_view(), name='video-ice-servers'),
    path('video/cleanup/', video_views.VideoCallCleanupView.as_view(), name='video-cleanup-all'),

    # Admin
    path('admin/sync/', views.SyncDatabaseView.as_view(), name='admin-sync'),
    path('admin/import/', views.ImportCardsView.as_view(), name='admin-import'),

    # Router URLs
    path('', include(router.urls)),
]
