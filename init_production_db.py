#!/usr/bin/env python3
"""
Initialize production database with data
Run this once to populate the database with initial data
"""
import os
from app import app, db
from models import Racer, Location, Race, RaceResult
from datetime import datetime

def init_production_data():
    """Initialize production database with starter data"""
    with app.app_context():
        # Check if database already has data
        if Racer.query.first():
            print("Database already has data. Skipping initialization.")
            return
        
        print("🏁 Initializing production database with data...")
        
        # Create tables if they don't exist
        db.create_all()
        
        # Add Racers
        racers_data = [
            {"name": "Rafael Kehl", "age": 29, "wins": 1, "podium_finishes": 2, "total_races": 2},
            {"name": "Tomaz Lanfredi", "age": 36, "wins": 0, "podium_finishes": 2, "total_races": 2},
            {"name": "Gustavo Cruz", "wins": 1, "podium_finishes": 2, "total_races": 2},
            {"name": "Gabriel Stepien", "wins": 0, "podium_finishes": 1, "total_races": 2},
            {"name": "Nicolas Chin Lee", "wins": 0, "podium_finishes": 1, "total_races": 2},
            {"name": "Thalys Da Silva", "wins": 0, "podium_finishes": 0, "total_races": 2},
            {"name": "Alexandre Moraes", "wins": 0, "podium_finishes": 0, "total_races": 2},
            {"name": "Douglas Borges", "wins": 0, "podium_finishes": 0, "total_races": 2},
            {"name": "Peterson Luz", "wins": 0, "podium_finishes": 0, "total_races": 2},
            {"name": "Rodrigo de Souza", "wins": 0, "podium_finishes": 0, "total_races": 2},
            {"name": "Valter Ferreira", "wins": 0, "podium_finishes": 0, "total_races": 2},
            {"name": "André Giordani", "wins": 0, "podium_finishes": 0, "total_races": 2},
            {"name": "Leonardo Paz", "wins": 0, "podium_finishes": 0, "total_races": 2},
            {"name": "Francisco Stepien", "wins": 0, "podium_finishes": 0, "total_races": 2},
            {"name": "Cauã Rodrigues", "wins": 0, "podium_finishes": 0, "total_races": 2},
            {"name": "Guilherme Barbosa", "wins": 0, "podium_finishes": 0, "total_races": 2},
            {"name": "Valter Junior", "wins": 0, "podium_finishes": 1, "total_races": 2},
            {"name": "Gregory Fiel", "wins": 0, "podium_finishes": 0, "total_races": 2}
        ]
        
        for racer_info in racers_data:
            racer = Racer(**racer_info)
            db.session.add(racer)
        
        # Add Locations
        locations_data = [
            {
                "name": "Velopark VP1000",
                "rental_duration": "25 minutos (5+20)",
                "price_per_person": 145.00,
                "min_participants": 11,
                "max_participants": 20,
                "address": "Rod. RS-020 Km 7",
                "city": "Nova Santa Rita",
                "instagram": "@velopark",
                "website": "https://www.velopark.com.br/",
                "thumbnail_url": "/static/images/vp1000.jpg"
            },
            {
                "name": "Velopark VP1500", 
                "rental_duration": "25 minutos (5+20)",
                "price_per_person": 165.00,
                "min_participants": 11,
                "max_participants": 20,
                "address": "Rod. RS-020 Km 7",
                "city": "Nova Santa Rita",
                "instagram": "@velopark",
                "website": "https://www.velopark.com.br/",
                "thumbnail_url": "/static/images/vp1500.jpg"
            },
            {
                "name": "Top Speed Kart",
                "rental_duration": "30 minutos",
                "price_per_person": 90.00,
                "min_participants": 11,
                "max_participants": 12,
                "address": "Av. Praia de Belas 1212",
                "city": "Porto Alegre",
                "instagram": "@topspeedkart",
                "website": "https://www.topspeedkart.com.br/",
                "thumbnail_url": "/static/images/topspeed.jpg"
            },
            {
                "name": "Piquet Kart Indoor",
                "rental_duration": "Consultar",
                "price_per_person": 0,
                "min_participants": 11,
                "max_participants": 16,
                "address": "Av. João Wallig 1800, Shopping Iguatemi",
                "city": "Porto Alegre",
                "instagram": "@piquetkartpoa",
                "website": "https://www.piquetkart.com/",
                "thumbnail_url": "/static/images/piquetkart.jpg"
            }
        ]
        
        for location_info in locations_data:
            location = Location(**location_info)
            db.session.add(location)
        
        # Add sample races
        races_data = [
            {
                "race_name": "1ª Corrida - Nerds do Kart",
                "date": datetime(2024, 11, 23).date(),
                "location_id": 1,
                "track_name": "Velopark VP1000",
                "weather": "Ensolarado",
                "total_laps": 20,
                "winner_id": 1
            },
            {
                "race_name": "2ª Corrida - Nerds do Kart",
                "date": datetime(2024, 12, 14).date(),
                "location_id": 1,
                "track_name": "Velopark VP1000",
                "weather": "Nublado",
                "total_laps": 20,
                "winner_id": 3
            }
        ]
        
        for race_info in races_data:
            race = Race(**race_info)
            db.session.add(race)
        
        db.session.commit()
        print("✅ Database initialized with starter data!")
        
        # Verify
        print(f"📊 Added: {Racer.query.count()} racers")
        print(f"📊 Added: {Location.query.count()} locations")
        print(f"📊 Added: {Race.query.count()} races")

if __name__ == "__main__":
    init_production_data()