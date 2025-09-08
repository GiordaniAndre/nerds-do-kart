from flask import Flask, jsonify, render_template, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import func, case
import os
from models import db, Racer, Location, Race, RaceResult

# Try to load .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, use system environment variables

app = Flask(__name__)

# Database configuration
database_url = os.environ.get('DATABASE_URL')

# Also check for Railway's default database URL patterns
if not database_url:
    database_url = os.environ.get('DATABASE_PUBLIC_URL')
if not database_url:
    database_url = os.environ.get('POSTGRES_URL')
if not database_url:
    # Try all PostgreSQL-related environment variables
    for key in os.environ:
        if 'DATABASE' in key or 'POSTGRES' in key:
            if os.environ[key].startswith('postgres'):
                database_url = os.environ[key]
                print(f"🔍 Found database URL in {key}")
                break

if database_url and database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

# Debug: Print all environment variables in production
if os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('PORT'):
    print("🔍 Production environment detected")
    print(f"   DATABASE_URL: {database_url[:50] if database_url else 'NOT SET'}")
    print(f"   DATABASE_PUBLIC_URL: {os.environ.get('DATABASE_PUBLIC_URL', 'NOT SET')}")
    print(f"   RAILWAY_ENVIRONMENT: {os.environ.get('RAILWAY_ENVIRONMENT', 'NOT SET')}")
    print(f"   PORT: {os.environ.get('PORT', 'NOT SET')}")
    
    if not database_url:
        print("❌ CRITICAL: DATABASE_URL is missing in production!")
        print("   Available env vars:", list(os.environ.keys()))
        # Don't crash, but log the issue
        # raise Exception("DATABASE_URL is required in production! Please set it in Railway Variables.")

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///kart_race.db'

if not database_url:
    print("⚠️  WARNING: Using SQLite fallback database (local only)")
    print("   Set DATABASE_URL for PostgreSQL production database")
    print(f"   Final URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
else:
    print("🗄️  Using PostgreSQL database")
    print(f"   Connection: {database_url[:50]}...")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)
migrate = Migrate(app, db)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/debug', methods=['GET'])
def debug_info():
    """Debug endpoint to check database connection"""
    return jsonify({
        'database_url_set': bool(os.environ.get('DATABASE_URL')),
        'database_public_url_set': bool(os.environ.get('DATABASE_PUBLIC_URL')),
        'railway_environment': os.environ.get('RAILWAY_ENVIRONMENT', 'NOT SET'),
        'port': os.environ.get('PORT', 'NOT SET'),
        'sqlalchemy_uri': app.config['SQLALCHEMY_DATABASE_URI'][:50] if app.config['SQLALCHEMY_DATABASE_URI'] else 'NOT SET',
        'is_sqlite': 'sqlite' in str(app.config['SQLALCHEMY_DATABASE_URI']),
        'is_postgresql': 'postgresql' in str(app.config['SQLALCHEMY_DATABASE_URI']),
        'env_vars_available': list(os.environ.keys())
    })

@app.route('/logo_nerds.jpg')
def logo():
    return send_file('logo_nerds.jpg')

@app.route('/velopark-cover.jpg')
def velopark_cover():
    return send_file('c821b246-b93b-400f-a948-dfc6286d3df5.jpeg')

@app.route('/api/racers', methods=['GET'])
def get_racers():
    racers = Racer.query.all()
    racers_data = [racer.to_dict() for racer in racers]
    return jsonify({
        'status': 'success',
        'count': len(racers_data),
        'data': racers_data
    })

@app.route('/api/racers/<int:racer_id>', methods=['GET'])
def get_racer(racer_id):
    racer = Racer.query.get(racer_id)
    if not racer:
        return jsonify({'status': 'error', 'message': 'Racer not found'}), 404
    
    recent_results = RaceResult.query.filter_by(racer_id=racer_id).limit(10).all()
    racer_data = racer.to_dict()
    racer_data['recent_results'] = [result.to_dict() for result in recent_results]
    
    return jsonify({
        'status': 'success',
        'data': racer_data
    })

@app.route('/api/races', methods=['GET'])
def get_races():
    races = Race.query.all()
    races_data = [race.to_dict() for race in races]
    return jsonify({
        'status': 'success',
        'count': len(races_data),
        'data': races_data
    })

@app.route('/api/races/<int:race_id>', methods=['GET'])
def get_race(race_id):
    race = Race.query.get(race_id)
    if not race:
        return jsonify({'status': 'error', 'message': 'Race not found'}), 404
    
    # Get race results with racer names
    race_results = db.session.query(RaceResult, Racer.name).join(
        Racer, RaceResult.racer_id == Racer.id
    ).filter(RaceResult.race_id == race_id).order_by(RaceResult.position).all()
    
    race_data = race.to_dict()
    race_data['results'] = []
    for result, racer_name in race_results:
        result_dict = result.to_dict()
        result_dict['name'] = racer_name
        race_data['results'].append(result_dict)
    
    return jsonify({
        'status': 'success',
        'data': race_data
    })

