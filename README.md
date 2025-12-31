<div align="center">

# Cards & Chaos

### The Ultimate Online Multiplayer Party Card Game

[![React](https://img.shields.io/badge/React-19.2-61DAFB?style=for-the-badge&logo=react&logoColor=white)](https://react.dev/)
[![Django](https://img.shields.io/badge/Django-4.2-092E20?style=for-the-badge&logo=django&logoColor=white)](https://djangoproject.com/)
[![Vite](https://img.shields.io/badge/Vite-7.2-646CFF?style=for-the-badge&logo=vite&logoColor=white)](https://vitejs.dev/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-4.1-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org/)
[![WebSocket](https://img.shields.io/badge/WebSocket-Channels-FF6B6B?style=for-the-badge&logo=websocket&logoColor=white)](https://channels.readthedocs.io/)

**A Cards Against Humanity-style party game with real-time multiplayer, video call integration, and 6 unique card packs featuring 300+ cards.**

[Live Demo](#) | [Report Bug](https://github.com/khatri90/CardsNChaos/issues) | [Request Feature](https://github.com/khatri90/CardsNChaos/issues)

</div>

---

## Table of Contents

- [About The Project](#about-the-project)
- [Features](#features)
- [System Architecture](#system-architecture)
- [Game Flow](#game-flow)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Database Schema](#database-schema)
- [Getting Started](#getting-started)
- [API Reference](#api-reference)
- [WebSocket Events](#websocket-events)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)

---

## About The Project

**Cards & Chaos** is a full-stack, real-time multiplayer party card game designed for online social gaming. Players gather in virtual rooms, where a rotating "Card Czar" draws a question card and everyone else submits their funniest answer. The Czar picks the winner, points are awarded, and chaos ensues.

### Why Cards & Chaos?

- **No Login Required**: Jump straight into games with anonymous authentication
- **Real-Time Sync**: WebSocket-powered instant updates for all players
- **Video Integration**: Optional WebRTC video calls during gameplay
- **Multiple Card Packs**: 6 themed packs from family-friendly to adult humor
- **Modern Stack**: Built with React 19, Django 4.2, and Django Channels

---

## Features

| Category | Features |
|----------|----------|
| **Gameplay** | 3-8 players per room, rotating Czar system, 10-30 configurable rounds |
| **Card Packs** | Standard Chaos, After Dark (NSFW), Geek & Gamers, Desi Parents, Czech Republic, Family Friendly |
| **Real-Time** | WebSocket game state sync, live player status, instant score updates |
| **Video Calls** | Optional WebRTC video integration with mute/camera controls |
| **Host Controls** | Kick players, adjust settings, start/restart games |
| **UI/UX** | Dark/Light theme toggle, responsive design, smooth animations |
| **Admin** | Card pack management dashboard, bulk import/export |

---

## System Architecture

```mermaid
flowchart TB
    subgraph Client["Frontend (React + Vite)"]
        UI[React Components]
        WS_Client[WebSocket Client]
        API_Client[REST API Client]
        Video[WebRTC Video]
    end

    subgraph Server["Backend (Django + Channels)"]
        DRF[Django REST Framework]
        Channels[Django Channels]
        GameEngine[Game Logic Engine]
        VideoSignal[Video Signaling]
    end

    subgraph Database["Database Layer"]
        PostgreSQL[(PostgreSQL)]
        Sessions[(Session Store)]
    end

    subgraph External["External Services"]
        STUN[STUN/TURN Servers]
    end

    UI --> API_Client
    UI --> WS_Client
    UI --> Video

    API_Client -->|HTTP/REST| DRF
    WS_Client -->|WebSocket| Channels

    DRF --> GameEngine
    Channels --> GameEngine
    GameEngine --> PostgreSQL

    DRF --> Sessions
    Channels --> Sessions

    Video -->|Signaling| VideoSignal
    VideoSignal --> Channels
    Video <-->|P2P| STUN
```

### Architecture Highlights

| Component | Technology | Purpose |
|-----------|------------|---------|
| **API Layer** | Django REST Framework | CRUD operations, game actions, authentication |
| **Real-Time Layer** | Django Channels + Daphne | WebSocket connections, game state broadcasts |
| **Game Engine** | Python (game_logic.py) | Card shuffling, round management, scoring |
| **Video Layer** | WebRTC + Custom Signaling | Peer-to-peer video calls with Django signaling |
| **Database** | PostgreSQL / SQLite | Game state, user sessions, card storage |

---

## Game Flow

```mermaid
flowchart LR
    subgraph Setup["Game Setup"]
        A[Landing Page] -->|Create Room| B[Host Creates Lobby]
        A -->|Enter Code| C[Player Joins Room]
        B --> D[Lobby - Waiting]
        C --> D
    end

    subgraph Game["Game Loop"]
        D -->|Host Starts| E[Round Begins]
        E --> F[Czar Draws Black Card]
        F --> G[Players Submit White Cards]
        G -->|60s Timer| H{All Submitted?}
        H -->|Yes| I[Czar Reviews]
        H -->|Timeout| I
        I -->|30s Timer| J[Czar Picks Winner]
        J --> K[Points Awarded]
        K --> L{Max Rounds?}
        L -->|No| M[Rotate Czar]
        M --> F
    end

    subgraph End["Game End"]
        L -->|Yes| N[Final Leaderboard]
        N --> O[Game Over Screen]
        O -->|Play Again| A
    end
```

### Round Phases

```mermaid
stateDiagram-v2
    [*] --> WAITING: Room Created
    WAITING --> SUBMISSION: Game Started
    SUBMISSION --> PICKING: All Cards Submitted
    SUBMISSION --> PICKING: 60s Timeout
    PICKING --> TRANSITIONING: Winner Picked
    PICKING --> TRANSITIONING: 30s Timeout
    TRANSITIONING --> SUBMISSION: Next Round
    TRANSITIONING --> GAME_OVER: Max Rounds
    GAME_OVER --> [*]
```

---

## Tech Stack

### Backend

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.11+ | Runtime environment |
| Django | 4.2+ | Web framework |
| Django REST Framework | 3.14+ | REST API |
| Django Channels | 4.0+ | WebSocket support |
| Daphne | 4.0+ | ASGI server |
| PostgreSQL | 16+ | Production database |
| WhiteNoise | 6.6+ | Static file serving |

### Frontend

| Technology | Version | Purpose |
|------------|---------|---------|
| React | 19.2 | UI framework |
| Vite | 7.2 | Build tool & dev server |
| Tailwind CSS | 4.1 | Utility-first styling |
| Framer Motion | 12.23 | Animations |
| React Router | 7.10 | Client-side routing |
| Lucide React | 0.559 | Icon library |

### Infrastructure

| Technology | Purpose |
|------------|---------|
| Docker | Backend containerization |
| Vercel | Frontend hosting |
| Railway / DeployRA | Backend hosting |
| PostgreSQL (Aiven) | Managed database |

---

## Project Structure

```
CardsNChaos/
├── backend/                      # Django REST API
│   ├── cardsnchaos/             # Django project settings
│   │   ├── settings.py          # Configuration
│   │   ├── urls.py              # Root URL routing
│   │   ├── asgi.py              # ASGI config (WebSocket)
│   │   └── routing.py           # WebSocket routes
│   ├── core/                    # Main application
│   │   ├── models.py            # 8 database models
│   │   ├── views.py             # 20+ API endpoints
│   │   ├── serializers.py       # DRF serializers
│   │   ├── consumers.py         # WebSocket consumers
│   │   ├── game_logic.py        # Game engine
│   │   ├── authentication.py    # Anonymous auth
│   │   ├── video_views.py       # Video call API
│   │   └── video_consumer.py    # Video WebSocket
│   ├── requirements.txt         # Python dependencies
│   ├── Dockerfile               # Container config
│   └── README.md                # Backend documentation
│
├── CardsNChaos/                 # React Frontend
│   ├── src/
│   │   ├── pages/               # 9 page components
│   │   ├── components/          # Reusable UI components
│   │   │   ├── ui/              # Base components
│   │   │   └── video/           # Video call components
│   │   ├── services/            # API service layer
│   │   ├── hooks/               # Custom React hooks
│   │   └── lib/                 # Utilities & config
│   ├── package.json             # Node dependencies
│   ├── vite.config.js           # Vite configuration
│   └── README.md                # Frontend documentation
│
└── README.md                    # This file
```

---

## Database Schema

```mermaid
erDiagram
    AnonymousUser ||--o{ Player : "has"
    AnonymousUser {
        UUID id PK
        string session_key UK
        datetime created_at
        datetime last_seen
    }

    Pack ||--o{ Card : "contains"
    Pack ||--o{ Room : "used_by"
    Pack {
        string id PK
        string name
        text description
        boolean enabled
    }

    Card {
        UUID id PK
        text text
        string card_type
        string pack_id FK
    }

    Room ||--o{ Player : "has"
    Room ||--o{ Submission : "has"
    Room ||--o{ VideoCallParticipant : "has"
    Room {
        string room_code PK
        UUID host_id FK
        string status
        string pack_id FK
        int max_rounds
        int current_round
        UUID czar_id
        text current_question
        string phase
        json black_deck
        json white_deck
    }

    Player ||--o{ Submission : "makes"
    Player ||--o{ VideoCallParticipant : "has"
    Player {
        UUID id PK
        UUID user_id FK
        string room_code FK
        string name
        string avatar
        int score
        boolean is_host
        boolean is_online
        json hand
    }

    Submission {
        UUID id PK
        string room_code FK
        UUID player_id FK
        int round_number
        text card_text
    }

    VideoCallParticipant ||--o{ VideoCallSignal : "sends"
    VideoCallParticipant {
        UUID id PK
        string room_code FK
        UUID player_id FK
        boolean video_enabled
        boolean audio_enabled
        boolean is_connected
    }

    VideoCallSignal {
        UUID id PK
        string room_code FK
        UUID from_player_id FK
        UUID to_player_id FK
        string signal_type
        json signal_data
        boolean delivered
    }
```

---

## Getting Started

### Prerequisites

- **Node.js** >= 18.0
- **Python** >= 3.11
- **PostgreSQL** >= 14 (production) or SQLite (development)

### Quick Start (Development)

#### 1. Clone the Repository

```bash
git clone https://github.com/khatri90/CardsNChaos.git
cd CardsNChaos
```

#### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Seed card database
python manage.py seed_cards

# Start server (WebSocket enabled)
daphne -b 127.0.0.1 -p 8000 cardsnchaos.asgi:application
```

#### 3. Frontend Setup

```bash
cd CardsNChaos

# Install dependencies
npm install

# Create environment file
cp .env.example .env

# Edit .env with your backend URL
# VITE_API_URL=http://localhost:8000/api
# VITE_WS_URL=ws://localhost:8000/ws

# Start development server
npm run dev
```

#### 4. Open in Browser

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000/api
- **Django Admin**: http://localhost:8000/admin

---

## API Reference

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/anonymous/` | Create/recover anonymous session |
| `GET` | `/api/auth/session/` | Check current session status |

### Room Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/rooms/` | Create new game room |
| `GET` | `/api/rooms/{code}/` | Get room details |
| `POST` | `/api/rooms/{code}/join/` | Join existing room |
| `POST` | `/api/rooms/{code}/leave/` | Leave room |
| `POST` | `/api/rooms/{code}/start/` | Start game (host only) |
| `PATCH` | `/api/rooms/{code}/settings/` | Update room settings |

### Game Actions

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/rooms/{code}/submit/` | Submit white card answer |
| `POST` | `/api/rooms/{code}/pick-winner/` | Czar selects winning card |
| `POST` | `/api/rooms/{code}/timeout/` | Handle round timeout |

### Video Calls

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/rooms/{code}/video/join/` | Join video call |
| `POST` | `/api/rooms/{code}/video/leave/` | Leave video call |
| `GET` | `/api/rooms/{code}/video/participants/` | List video participants |
| `POST` | `/api/rooms/{code}/video/signals/` | Send WebRTC signal |

### Card Management (Admin)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/packs/` | List all card packs |
| `POST` | `/api/packs/` | Create new pack |
| `GET` | `/api/cards/?pack_id={id}` | List cards by pack |
| `POST` | `/api/cards/` | Add new card |
| `DELETE` | `/api/cards/{id}/` | Delete card |

---

## WebSocket Events

### Room Updates

**Endpoint**: `ws://{host}/ws/room/{room_code}/`

#### Received Messages

```json
{
  "type": "room_state",
  "action": "update | game_started | winner_picked",
  "data": {
    "room_code": "ABCD",
    "status": "PLAYING",
    "phase": "SUBMISSION",
    "current_round": 3,
    "current_question": "What's the secret to a happy life?",
    "czar_id": "uuid-here",
    "players": [...],
    "submissions": [...]
  }
}
```

#### Client Messages

```json
{"action": "ping"}       // Health check
{"action": "heartbeat"}  // Keep alive
```

### Video Signaling

**Endpoint**: `ws://{host}/ws/video/{room_code}/`

#### Signal Types

| Type | Description |
|------|-------------|
| `offer` | WebRTC SDP offer |
| `answer` | WebRTC SDP answer |
| `ice_candidate` | ICE candidate for NAT traversal |
| `renegotiate` | Request connection renegotiation |

---

## Deployment

### Backend (Docker)

```bash
cd backend

# Build image
docker build -t cardsnchaos-backend .

# Run container
docker run -d \
  -p 8000:8000 \
  -e DEBUG=False \
  -e DJANGO_SECRET_KEY=your-secret-key \
  -e DATABASE_URL=postgresql://user:pass@host/db \
  -e ALLOWED_HOSTS=yourdomain.com \
  -e CORS_ALLOWED_ORIGINS=https://frontend.com \
  cardsnchaos-backend
```

### Frontend (Vercel)

```bash
cd CardsNChaos

# Build for production
npm run build

# Deploy to Vercel
vercel --prod
```

### Environment Variables

#### Backend

| Variable | Description | Example |
|----------|-------------|---------|
| `DEBUG` | Debug mode | `False` |
| `DJANGO_SECRET_KEY` | Secret key | `your-secure-key` |
| `DATABASE_URL` | PostgreSQL URL | `postgresql://...` |
| `ALLOWED_HOSTS` | Allowed domains | `api.example.com` |
| `CORS_ALLOWED_ORIGINS` | Frontend URL | `https://example.com` |
| `CSRF_TRUSTED_ORIGINS` | CSRF origins | `https://api.example.com` |

#### Frontend

| Variable | Description | Example |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API URL | `https://api.example.com/api` |
| `VITE_WS_URL` | WebSocket URL | `wss://api.example.com/ws` |

---

## Card Packs

| Pack | Description | Black Cards | White Cards |
|------|-------------|-------------|-------------|
| **Standard Chaos** | Classic adult humor | 41 | 73 |
| **After Dark** | NSFW content | 24 | 80 |
| **Geek & Gamers** | Gaming & tech references | 10 | 13 |
| **Desi Parents** | South Asian culture | 8 | 11 |
| **Czech Republic** | Czech humor | 20 | 31 |
| **Family Friendly** | All-ages fun | 20 | 30 |

**Total**: 123 Black Cards + 238 White Cards = **361 Cards**

---

## Contributing

Contributions are welcome! Please follow these steps:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/AmazingFeature`)
3. **Commit** your changes (`git commit -m 'Add AmazingFeature'`)
4. **Push** to the branch (`git push origin feature/AmazingFeature`)
5. **Open** a Pull Request

### Development Guidelines

- Follow existing code style and patterns
- Write tests for new features
- Update documentation as needed
- Keep commits atomic and descriptive

---

## License

Distributed under the MIT License. See `LICENSE` for more information.

---

<div align="center">

**Built with love by the Cards & Chaos Team**

[Report a Bug](https://github.com/khatri90/CardsNChaos/issues) | [Request a Feature](https://github.com/khatri90/CardsNChaos/issues)

</div>
