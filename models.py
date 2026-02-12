from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum


class SwipeDirection(str, Enum):
    LEFT = "left"
    RIGHT = "right"


# User models
class UserCreate(BaseModel):
    username: str


class UserResponse(BaseModel):
    id: int
    username: str
    invite_code: str
    created_at: datetime

    class Config:
        from_attributes = True


# Friend models
class FriendRequestCreate(BaseModel):
    invite_code: str


class FriendRequestResponse(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    status: str
    created_at: datetime
    sender: UserResponse
    receiver: UserResponse

    class Config:
        from_attributes = True


class FriendshipResponse(BaseModel):
    id: int
    user1_id: int
    user2_id: int
    created_at: datetime
    friend: UserResponse

    class Config:
        from_attributes = True


# Movie models
class MovieCreate(BaseModel):
    title: str
    genre: str
    rating: Optional[str] = None
    description: Optional[str] = None
    poster_url: Optional[str] = None
    release_year: Optional[int] = None
    imdb_rating: Optional[str] = None


class StreamingServiceResponse(BaseModel):
    id: int
    name: str
    logo_url: Optional[str] = None

    class Config:
        from_attributes = True


class MovieResponse(BaseModel):
    id: int
    title: str
    genre: str
    rating: Optional[str] = None
    description: Optional[str] = None
    poster_url: Optional[str] = None
    release_year: Optional[int] = None
    imdb_rating: Optional[str] = None
    streaming_services: List[StreamingServiceResponse] = []

    class Config:
        from_attributes = True


# Swipe models
class SwipeCreate(BaseModel):
    movie_id: int
    direction: SwipeDirection


class SwipeResponse(BaseModel):
    id: int
    user_id: int
    movie_id: int
    direction: SwipeDirection
    created_at: datetime

    class Config:
        from_attributes = True


# Match models
class MatchResponse(BaseModel):
    id: int
    user1_id: int
    user2_id: int
    movie_id: int
    notified_user1: bool
    notified_user2: bool
    created_at: datetime
    movie: MovieResponse
    friend: UserResponse

    class Config:
        from_attributes = True


# Watch session models
class WatchSessionCreate(BaseModel):
    friend_id: int


class WatchSessionResponse(BaseModel):
    id: int
    user1_id: int
    user2_id: int
    created_at: datetime
    friend: UserResponse

    class Config:
        from_attributes = True


# Filter models
class MovieFilter(BaseModel):
    streaming_services: Optional[List[str]] = None
    genres: Optional[List[str]] = None
