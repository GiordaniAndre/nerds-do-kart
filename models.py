from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    racer_id = db.Column(db.Integer, db.ForeignKey('racers.id', ondelete='SET NULL'), nullable=True)
    interested_in_13hp = db.Column(db.Boolean, default=False)
    has_13hp_permission = db.Column(db.Boolean, default=False)
    bio = db.Column(db.Text, nullable=True)

    # Relationship
    racer = db.relationship('Racer', backref='user', lazy=True)

    def get_id(self):
        return str(self.id)

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def set_password(self, password):
        """Hash and set the user's password"""
        from app import bcrypt
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'racer_id': self.racer_id,
            'interested_in_13hp': self.interested_in_13hp,
            'has_13hp_permission': self.has_13hp_permission,
            'bio': self.bio
        }

class Racer(db.Model):
    __tablename__ = 'racers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer)
    experience_years = db.Column(db.Integer, default=0)
    total_races = db.Column(db.Integer, default=0)
    wins = db.Column(db.Integer, default=0)
    podium_finishes = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    race_results = db.relationship('RaceResult', backref='racer', lazy=True)
    best_laps = db.relationship('RacerBestLap', backref='racer', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'racer_id': self.id,
            'name': self.name,
            'age': self.age,
            'experience_years': self.experience_years,
            'total_races': self.total_races,
            'wins': self.wins,
            'podium_finishes': self.podium_finishes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class RacerBestLap(db.Model):
    __tablename__ = 'racer_best_laps'

    id = db.Column(db.Integer, primary_key=True)
    racer_id = db.Column(db.Integer, db.ForeignKey('racers.id', ondelete='CASCADE'), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id', ondelete='CASCADE'), nullable=False)
    condition = db.Column(db.String(20), nullable=False, default='dry')  # 'dry', 'wet', 'indoor'
    best_lap = db.Column(db.String(20), nullable=False)
    best_lap_seconds = db.Column(db.Float)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to location
    location = db.relationship('Location', lazy=True)

    def to_dict(self):
        return {
            'location_id': self.location_id,
            'location_name': self.location.name if self.location else None,
            'condition': self.condition,
            'best_lap': self.best_lap
        }


class LocationFastestLap(db.Model):
    __tablename__ = 'location_fastest_laps'

    id = db.Column(db.Integer, primary_key=True)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id', ondelete='CASCADE'), nullable=False)
    condition = db.Column(db.String(20), nullable=False)  # 'dry', 'wet', 'indoor'
    racer_id = db.Column(db.Integer, db.ForeignKey('racers.id', ondelete='CASCADE'), nullable=False)
    best_lap = db.Column(db.String(20), nullable=False)
    best_lap_seconds = db.Column(db.Float)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    location = db.relationship('Location', lazy=True)
    racer = db.relationship('Racer', lazy=True)

    def to_dict(self):
        return {
            'location_id': self.location_id,
            'location_name': self.location.name if self.location else None,
            'condition': self.condition,
            'racer_id': self.racer_id,
            'racer_name': self.racer.name if self.racer else None,
            'best_lap': self.best_lap
        }

class Location(db.Model):
    __tablename__ = 'locations'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    rental_duration = db.Column(db.String(50))
    price_per_person = db.Column(db.Numeric(10, 2))
    min_participants = db.Column(db.Integer)
    max_participants = db.Column(db.Integer)
    exclusive_info = db.Column(db.Text)
    min_height = db.Column(db.String(20))
    schedule_weekday = db.Column(db.String(100))
    schedule_saturday = db.Column(db.String(100))
    schedule_sunday = db.Column(db.String(100))
    address = db.Column(db.String(200))
    neighborhood = db.Column(db.String(100))
    city = db.Column(db.String(100))
    instagram = db.Column(db.String(100))
    website = db.Column(db.String(200))
    description = db.Column(db.Text)
    thumbnail_url = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    races = db.relationship('Race', backref='location', lazy=True)
    
    def to_dict(self):
        return {
            'location_id': self.id,
            'name': self.name,
            'rental_duration': self.rental_duration,
            'price_per_person': float(self.price_per_person) if self.price_per_person else 0,
            'min_participants': self.min_participants,
            'max_participants': self.max_participants,
            'exclusive_info': self.exclusive_info,
            'min_height': self.min_height,
            'schedule_weekday': self.schedule_weekday,
            'schedule_saturday': self.schedule_saturday,
            'schedule_sunday': self.schedule_sunday,
            'address': self.address,
            'neighborhood': self.neighborhood,
            'city': self.city,
            'instagram': self.instagram,
            'website': self.website,
            'description': self.description,
            'thumbnail_url': self.thumbnail_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Championship(db.Model):
    __tablename__ = 'championships'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    races = db.relationship('Race', backref='championship', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Race(db.Model):
    __tablename__ = 'races'

    id = db.Column(db.Integer, primary_key=True)
    race_name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'))
    championship_id = db.Column(db.Integer, db.ForeignKey('championships.id'), nullable=True)
    track_name = db.Column(db.String(100))
    weather = db.Column(db.String(50))
    total_laps = db.Column(db.Integer)
    winner_id = db.Column(db.Integer, db.ForeignKey('racers.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    race_results = db.relationship('RaceResult', backref='race', lazy=True)
    winner = db.relationship('Racer', foreign_keys=[winner_id])
    albums = db.relationship('Album', backref='race', lazy=True)

    def to_dict(self):
        return {
            'race_id': self.id,
            'race_name': self.race_name,
            'date': self.date.isoformat() if self.date else None,
            'location_id': self.location_id,
            'championship_id': self.championship_id,
            'track_name': self.track_name,
            'weather': self.weather,
            'total_laps': self.total_laps,
            'winner_id': self.winner_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class RaceResult(db.Model):
    __tablename__ = 'race_results'

    id = db.Column(db.Integer, primary_key=True)
    race_id = db.Column(db.Integer, db.ForeignKey('races.id'), nullable=False)
    racer_id = db.Column(db.Integer, db.ForeignKey('racers.id'), nullable=False)
    position = db.Column(db.Integer)
    lap_time_best = db.Column(db.String(20))
    lap_time_average = db.Column(db.String(20))
    total_time = db.Column(db.String(20))
    points_earned = db.Column(db.Integer, default=0)
    dnf = db.Column(db.Boolean, default=False)
    laps = db.Column(db.Integer)
    excluded = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'result_id': self.id,
            'race_id': self.race_id,
            'racer_id': self.racer_id,
            'position': self.position,
            'lap_time_best': self.lap_time_best,
            'lap_time_average': self.lap_time_average,
            'total_time': self.total_time,
            'points_earned': self.points_earned,
            'dnf': self.dnf,
            'laps': self.laps,
            'excluded': self.excluded,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Album(db.Model):
    __tablename__ = 'albums'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    race_id = db.Column(db.Integer, db.ForeignKey('races.id'), nullable=True)
    cover_url = db.Column(db.String(500))
    google_photos_link = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    media_items = db.relationship('MediaItem', backref='album', cascade='all, delete-orphan', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'race_id': self.race_id,
            'cover_url': self.cover_url,
            'google_photos_link': self.google_photos_link,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class MediaItem(db.Model):
    __tablename__ = 'media_items'

    id = db.Column(db.Integer, primary_key=True)
    album_id = db.Column(db.Integer, db.ForeignKey('albums.id'), nullable=False)
    media_type = db.Column(db.String(10))  # 'photo' or 'video'
    url = db.Column(db.String(500), nullable=False)
    title = db.Column(db.String(100))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'album_id': self.album_id,
            'media_type': self.media_type,
            'url': self.url,
            'title': self.title,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }