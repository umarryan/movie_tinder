from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import enum

SQLALCHEMY_DATABASE_URL = "sqlite:///./movie_tinder.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class SwipeDirection(enum.Enum):
    LEFT = "left"
    RIGHT = "right"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    invite_code = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    sent_friend_requests = relationship("FriendRequest", foreign_keys="FriendRequest.sender_id", back_populates="sender")
    received_friend_requests = relationship("FriendRequest", foreign_keys="FriendRequest.receiver_id", back_populates="receiver")
    friendships_as_user1 = relationship("Friendship", foreign_keys="Friendship.user1_id", back_populates="user1")
    friendships_as_user2 = relationship("Friendship", foreign_keys="Friendship.user2_id", back_populates="user2")
    swipes = relationship("Swipe", back_populates="user")
    matches = relationship("Match", back_populates="user1", foreign_keys="Match.user1_id")
    matches_as_user2 = relationship("Match", back_populates="user2", foreign_keys="Match.user2_id")
    watch_sessions = relationship("WatchSession", back_populates="user1", foreign_keys="WatchSession.user1_id")
    watch_sessions_as_user2 = relationship("WatchSession", back_populates="user2", foreign_keys="WatchSession.user2_id")


class FriendRequest(Base):
    __tablename__ = "friend_requests"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String, default="pending")  # pending, accepted, rejected
    created_at = Column(DateTime, default=datetime.utcnow)

    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_friend_requests")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="received_friend_requests")


class Friendship(Base):
    __tablename__ = "friendships"

    id = Column(Integer, primary_key=True, index=True)
    user1_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user2_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user1 = relationship("User", foreign_keys=[user1_id], back_populates="friendships_as_user1")
    user2 = relationship("User", foreign_keys=[user2_id], back_populates="friendships_as_user2")


class Movie(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    genre = Column(String, nullable=False)
    rating = Column(String)  # e.g., "PG-13", "R", etc.
    description = Column(Text)
    poster_url = Column(String)
    release_year = Column(Integer)
    imdb_rating = Column(String)  # e.g., "8.5/10"
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    swipes = relationship("Swipe", back_populates="movie")
    matches = relationship("Match", back_populates="movie")
    streaming_services = relationship("MovieStreamingService", back_populates="movie")


class Swipe(Base):
    __tablename__ = "swipes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False)
    direction = Column(SQLEnum(SwipeDirection), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="swipes")
    movie = relationship("Movie", back_populates="swipes")


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    user1_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user2_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False)
    notified_user1 = Column(Boolean, default=False)
    notified_user2 = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user1 = relationship("User", foreign_keys=[user1_id], back_populates="matches")
    user2 = relationship("User", foreign_keys=[user2_id], back_populates="matches_as_user2")
    movie = relationship("Movie", back_populates="matches")


class StreamingService(Base):
    __tablename__ = "streaming_services"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)  # Netflix, Hulu, etc.
    logo_url = Column(String)

    movies = relationship("MovieStreamingService", back_populates="streaming_service")


class MovieStreamingService(Base):
    __tablename__ = "movie_streaming_services"

    id = Column(Integer, primary_key=True, index=True)
    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False)
    streaming_service_id = Column(Integer, ForeignKey("streaming_services.id"), nullable=False)

    movie = relationship("Movie", back_populates="streaming_services")
    streaming_service = relationship("StreamingService", back_populates="movies")


class WatchSession(Base):
    __tablename__ = "watch_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user1_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user2_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user1 = relationship("User", foreign_keys=[user1_id], back_populates="watch_sessions")
    user2 = relationship("User", foreign_keys=[user2_id], back_populates="watch_sessions_as_user2")


# Create all tables
def init_db():
    Base.metadata.create_all(bind=engine)


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
