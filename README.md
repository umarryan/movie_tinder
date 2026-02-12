# Movie Tinder 🎬

A fun web application for friends to swipe through movies and find matches! Built with FastAPI and Uvicorn.

## Features

- **Account System**: Simple username-based authentication (no personal data required)
- **Friend System**: Send friend requests using invite codes
- **Movie Swiping**: Swipe right (interested) or left (not interested) on movies
- **Match System**: Get notified when you and a friend both swipe right on the same movie
- **Streaming Availability**: See which streaming services have each movie
- **Filtering**: Filter movies by streaming platform
- **Watch Sessions**: Create watch sessions with friends

## Setup

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Seed the database** (optional, adds sample movies):
```bash
python seed_db.py
```

3. **Run the application**:
```bash
uvicorn main:app --reload
```

Or:
```bash
python main.py
```

4. **Access the application**:
   - Open your browser and go to `http://localhost:8000`
   - The API documentation is available at `http://localhost:8000/docs`

## Usage

1. **Create an account**: Enter a username to login or register
2. **Add friends**: Share your invite code or use a friend's invite code to send a friend request
3. **Swipe movies**: Swipe right (♥) if interested, left (✕) if not
4. **View matches**: Check the Matches tab to see movies you and your friends both liked
5. **Filter movies**: Use the filter section to show only movies on specific streaming services

## API Endpoints

### Users
- `POST /api/users/` - Create a new user
- `GET /api/users/{username}` - Get user by username
- `GET /api/users/` - List all users

### Friends
- `POST /api/friends/request` - Send a friend request (requires `current_username` query param)
- `POST /api/friends/accept/{request_id}` - Accept a friend request
- `GET /api/friends/` - Get user's friends
- `GET /api/friends/requests` - Get pending friend requests

### Movies
- `GET /api/movies/` - Get movies (supports filtering and pagination)
- `GET /api/movies/{movie_id}` - Get movie details

### Swipes
- `POST /api/swipes/` - Create a swipe (requires `current_username` query param)
- `GET /api/swipes/` - Get user's swipes

### Matches
- `GET /api/matches/` - Get user's matches
- `POST /api/matches/{match_id}/notify` - Mark match as notified

### Watch Sessions
- `POST /api/watch-sessions/` - Create a watch session
- `GET /api/watch-sessions/` - Get user's watch sessions

### Streaming Services
- `GET /api/streaming-services/` - List all streaming services

## Database

The application uses SQLite by default (`movie_tinder.db`). The database will be created automatically when you first run the application.

## Notes

- The frontend uses localStorage to persist the current user session
- All API endpoints that require authentication use a `current_username` query parameter
- Matches are automatically created when two friends both swipe right on the same movie
- The seed script includes 15 popular movies with streaming availability data

## Future Enhancements

- Real-time notifications using WebSockets
- Integration with actual streaming API (e.g., JustWatch API)
- Movie recommendations based on swipe history
- Group watch sessions with multiple friends
- Movie reviews and ratings
