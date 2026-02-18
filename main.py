from fastapi import FastAPI, Depends, HTTPException, status, Query, WebSocket, WebSocketDisconnect, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
import asyncio
import json
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
import secrets
import string
from datetime import datetime

from database import (
    get_db, init_db, User, Movie, Swipe, Match, FriendRequest,
    Friendship, StreamingService, MovieStreamingService, WatchSession,
    SwipeDirection
)
from tmdb_sync import sync_movie_from_tmdb, sync_movie_by_title, sync_popular_movies
from models import (
    UserCreate, UserResponse, FriendRequestCreate, FriendRequestResponse,
    FriendshipResponse, MovieResponse, SwipeCreate, SwipeResponse,
    MatchResponse, WatchSessionCreate, WatchSessionResponse, MovieFilter,
    StreamingServiceResponse
)

app = FastAPI(title="Movie Tinder API", version="1.0.0")

# Initialize database
init_db()

# Mount static files for frontend
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.on_event("startup")
async def store_event_loop():
    app.state.loop = asyncio.get_running_loop()


# WebSocket connection manager for real-time notifications
class ConnectionManager:
    def __init__(self):
        self._connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, username: str) -> None:
        await websocket.accept()
        self._connections[username] = websocket

    def disconnect(self, username: str) -> None:
        self._connections.pop(username, None)

    async def send_personal(self, username: str, message: dict) -> None:
        ws = self._connections.get(username)
        if ws:
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                self.disconnect(username)


connection_manager = ConnectionManager()


async def notify_new_match(
    user1_username: str,
    user2_username: str,
    match_id: int,
    movie_title: str,
) -> None:
    """Send new_match notification to both users (each sees the other as friend)."""
    await connection_manager.send_personal(
        user1_username,
        {"type": "new_match", "match_id": match_id, "movie_title": movie_title, "friend_username": user2_username},
    )
    await connection_manager.send_personal(
        user2_username,
        {"type": "new_match", "match_id": match_id, "movie_title": movie_title, "friend_username": user1_username},
    )


# Helper function to generate invite code
def generate_invite_code(length=8):
    characters = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))


# Helper function to get user by username
def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()


# Helper function to get user by invite code
def get_user_by_invite_code(db: Session, invite_code: str):
    return db.query(User).filter(User.invite_code == invite_code).first()


# Helper function to check if users are friends
def are_friends(db: Session, user1_id: int, user2_id: int) -> bool:
    friendship = db.query(Friendship).filter(
        or_(
            and_(Friendship.user1_id == user1_id, Friendship.user2_id == user2_id),
            and_(Friendship.user1_id == user2_id, Friendship.user2_id == user1_id)
        )
    ).first()
    return friendship is not None


# USER ENDPOINTS
@app.post("/api/users/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # Check if username already exists
    if get_user_by_username(db, user.username):
        raise HTTPException(status_code=400, detail="Username already taken")
    
    # Generate unique invite code
    invite_code = generate_invite_code()
    while get_user_by_invite_code(db, invite_code):
        invite_code = generate_invite_code()
    
    db_user = User(username=user.username, invite_code=invite_code)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.get("/api/users/{username}", response_model=UserResponse)
def get_user(username: str, db: Session = Depends(get_db)):
    user = get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.get("/api/users/", response_model=List[UserResponse])
def list_users(db: Session = Depends(get_db)):
    return db.query(User).all()


# FRIEND ENDPOINTS
@app.post("/api/friends/request", response_model=FriendRequestResponse)
def send_friend_request(request: FriendRequestCreate, current_username: str = Query(...), db: Session = Depends(get_db)):
    current_user = get_user_by_username(db, current_username)
    if not current_user:
        raise HTTPException(status_code=404, detail="Current user not found")
    
    friend_user = get_user_by_invite_code(db, request.invite_code)
    if not friend_user:
        raise HTTPException(status_code=404, detail="Invalid invite code")
    
    if current_user.id == friend_user.id:
        raise HTTPException(status_code=400, detail="Cannot friend yourself")
    
    # Check if already friends
    if are_friends(db, current_user.id, friend_user.id):
        raise HTTPException(status_code=400, detail="Already friends")
    
    # Check if request already exists
    existing_request = db.query(FriendRequest).filter(
        or_(
            and_(FriendRequest.sender_id == current_user.id, FriendRequest.receiver_id == friend_user.id),
            and_(FriendRequest.sender_id == friend_user.id, FriendRequest.receiver_id == current_user.id)
        )
    ).first()
    
    if existing_request:
        if existing_request.status == "pending":
            raise HTTPException(status_code=400, detail="Friend request already pending")
        elif existing_request.status == "accepted":
            raise HTTPException(status_code=400, detail="Already friends")
    
    friend_request = FriendRequest(sender_id=current_user.id, receiver_id=friend_user.id)
    db.add(friend_request)
    db.commit()
    db.refresh(friend_request)
    
    # Load relationships
    db.refresh(friend_request)
    return friend_request


@app.post("/api/friends/accept/{request_id}")
def accept_friend_request(request_id: int, current_username: str, db: Session = Depends(get_db)):
    current_user = get_user_by_username(db, current_username)
    if not current_user:
        raise HTTPException(status_code=404, detail="Current user not found")
    
    friend_request = db.query(FriendRequest).filter(FriendRequest.id == request_id).first()
    if not friend_request:
        raise HTTPException(status_code=404, detail="Friend request not found")
    
    if friend_request.receiver_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to accept this request")
    
    if friend_request.status != "pending":
        raise HTTPException(status_code=400, detail="Request already processed")
    
    # Create friendship
    friendship = Friendship(
        user1_id=min(friend_request.sender_id, friend_request.receiver_id),
        user2_id=max(friend_request.sender_id, friend_request.receiver_id)
    )
    db.add(friendship)
    
    # Update request status
    friend_request.status = "accepted"
    db.commit()
    
    return {"message": "Friend request accepted"}


@app.get("/api/friends/", response_model=List[FriendshipResponse])
def get_friends(current_username: str = Query(...), db: Session = Depends(get_db)):
    current_user = get_user_by_username(db, current_username)
    if not current_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    friendships = db.query(Friendship).filter(
        or_(Friendship.user1_id == current_user.id, Friendship.user2_id == current_user.id)
    ).all()
    
    result = []
    for friendship in friendships:
        friend_id = friendship.user2_id if friendship.user1_id == current_user.id else friendship.user1_id
        friend = db.query(User).filter(User.id == friend_id).first()
        result.append({
            "id": friendship.id,
            "user1_id": friendship.user1_id,
            "user2_id": friendship.user2_id,
            "created_at": friendship.created_at,
            "friend": friend
        })
    
    return result


@app.get("/api/friends/requests", response_model=List[FriendRequestResponse])
def get_friend_requests(current_username: str, db: Session = Depends(get_db)):
    current_user = get_user_by_username(db, current_username)
    if not current_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    requests = db.query(FriendRequest).filter(
        FriendRequest.receiver_id == current_user.id,
        FriendRequest.status == "pending"
    ).all()
    
    return requests


# MOVIE ENDPOINTS
@app.get("/api/movies/", response_model=List[MovieResponse])
def get_movies(
    skip: int = 0,
    limit: int = 100,
    current_username: Optional[str] = Query(None),
    streaming_services: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Movie)
    
    # Filter by streaming services if provided
    if streaming_services:
        try:
            import json
            services_list = json.loads(streaming_services)
            if isinstance(services_list, list) and len(services_list) > 0:
                query = query.join(MovieStreamingService).join(StreamingService).filter(
                    StreamingService.name.in_(services_list)
                ).distinct()
        except:
            pass
    
    # Exclude movies user has already swiped on
    if current_username:
        current_user = get_user_by_username(db, current_username)
        if current_user:
            swiped_movie_ids = db.query(Swipe.movie_id).filter(Swipe.user_id == current_user.id).subquery()
            query = query.filter(~Movie.id.in_(swiped_movie_ids))
    
    movies = query.offset(skip).limit(limit).all()
    
    # Load streaming services for each movie
    result = []
    for movie in movies:
        streaming_services = db.query(StreamingService).join(MovieStreamingService).filter(
            MovieStreamingService.movie_id == movie.id
        ).all()
        movie_dict = {
            "id": movie.id,
            "title": movie.title,
            "genre": movie.genre,
            "rating": movie.rating,
            "description": movie.description,
            "poster_url": movie.poster_url,
            "release_year": movie.release_year,
            "imdb_rating": movie.imdb_rating,
            "streaming_services": streaming_services
        }
        result.append(movie_dict)
    
    return result


@app.get("/api/movies/{movie_id}", response_model=MovieResponse)
def get_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    streaming_services = db.query(StreamingService).join(MovieStreamingService).filter(
        MovieStreamingService.movie_id == movie.id
    ).all()
    
    return {
        "id": movie.id,
        "title": movie.title,
        "genre": movie.genre,
        "rating": movie.rating,
        "description": movie.description,
        "poster_url": movie.poster_url,
        "release_year": movie.release_year,
        "imdb_rating": movie.imdb_rating,
        "streaming_services": streaming_services
    }


# SWIPE ENDPOINTS
@app.post("/api/swipes/", response_model=SwipeResponse)
def create_swipe(
    swipe: SwipeCreate,
    current_username: str = Query(...),
    request: Request = None,
    db: Session = Depends(get_db),
):
    _app = request.app if request else None
    current_user = get_user_by_username(db, current_username)
    if not current_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if movie exists
    movie = db.query(Movie).filter(Movie.id == swipe.movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    # Check if user already swiped on this movie
    existing_swipe = db.query(Swipe).filter(
        Swipe.user_id == current_user.id,
        Swipe.movie_id == swipe.movie_id
    ).first()
    
    if existing_swipe:
        raise HTTPException(status_code=400, detail="Already swiped on this movie")
    
    db_swipe = Swipe(
        user_id=current_user.id,
        movie_id=swipe.movie_id,
        direction=swipe.direction
    )
    db.add(db_swipe)
    db.commit()
    db.refresh(db_swipe)
    
    # Check for matches if swiped right
    if swipe.direction == SwipeDirection.RIGHT:
        check_for_matches(db, current_user.id, swipe.movie_id, _app)
    
    return db_swipe


def check_for_matches(db: Session, user_id: int, movie_id: int, app=None):
    """Check if swiping right creates a match with any friend. Notifies both users via WebSocket if connected."""
    # Get all friends
    friendships = db.query(Friendship).filter(
        or_(Friendship.user1_id == user_id, Friendship.user2_id == user_id)
    ).all()
    
    friend_ids = []
    for friendship in friendships:
        friend_id = friendship.user2_id if friendship.user1_id == user_id else friendship.user1_id
        friend_ids.append(friend_id)
    
    # Check if any friend also swiped right on this movie
    for friend_id in friend_ids:
        friend_swipe = db.query(Swipe).filter(
            Swipe.user_id == friend_id,
            Swipe.movie_id == movie_id,
            Swipe.direction == SwipeDirection.RIGHT
        ).first()
        
        if friend_swipe:
            # Check if match already exists
            existing_match = db.query(Match).filter(
                or_(
                    and_(Match.user1_id == user_id, Match.user2_id == friend_id, Match.movie_id == movie_id),
                    and_(Match.user1_id == friend_id, Match.user2_id == user_id, Match.movie_id == movie_id)
                )
            ).first()
            
            if not existing_match:
                # Create match
                match = Match(
                    user1_id=min(user_id, friend_id),
                    user2_id=max(user_id, friend_id),
                    movie_id=movie_id
                )
                db.add(match)
                db.commit()
                db.refresh(match)
                movie_row = db.query(Movie).filter(Movie.id == movie_id).first()
                user1 = db.query(User).filter(User.id == match.user1_id).first()
                user2 = db.query(User).filter(User.id == match.user2_id).first()
                movie_title = movie_row.title if movie_row else ""

                # Notify both users in real time (best-effort, non-blocking)
                loop = getattr(getattr(app, "state", None), "loop", None) if app else None
                if loop and user1 and user2:
                    def _notify():
                        asyncio.ensure_future(
                            notify_new_match(
                                user1.username,
                                user2.username,
                                match.id,
                                movie_title,
                            ),
                            loop=loop,
                        )
                    loop.call_soon_threadsafe(_notify)


@app.get("/api/swipes/", response_model=List[SwipeResponse])
def get_swipes(current_username: str = Query(...), db: Session = Depends(get_db)):
    current_user = get_user_by_username(db, current_username)
    if not current_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return db.query(Swipe).filter(Swipe.user_id == current_user.id).all()


# MATCH ENDPOINTS
@app.get("/api/matches/", response_model=List[MatchResponse])
def get_matches(current_username: str = Query(...), db: Session = Depends(get_db)):
    current_user = get_user_by_username(db, current_username)
    if not current_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    matches = db.query(Match).filter(
        or_(Match.user1_id == current_user.id, Match.user2_id == current_user.id)
    ).all()
    
    result = []
    for match in matches:
        friend_id = match.user2_id if match.user1_id == current_user.id else match.user1_id
        friend = db.query(User).filter(User.id == friend_id).first()
        movie = db.query(Movie).filter(Movie.id == match.movie_id).first()
        streaming_services = db.query(StreamingService).join(MovieStreamingService).filter(
            MovieStreamingService.movie_id == match.movie_id
        ).all()
        
        result.append({
            "id": match.id,
            "user1_id": match.user1_id,
            "user2_id": match.user2_id,
            "movie_id": match.movie_id,
            "notified_user1": match.notified_user1,
            "notified_user2": match.notified_user2,
            "created_at": match.created_at,
            "movie": {
                **movie.__dict__,
                "streaming_services": streaming_services
            },
            "friend": friend
        })
    
    return result


@app.post("/api/matches/{match_id}/notify")
def mark_match_notified(match_id: int, current_username: str = Query(...), db: Session = Depends(get_db)):
    current_user = get_user_by_username(db, current_username)
    if not current_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    
    if match.user1_id == current_user.id:
        match.notified_user1 = True
    elif match.user2_id == current_user.id:
        match.notified_user2 = True
    else:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db.commit()
    return {"message": "Match notification marked as read"}


# WATCH SESSION ENDPOINTS
@app.post("/api/watch-sessions/", response_model=WatchSessionResponse)
def create_watch_session(session: WatchSessionCreate, current_username: str, db: Session = Depends(get_db)):
    current_user = get_user_by_username(db, current_username)
    if not current_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    friend = db.query(User).filter(User.id == session.friend_id).first()
    if not friend:
        raise HTTPException(status_code=404, detail="Friend not found")
    
    if not are_friends(db, current_user.id, session.friend_id):
        raise HTTPException(status_code=400, detail="Users are not friends")
    
    watch_session = WatchSession(
        user1_id=min(current_user.id, session.friend_id),
        user2_id=max(current_user.id, session.friend_id)
    )
    db.add(watch_session)
    db.commit()
    db.refresh(watch_session)
    
    friend_id = watch_session.user2_id if watch_session.user1_id == current_user.id else watch_session.user1_id
    friend_user = db.query(User).filter(User.id == friend_id).first()
    
    return {
        "id": watch_session.id,
        "user1_id": watch_session.user1_id,
        "user2_id": watch_session.user2_id,
        "created_at": watch_session.created_at,
        "friend": friend_user
    }


@app.get("/api/watch-sessions/", response_model=List[WatchSessionResponse])
def get_watch_sessions(current_username: str = Query(...), db: Session = Depends(get_db)):
    current_user = get_user_by_username(db, current_username)
    if not current_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    sessions = db.query(WatchSession).filter(
        or_(WatchSession.user1_id == current_user.id, WatchSession.user2_id == current_user.id)
    ).all()
    
    result = []
    for session in sessions:
        friend_id = session.user2_id if session.user1_id == current_user.id else session.user1_id
        friend = db.query(User).filter(User.id == friend_id).first()
        result.append({
            "id": session.id,
            "user1_id": session.user1_id,
            "user2_id": session.user2_id,
            "created_at": session.created_at,
            "friend": friend
        })
    
    return result


# STREAMING SERVICES ENDPOINTS
@app.get("/api/streaming-services/", response_model=List[StreamingServiceResponse])
def get_streaming_services(db: Session = Depends(get_db)):
    return db.query(StreamingService).all()


# ADMIN - TMDB sync (seed/refresh movie and streaming availability)
@app.post("/admin/sync-movie/{movie_id}")
def admin_sync_movie(movie_id: int, db: Session = Depends(get_db)):
    if not sync_movie_from_tmdb(db, movie_id):
        raise HTTPException(status_code=404, detail="Movie not found or TMDB sync failed")
    return {"message": "Synced", "movie_id": movie_id}


@app.post("/admin/sync-movie-by-title")
def admin_sync_movie_by_title(
    title: str,
    year: Optional[int] = None,
    db: Session = Depends(get_db),
):
    movie = sync_movie_by_title(db, title, year)
    if not movie:
        raise HTTPException(status_code=404, detail="TMDB search failed or no results")
    return {"message": "Synced", "movie_id": movie.id, "title": movie.title}


@app.post("/api/load-more-movies")
def load_more_movies(page: int = 1, db: Session = Depends(get_db)):
    """Fetch a page of popular movies from TMDB and add new ones to the catalog."""
    added = sync_popular_movies(db, page)
    return {"added": added, "message": f"Added {added} new movies from TMDB."}


# WebSocket endpoint for real-time notifications
@app.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    await connection_manager.connect(websocket, username)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        connection_manager.disconnect(username)


# ROOT ENDPOINT - Serve frontend
@app.get("/", response_class=HTMLResponse)
def read_root():
    # Explicitly use UTF-8 so Windows default encoding (cp1252) doesn't break on special characters
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
