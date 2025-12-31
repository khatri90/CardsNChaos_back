# CardsNChaos Backend

Django REST API backend for the CardsNChaos card game.

## Features

- **REST API**: Full game management endpoints
- **WebSocket**: Real-time game state updates via Django Channels
- **Anonymous Auth**: Session-based anonymous user authentication
- **Card Packs**: 6 pre-loaded card packs with 300+ cards
- **Game Logic**: Complete game engine with timeout handling

## Quick Start

### 1. Create Virtual Environment

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run Migrations

```bash
python manage.py migrate
```

### 4. Seed Database with Cards

```bash
python manage.py seed_cards
```

### 5. Run Development Server

```bash
# Using Daphne (recommended for WebSocket support)
daphne -b 127.0.0.1 -p 8000 cardsnchaos.asgi:application

# Or using Django's runserver (HTTP only, no WebSocket)
python manage.py runserver
```

The API will be available at `http://localhost:8000/api/`

## API Endpoints

### Authentication
- `POST /api/auth/anonymous/` - Create anonymous session
- `GET /api/auth/session/` - Get current session status

### Rooms
- `POST /api/rooms/` - Create a new room
- `GET /api/rooms/<code>/` - Get room details
- `POST /api/rooms/<code>/join/` - Join a room
- `POST /api/rooms/<code>/leave/` - Leave a room
- `POST /api/rooms/<code>/start/` - Start the game (host only)
- `PATCH /api/rooms/<code>/settings/` - Update room settings

### Game Actions
- `POST /api/rooms/<code>/submit/` - Submit a white card
- `POST /api/rooms/<code>/pick-winner/` - Czar picks winner
- `POST /api/rooms/<code>/timeout/` - Handle round timeout

### Card Packs (Admin)
- `GET /api/packs/` - List all packs
- `POST /api/packs/` - Create a pack
- `GET /api/packs/<id>/` - Get pack details
- `DELETE /api/packs/<id>/` - Delete a pack
- `PATCH /api/packs/<id>/toggle/` - Toggle pack enabled status

### Cards (Admin)
- `GET /api/cards/` - List cards (filter with `?pack_id=` or `?type=`)
- `POST /api/cards/` - Add a card
- `DELETE /api/cards/<id>/` - Delete a card

### Admin
- `POST /api/admin/sync/` - Sync database with seed data
- `POST /api/admin/import/` - Bulk import cards from JSON

## WebSocket

Connect to receive real-time room updates:

```
ws://localhost:8000/ws/room/<room_code>/
```

### Messages Received
```json
{
  "type": "room_state",
  "data": { /* full room state */ },
  "action": "update|game_started|winner_picked"
}
```

### Messages to Send
```json
{"action": "ping"}      // Receive pong response
{"action": "heartbeat"} // Keep connection alive
```

## Project Structure

```
backend/
├── manage.py
├── requirements.txt
├── cardsnchaos/          # Django project
│   ├── settings.py       # Configuration
│   ├── urls.py           # Root URL config
│   ├── asgi.py           # ASGI config for WebSocket
│   └── routing.py        # WebSocket URL routing
└── core/                 # Main Django app
    ├── models.py         # Database models
    ├── views.py          # API views
    ├── urls.py           # API URL patterns
    ├── serializers.py    # DRF serializers
    ├── consumers.py      # WebSocket consumers
    ├── game_logic.py     # Game engine
    ├── authentication.py # Custom auth
    └── management/commands/
        └── seed_cards.py # Database seeder
```

## Environment Variables

For production, set these environment variables:

- `DJANGO_SECRET_KEY` - Secret key for Django
- `DEBUG` - Set to `False` in production
- `ALLOWED_HOSTS` - Comma-separated list of allowed hosts

## Card Packs Included

1. **Standard Chaos** - Classic experience (41 black, 73 white)
2. **After Dark** - NSFW content (24 black, 80 white)
3. **Geek & Gamers** - Gaming references (10 black, 13 white)
4. **Desi Parents** - South Asian humor (8 black, 11 white)
5. **Czech Republic** - Czech culture (20 black, 31 white)
6. **Chaos (Family Friendly)** - Simple jokes (20 black, 30 white)

## Development

### Create Superuser (optional)

```bash
python manage.py createsuperuser
```

Then access Django admin at `http://localhost:8000/admin/`

### Run Tests

```bash
python manage.py test
```
"# CardsNChaos_back" 
