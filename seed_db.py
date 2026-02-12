"""
Script to seed the database with sample movies and streaming services
"""
from database import SessionLocal, Movie, StreamingService, MovieStreamingService
from sqlalchemy.exc import IntegrityError

def seed_database():
    db = SessionLocal()
    
    try:
        # Create streaming services
        streaming_services_data = [
            {"name": "Netflix", "logo_url": None},
            {"name": "Hulu", "logo_url": None},
            {"name": "Amazon Prime Video", "logo_url": None},
            {"name": "Disney+", "logo_url": None},
            {"name": "HBO Max", "logo_url": None},
            {"name": "Apple TV+", "logo_url": None},
            {"name": "Paramount+", "logo_url": None},
            {"name": "Peacock", "logo_url": None},
        ]
        
        streaming_services = {}
        for service_data in streaming_services_data:
            service = db.query(StreamingService).filter(StreamingService.name == service_data["name"]).first()
            if not service:
                service = StreamingService(**service_data)
                db.add(service)
            streaming_services[service_data["name"]] = service
        
        db.commit()
        
        # Sample movies with streaming availability
        movies_data = [
            {
                "title": "The Shawshank Redemption",
                "genre": "Drama",
                "rating": "R",
                "description": "Two imprisoned men bond over a number of years, finding solace and eventual redemption through acts of common decency.",
                "poster_url": "https://m.media-amazon.com/images/M/MV5BNDE3ODcxYzMtY2YzZC00NmNlLWJiNDMtZDViZWM2MzIxZDYwXkEyXkFqcGdeQXVyNjAwNDUxODI@._V1_SX300.jpg",
                "release_year": 1994,
                "imdb_rating": "9.3/10",
                "streaming_services": ["Netflix", "HBO Max"]
            },
            {
                "title": "The Dark Knight",
                "genre": "Action",
                "rating": "PG-13",
                "description": "When the menace known as the Joker wreaks havoc and chaos on the people of Gotham, Batman must accept one of the greatest psychological and physical tests of his ability to fight injustice.",
                "poster_url": "https://m.media-amazon.com/images/M/MV5BMTMxNTMwODM0NF5BMl5BanBnXkFtZTcwODAyMTk2Mw@@._V1_SX300.jpg",
                "release_year": 2008,
                "imdb_rating": "9.0/10",
                "streaming_services": ["HBO Max", "Amazon Prime Video"]
            },
            {
                "title": "Pulp Fiction",
                "genre": "Crime",
                "rating": "R",
                "description": "The lives of two mob hitmen, a boxer, a gangster and his wife, and a pair of diner bandits intertwine in four tales of violence and redemption.",
                "poster_url": "https://m.media-amazon.com/images/M/MV5BNGNhMDIzZTUtNTBlZi00MTRlLWFjM2ItYzViMjE3Yz5WRjY4XkEyXkFqcGdeQXVyNzkwMjQ5NzM@._V1_SX300.jpg",
                "release_year": 1994,
                "imdb_rating": "8.9/10",
                "streaming_services": ["Netflix", "Hulu"]
            },
            {
                "title": "Inception",
                "genre": "Sci-Fi",
                "rating": "PG-13",
                "description": "A skilled thief is given a chance at redemption if he can pull off an impossible heist: planting an idea in someone's mind through dream-sharing technology.",
                "poster_url": "https://m.media-amazon.com/images/M/MV5BMjAxMzY3NjcxNF5BMl5BanBnXkFtZTcwNTI5OTM0Mw@@._V1_SX300.jpg",
                "release_year": 2010,
                "imdb_rating": "8.8/10",
                "streaming_services": ["Netflix", "HBO Max"]
            },
            {
                "title": "The Matrix",
                "genre": "Sci-Fi",
                "rating": "R",
                "description": "A computer hacker learns from mysterious rebels about the true nature of his reality and his role in the war against its controllers.",
                "poster_url": "https://m.media-amazon.com/images/M/MV5BNzQzOTk3OTAtNDQ0Zi00ZTVkLWI0MTEtMDllZjNkYzNjNTc4L2ltYWdlXkEyXkFqcGdeQXVyNjU0OTQ0OTY@._V1_SX300.jpg",
                "release_year": 1999,
                "imdb_rating": "8.7/10",
                "streaming_services": ["HBO Max", "Hulu"]
            },
            {
                "title": "Goodfellas",
                "genre": "Crime",
                "rating": "R",
                "description": "The story of Henry Hill and his life in the mob, covering his relationship with his wife Karen Hill and his mob partners.",
                "poster_url": "https://m.media-amazon.com/images/M/MV5BY2NkZjEzMDgtN2RjYy00YzM1LWI4ZmQtMjIwYjFjNmI3ZGEwXkEyXkFqcGdeQXVyNzkwMjQ5NzM@._V1_SX300.jpg",
                "release_year": 1990,
                "imdb_rating": "8.7/10",
                "streaming_services": ["Netflix", "Amazon Prime Video"]
            },
            {
                "title": "Interstellar",
                "genre": "Sci-Fi",
                "rating": "PG-13",
                "description": "A team of explorers travel through a wormhole in space in an attempt to ensure humanity's survival.",
                "poster_url": "https://m.media-amazon.com/images/M/MV5BZjdkOTU3MDktN2IxOS00OGEyLWFmMjktY2FiMmZkNWIyODZiXkEyXkFqcGdeQXVyMTMxODk2OTU@._V1_SX300.jpg",
                "release_year": 2014,
                "imdb_rating": "8.6/10",
                "streaming_services": ["Paramount+", "Hulu"]
            },
            {
                "title": "The Lord of the Rings: The Fellowship of the Ring",
                "genre": "Fantasy",
                "rating": "PG-13",
                "description": "A meek Hobbit from the Shire and eight companions set out on a journey to destroy the powerful One Ring and save Middle-earth from the Dark Lord Sauron.",
                "poster_url": "https://m.media-amazon.com/images/M/MV5BN2EyZjM3NzUtNWVjMi00MzkxLWEzYzQtYjY0YjY0YzY0YzY0XkEyXkFqcGdeQXVyNjU0OTQ0OTY@._V1_SX300.jpg",
                "release_year": 2001,
                "imdb_rating": "8.8/10",
                "streaming_services": ["HBO Max", "Amazon Prime Video"]
            },
            {
                "title": "Fight Club",
                "genre": "Drama",
                "rating": "R",
                "description": "An insomniac office worker and a devil-may-care soapmaker form an underground fight club that evolves into something much bigger.",
                "poster_url": "https://m.media-amazon.com/images/M/MV5BMmEzNTkxYjQtZTc0MC00YTVjLTg5ZTEtZWMwOWVlYzY0NWIwXkEyXkFqcGdeQXVyNzkwMjQ5NzM@._V1_SX300.jpg",
                "release_year": 1999,
                "imdb_rating": "8.8/10",
                "streaming_services": ["Hulu", "Amazon Prime Video"]
            },
            {
                "title": "Forrest Gump",
                "genre": "Drama",
                "rating": "PG-13",
                "description": "The presidencies of Kennedy and Johnson, the Vietnam War, the Watergate scandal and other historical events unfold from the perspective of an Alabama man with an IQ of 75.",
                "poster_url": "https://m.media-amazon.com/images/M/MV5BNWIwODRlZTUtY2U3ZS00Yzg1LWJhNzYtMmZiYmEyNmU1NjMzXkEyXkFqcGdeQXVyMTQxNzMzNDI@._V1_SX300.jpg",
                "release_year": 1994,
                "imdb_rating": "8.8/10",
                "streaming_services": ["Netflix", "Paramount+"]
            },
            {
                "title": "The Godfather",
                "genre": "Crime",
                "rating": "R",
                "description": "The aging patriarch of an organized crime dynasty transfers control of his clandestine empire to his reluctant son.",
                "poster_url": "https://m.media-amazon.com/images/M/MV5BM2MyNjYxNmUtYTAwNi00MTYxLWJmNWYtYzZlODY3ZTk3OTFlXkEyXkFqcGdeQXVyNzkwMjQ5NzM@._V1_SX300.jpg",
                "release_year": 1972,
                "imdb_rating": "9.2/10",
                "streaming_services": ["Paramount+", "HBO Max"]
            },
            {
                "title": "The Avengers",
                "genre": "Action",
                "rating": "PG-13",
                "description": "Earth's mightiest heroes must come together and learn to fight as a team if they are going to stop the mischievous Loki and his alien army from enslaving humanity.",
                "poster_url": "https://m.media-amazon.com/images/M/MV5BNDYxNjQyMjAtNTdiOS00NGYwLWFmNTAtNThmYjU5ZGI2YTI1XkEyXkFqcGdeQXVyMTMxODk2OTU@._V1_SX300.jpg",
                "release_year": 2012,
                "imdb_rating": "8.0/10",
                "streaming_services": ["Disney+", "Hulu"]
            },
            {
                "title": "Parasite",
                "genre": "Thriller",
                "rating": "R",
                "description": "Greed and class discrimination threaten the newly formed symbiotic relationship between the wealthy Park family and the destitute Kim clan.",
                "poster_url": "https://m.media-amazon.com/images/M/MV5BYWZjMjk3ZTItODQ2ZC00NTY5LWE0ZDYtZTI3MjcwN2Q5NTVkXkEyXkFqcGdeQXVyODk4OTc3MTY@._V1_SX300.jpg",
                "release_year": 2019,
                "imdb_rating": "8.5/10",
                "streaming_services": ["Hulu", "Amazon Prime Video"]
            },
            {
                "title": "Spirited Away",
                "genre": "Animation",
                "rating": "PG",
                "description": "During her family's move to the suburbs, a sullen 10-year-old girl wanders into a world ruled by gods, witches, and spirits.",
                "poster_url": "https://m.media-amazon.com/images/M/MV5BMjlmZmI5MDctNDE2YS00YWE0LWE5ZWItZDBhYWQ0NTcxNTgyXkEyXkFqcGdeQXVyMTMxODk2OTU@._V1_SX300.jpg",
                "release_year": 2001,
                "imdb_rating": "8.6/10",
                "streaming_services": ["HBO Max", "Netflix"]
            },
            {
                "title": "The Lion King",
                "genre": "Animation",
                "rating": "G",
                "description": "Lion prince Simba and his father are targeted by his bitter uncle, who wants to ascend the throne himself.",
                "poster_url": "https://m.media-amazon.com/images/M/MV5BYTYxNGMyZTYtMjE3MS00MzNjLWFjNmYtMDk3N2FmM2JiM2M1XkEyXkFqcGdeQXVyNjY5NDU4NzI@._V1_SX300.jpg",
                "release_year": 1994,
                "imdb_rating": "8.5/10",
                "streaming_services": ["Disney+"]
            },
        ]
        
        for movie_data in movies_data:
            streaming_services_list = movie_data.pop("streaming_services", [])
            
            # Check if movie already exists
            existing_movie = db.query(Movie).filter(Movie.title == movie_data["title"]).first()
            if existing_movie:
                movie = existing_movie
            else:
                movie = Movie(**movie_data)
                db.add(movie)
                db.flush()  # Get the movie ID
            
            # Add streaming services
            for service_name in streaming_services_list:
                if service_name in streaming_services:
                    # Check if relationship already exists
                    existing_link = db.query(MovieStreamingService).filter(
                        MovieStreamingService.movie_id == movie.id,
                        MovieStreamingService.streaming_service_id == streaming_services[service_name].id
                    ).first()
                    
                    if not existing_link:
                        link = MovieStreamingService(
                            movie_id=movie.id,
                            streaming_service_id=streaming_services[service_name].id
                        )
                        db.add(link)
        
        db.commit()
        print("Database seeded successfully!")
        print(f"Added {len(movies_data)} movies and {len(streaming_services_data)} streaming services")
        
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
