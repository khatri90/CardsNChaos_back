"""
Custom authentication for anonymous sessions.
Replaces Firebase Anonymous Auth.
"""

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .models import AnonymousUser


class AnonymousSessionAuthentication(BaseAuthentication):
    """
    Custom authentication that creates/retrieves anonymous users
    based on session keys or explicit user ID header.

    Priority:
    1. X-User-ID header (set by frontend after ensureAuth)
    2. Session-based lookup (fallback)
    """

    def authenticate(self, request):
        # First, check for explicit user ID header (from frontend after ensureAuth)
        user_id = request.headers.get('X-User-ID')

        if user_id:
            try:
                user = AnonymousUser.objects.get(id=user_id)
                return (user, None)
            except AnonymousUser.DoesNotExist:
                # User ID was invalid, fall through to session-based auth
                pass

        # Fallback: session-based authentication
        if not request.session.session_key:
            request.session.create()

        session_key = request.session.session_key

        try:
            user, created = AnonymousUser.objects.get_or_create(
                session_key=session_key
            )
            return (user, None)
        except Exception as e:
            raise AuthenticationFailed(f'Authentication failed: {str(e)}')
