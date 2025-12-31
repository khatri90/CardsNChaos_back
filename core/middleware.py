"""
WebSocket authentication middleware.
"""

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from urllib.parse import parse_qs
from django.contrib.sessions.models import Session
from .models import AnonymousUser


class WebSocketAuthMiddleware(BaseMiddleware):
    """
    WebSocket middleware to authenticate anonymous users via session cookie
    or query parameter (for cross-origin WebSocket connections).
    """

    async def __call__(self, scope, receive, send):
        session_key = None
        user_id = None

        # Try to get session from cookies first
        headers = dict(scope.get('headers', []))
        cookie_header = headers.get(b'cookie', b'').decode()

        if cookie_header:
            cookies = {}
            for item in cookie_header.split('; '):
                if '=' in item:
                    key, value = item.split('=', 1)
                    cookies[key] = value
            session_key = cookies.get('sessionid')

        # Fallback: try query parameters for cross-origin WebSocket
        if not session_key:
            query_string = scope.get('query_string', b'').decode()
            query_params = parse_qs(query_string)
            # Support both session_key and user_id params
            if 'session_key' in query_params:
                session_key = query_params['session_key'][0]
            elif 'user_id' in query_params:
                user_id = query_params['user_id'][0]

        if session_key:
            scope['user'] = await self.get_user_by_session(session_key)
        elif user_id:
            scope['user'] = await self.get_user_by_id(user_id)
        else:
            scope['user'] = None

        return await super().__call__(scope, receive, send)

    @database_sync_to_async
    def get_user_by_session(self, session_key):
        try:
            return AnonymousUser.objects.get(session_key=session_key)
        except AnonymousUser.DoesNotExist:
            return None

    @database_sync_to_async
    def get_user_by_id(self, user_id):
        try:
            return AnonymousUser.objects.get(id=user_id)
        except AnonymousUser.DoesNotExist:
            return None
