from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

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

class Race(db.Model):
    __tablename__ = 'races'
    
    id = db.Column(db.Integer, primary_key=True)
    race_name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'))
    track_name = db.Column(db.String(100))
    weather = db.Column(db.String(50))
    total_laps = db.Column(db.Integer)
    winner_id = db.Column(db.Integer, db.ForeignKey('racers.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    race_results = db.relationship('RaceResult', backref='race', lazy=True)
    winner = db.relationship('Racer', foreign_keys=[winner_id])
    
    def to_dict(self):
        return {
            'race_id': self.id,
            'race_name': self.race_name,
            'date': self.date.isoformat() if self.date else None,
            'location_id': self.location_id,
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
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }