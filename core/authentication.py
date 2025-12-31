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
    based on session keys. Replaces Firebase Anonymous Auth.
    """

    def authenticate(self, request):
        # Ensure session exists
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