@app.route('/api/values', methods=['GET'])
@app.route('/api/results', methods=['GET'])
def get_race_results():
    # Get results with racer and race info
    results = db.session.query(RaceResult, Racer.name, Race.race_name, Race.date).join(
        Racer, RaceResult.racer_id == Racer.id
    ).join(
        Race, RaceResult.race_id == Race.id
    ).all()
    
    results_list = []
    for result, racer_name, race_name, race_date in results:
        result_dict = result.to_dict()
        result_dict['name'] = racer_name
        result_dict['race_name'] = race_name
        result_dict['date'] = race_date.isoformat() if race_date else None
        results_list.append(result_dict)
    
    return jsonify({
        'status': 'success',
        'count': len(results_list),
        'data': results_list
    })

@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    racers = Racer.query.order_by(Racer.wins.desc()).all()
    return jsonify({
        'status': 'success',
        'data': [racer.to_dict() for racer in racers]
    })

@app.route('/api/standings', methods=['GET'])
def get_championship_standings():
    # Calculate standings from race results
    standings = db.session.query(
        Racer.id.label('racer_id'),
        Racer.name,
        func.sum(RaceResult.points_earned).label('total_points'),
        func.sum(case((RaceResult.position == 1, 1), else_=0)).label('wins'),
        func.count(RaceResult.id).label('races_participated')
    ).join(
        RaceResult, Racer.id == RaceResult.racer_id
    ).group_by(Racer.id, Racer.name).order_by(func.sum(RaceResult.points_earned).desc()).all()
    
    standings_list = []
    for standing in standings:
        standings_list.append({
            'racer_id': standing.racer_id,
            'name': standing.name,
            'total_points': int(standing.total_points or 0),
            'wins': int(standing.wins or 0),
            'races_participated': int(standing.races_participated or 0)
        })
    
    return jsonify({
        'status': 'success',
        'data': standings_list
    })

@app.route('/api/stats', methods=['GET'])
def get_stats():
    total_racers = Racer.query.count()
    total_races = Race.query.count()
    total_results = RaceResult.query.count()
    
    # Find fastest lap (handle MM:SS.mmm format)
    fastest_result = None
    fastest_lap_time = None
    fastest_racer = None
    
    # Get all valid lap times
    results_with_times = db.session.query(RaceResult, Racer.name).join(
        Racer, RaceResult.racer_id == Racer.id
    ).filter(
        RaceResult.lap_time_best.isnot(None),
        RaceResult.lap_time_best != '',
        RaceResult.lap_time_best != '-'
    ).all()
    
    min_time_seconds = float('inf')
    
    for result, racer_name in results_with_times:
        lap_time_str = result.lap_time_best
        try:
            # Try to parse MM:SS.mmm format
            if ':' in lap_time_str:
                parts = lap_time_str.split(':')
                minutes = int(parts[0])
                seconds = float(parts[1])
                total_seconds = minutes * 60 + seconds
            else:
                # Try direct float conversion
                total_seconds = float(lap_time_str)
            
            if total_seconds < min_time_seconds:
                min_time_seconds = total_seconds
                fastest_lap_time = total_seconds
                fastest_racer = racer_name
        except (ValueError, TypeError, IndexError):
            continue
    
    stats = {
        'total_racers': total_racers,
        'total_races': total_races,
        'total_results': total_results,
        'fastest_lap_time': fastest_lap_time,
        'fastest_lap_racer': fastest_racer
    }
    
    return jsonify({
        'status': 'success',
        'data': stats
    })

@app.route('/api/recent-races', methods=['GET'])
def get_recent_races():
    recent_races = Race.query.order_by(Race.date.desc()).limit(5).all()
    return jsonify({
        'status': 'success',
        'data': [race.to_dict() for race in recent_races]
    })

@app.route('/api/locations', methods=['GET'])
def get_locations():
    locations = Location.query.all()
    locations_data = [location.to_dict() for location in locations]
    return jsonify(locations_data)

@app.route('/api/locations/<int:location_id>', methods=['GET'])
def get_location(location_id):
    location = Location.query.get(location_id)
    if not location:
        return jsonify({'error': f'Location {location_id} not found'}), 404
    return jsonify(location.to_dict())

@app.route('/api/reload', methods=['POST'])
def reload_data():
    """Manual endpoint to refresh database connection"""
    try:
        # Test database connection
        db.session.execute(db.text('SELECT 1'))
        return jsonify({
            'status': 'success',
            'message': 'Database connection verified'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Database error: {str(e)}'
        }), 500

@app.route('/api/init-db', methods=['GET'])
def init_database():
    """Initialize database with starter data (run once)"""
    try:
        # Check if already has data
        if Racer.query.first():
            return jsonify({
                'status': 'success',
                'message': 'Database already has data'
            })
        
        # Import the init function
        from init_production_db import init_production_data
        init_production_data()
        
        return jsonify({
            'status': 'success',
            'message': 'Database initialized with data!',
            'stats': {
                'racers': Racer.query.count(),
                'locations': Location.query.count(),
                'races': Race.query.count()
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error initializing database: {str(e)}'
        }), 500

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5003))
    debug = os.environ.get('ENVIRONMENT') != 'production'
    
    if debug:
        print("🏁 Nerds do Kart - Development Server (Database Only)")
        print(f"📍 Local access: http://localhost:{port}")
        print("🗄️  Using PostgreSQL database")
        print("🚀 Server running... Press Ctrl+C to stop")
    else:
        print("🏁 Nerds do Kart - Production Server (Database Only)")
        print("🌐 Live at: https://nerdsdokart.com.br")
        print("🗄️  Using PostgreSQL database")
    
    app.run(debug=debug, host='0.0.0.0', port=port)