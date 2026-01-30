from flask import Flask, jsonify, render_template, send_file, request, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_talisman import Talisman
from flask_login import LoginManager, current_user, login_required
from flask_bcrypt import Bcrypt
from sqlalchemy import func, case
from werkzeug.utils import secure_filename
import os
import uuid
import boto3
from models import db, User, Racer, Location, Race, RaceResult, Championship, Album, MediaItem, RacerBestLap, LocationFastestLap

# Try to load .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, use system environment variables

app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Por favor, faca login para acessar esta pagina.'
login_manager.login_message_category = 'error'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


if os.environ.get('ENVIRONMENT') == 'production':
    Talisman(app, force_https=True, content_security_policy=None)

database_url = os.environ.get('DATABASE_URL')

if database_url and database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///kart_race.db'

if not database_url:
    print("WARNING: Using SQLite fallback database (local only)")
    print("Set DATABASE_URL for PostgreSQL production database")
else:
    print("Using PostgreSQL database")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)

from auth import auth as auth_blueprint
app.register_blueprint(auth_blueprint)

from admin import admin as admin_blueprint
app.register_blueprint(admin_blueprint)


@app.route('/')
@app.route('/dashboard')
def dashboard():
    return render_template('pages/dashboard.html', current_user=current_user)

@app.route('/racers')
def racers():
    return render_template('pages/racers.html', current_user=current_user)

@app.route('/races')
def races():
    return render_template('pages/races.html', current_user=current_user)

@app.route('/leaderboard')
def leaderboard():
    return render_template('pages/leaderboard.html', current_user=current_user)

@app.route('/standings')
def standings():
    return render_template('pages/standings.html', current_user=current_user)

@app.route('/media')
def media():
    return render_template('pages/media.html', current_user=current_user)

@app.route('/locations')
def locations():
    return render_template('pages/locations.html', current_user=current_user)

@app.route('/13hp')
@login_required
def thirteenhp():
    """Hidden page for users interested in 13hp - only accessible if user has checked the option"""
    if not current_user.interested_in_13hp:
        flash('Voce precisa marcar interesse em 13hp no seu perfil para acessar esta pagina.', 'error')
        return redirect(url_for('dashboard'))
    return render_template('pages/13hp.html', current_user=current_user)

@app.route('/api/13hp/stats', methods=['GET'])
@login_required
def get_13hp_stats():
    """Get race stats for users interested in 13hp"""
    if not current_user.interested_in_13hp:
        return jsonify({'status': 'error', 'message': 'Acesso negado'}), 403

    interested_users = User.query.filter(
        User.interested_in_13hp == True,
        User.racer_id.isnot(None)
    ).all()

    all_locations = Location.query.all()

    # More flexible matching - look for "1000" or "1500" in name
    vp1000_ids = [loc.id for loc in all_locations if '1000' in loc.name.upper()]
    vp1500_ids = [loc.id for loc in all_locations if '1500' in loc.name.upper()]

    stats = []
    for user in interested_users:
        racer = Racer.query.get(user.racer_id)
        if not racer:
            continue

        vp1000_races = db.session.query(RaceResult).join(
            Race, RaceResult.race_id == Race.id
        ).filter(
            RaceResult.racer_id == racer.id,
            Race.location_id.in_(vp1000_ids)
        ).count() if vp1000_ids else 0

        vp1500_races = db.session.query(RaceResult).join(
            Race, RaceResult.race_id == Race.id
        ).filter(
            RaceResult.racer_id == racer.id,
            Race.location_id.in_(vp1500_ids)
        ).count() if vp1500_ids else 0

        stats.append({
            'racer_id': racer.id,
            'racer_name': racer.name,
            'user_name': user.name,
            'vp1000_races': vp1000_races,
            'vp1500_races': vp1500_races,
            'total_races': racer.total_races or 0,
            'has_permission': user.has_13hp_permission
        })

    vp1000_names = [loc.name for loc in all_locations if '1000' in loc.name.upper()]
    vp1500_names = [loc.name for loc in all_locations if '1500' in loc.name.upper()]

    return jsonify({
        'status': 'success',
        'data': stats,
        'debug': {
            'vp1000_locations': vp1000_names,
            'vp1500_locations': vp1500_names
        }
    })

@app.route('/index')
def index():
    return render_template('pages/dashboard.html', current_user=current_user)

@app.route('/logo_nerds.jpg')
def logo():
    return send_file('logo_nerds.jpg')

@app.route('/velopark-cover.jpg')
def velopark_cover():
    return send_file('c821b246-b93b-400f-a948-dfc6286d3df5.jpeg')

@app.route('/api/racers', methods=['GET'])
def get_racers():
    from sqlalchemy.orm import joinedload

    racers = Racer.query.options(
        joinedload(Racer.best_laps).joinedload(RacerBestLap.location)
    ).all()

    racers_data = []
    for racer in racers:
        racer_dict = racer.to_dict()

        locations_data = {}
        for lap in racer.best_laps:
            loc_id = lap.location_id
            if loc_id not in locations_data:
                locations_data[loc_id] = {
                    'location_name': lap.location.name if lap.location else None,
                    'dry': None,
                    'wet': None,
                    'indoor': None
                }
            locations_data[loc_id][lap.condition] = lap.best_lap

        racer_dict['best_laps_by_location'] = list(locations_data.values())
        racers_data.append(racer_dict)

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
    races = Race.query.order_by(Race.date.desc()).all()
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
    racers = Racer.query.order_by(
        Racer.wins.desc(),
        Racer.podium_finishes.desc(),
        Racer.total_races.desc()
    ).all()
    return jsonify({
        'status': 'success',
        'data': [racer.to_dict() for racer in racers]
    })

@app.route('/api/standings', methods=['GET'])
def get_championship_standings():
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
    
    fastest_result = None
    fastest_lap_time = None
    fastest_racer = None

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
            if ':' in lap_time_str:
                parts = lap_time_str.split(':')
                minutes = int(parts[0])
                seconds = float(parts[1])
                total_seconds = minutes * 60 + seconds
            else:
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
    recent_races = Race.query.order_by(Race.date.desc()).limit(8).all()
    return jsonify({
        'status': 'success',
        'data': [race.to_dict() for race in recent_races]
    })

@app.route('/api/fastest-by-location', methods=['GET'])
def get_fastest_by_location():
    from sqlalchemy.orm import joinedload

    fastest_records = LocationFastestLap.query.options(
        joinedload(LocationFastestLap.location),
        joinedload(LocationFastestLap.racer)
    ).all()

    location_data = {}
    for record in fastest_records:
        loc_id = record.location_id
        if loc_id not in location_data:
            location_data[loc_id] = {
                'location_id': loc_id,
                'location_name': record.location.name if record.location else None,
                'dry': None,
                'wet': None,
                'indoor': None
            }

        location_data[loc_id][record.condition] = {
            'fastest_lap': record.best_lap,
            'fastest_racer': record.racer.name if record.racer else None
        }

    fastest_laps = [data for data in location_data.values() if data['dry'] or data['wet'] or data['indoor']]

    return jsonify({
        'status': 'success',
        'data': fastest_laps
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

@app.route('/api/albums', methods=['GET'])
def get_albums():
    albums = Album.query.outerjoin(Race).order_by(
        Race.date.desc().nullslast(),
        Album.created_at.desc()
    ).all()
    albums_data = []
    for album in albums:
        album_dict = album.to_dict()
        photos = MediaItem.query.filter_by(album_id=album.id, media_type='photo').limit(4).all()
        videos = MediaItem.query.filter_by(album_id=album.id, media_type='video').limit(4 - len(photos)).all()
        media_items = photos + videos

        album_dict['media_count'] = MediaItem.query.filter_by(album_id=album.id).count()
        album_dict['media_preview'] = [item.to_dict() for item in media_items]

        if not album_dict.get('cover_url'):
            first_photo = MediaItem.query.filter_by(album_id=album.id, media_type='photo').first()
            if first_photo:
                album_dict['cover_url'] = first_photo.url

        if album.race:
            album_dict['race_name'] = album.race.race_name
            album_dict['race_date'] = album.race.date.isoformat() if album.race.date else None
        albums_data.append(album_dict)

    return jsonify({
        'status': 'success',
        'data': albums_data
    })

@app.route('/api/albums/<int:album_id>', methods=['GET'])
def get_album(album_id):
    album = Album.query.get(album_id)
    if not album:
        return jsonify({'error': 'Album not found'}), 404

    album_dict = album.to_dict()
    media_items = MediaItem.query.filter_by(album_id=album_id).order_by(MediaItem.created_at.desc()).all()
    album_dict['media_items'] = [item.to_dict() for item in media_items]

    if album.race:
        album_dict['race_name'] = album.race.race_name
        album_dict['race_date'] = album.race.date.isoformat() if album.race.date else None

    return jsonify({
        'status': 'success',
        'data': album_dict
    })

@app.route('/api/photos/by-race', methods=['GET'])
def get_photos_by_race():
    """Get all photos grouped by race, sorted by race date (most recent first)"""
    albums = Album.query.outerjoin(Race).order_by(
        Race.date.desc().nullslast(),
        Album.created_at.desc()
    ).all()

    result = []
    for album in albums:
        photos = MediaItem.query.filter_by(
            album_id=album.id,
            media_type='photo'
        ).order_by(MediaItem.created_at.desc()).all()

        if photos:
            album_data = {
                'album_id': album.id,
                'album_name': album.name,
                'race_name': album.race.race_name if album.race else 'Sem corrida associada',
                'race_date': album.race.date.isoformat() if album.race and album.race.date else None,
                'description': album.description,
                'photo_count': len(photos),
                'photos': [photo.to_dict() for photo in photos]
            }
            result.append(album_data)

    return jsonify({
        'status': 'success',
        'data': result
    })

@app.route('/api/videos', methods=['GET'])
def get_videos():
    """Get all videos grouped by album"""
    albums = Album.query.outerjoin(Race).order_by(
        Race.date.desc().nullslast(),
        Album.created_at.desc()
    ).all()

    videos = []
    for album in albums:
        album_videos = MediaItem.query.filter_by(
            album_id=album.id,
            media_type='video'
        ).order_by(MediaItem.created_at.desc()).all()

        for video in album_videos:
            video_dict = video.to_dict()
            video_dict['album_name'] = album.name
            video_dict['album_id'] = album.id
            videos.append(video_dict)

    return jsonify({
        'status': 'success',
        'data': videos
    })

@app.route('/api/reload', methods=['POST'])
def reload_data():
    """Manual endpoint to refresh database connection"""
    try:
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

def get_r2_client():
    """Get Cloudflare R2 client"""
    return boto3.client(
        's3',
        endpoint_url=os.environ.get('R2_ENDPOINT_URL'),
        aws_access_key_id=os.environ.get('R2_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('R2_SECRET_ACCESS_KEY'),
        region_name='auto'
    )

def upload_to_r2(file, folder='media'):
    """Upload file to Cloudflare R2"""
    try:
        filename = secure_filename(file.filename)
        ext = filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{folder}/{uuid.uuid4().hex}.{ext}"

        r2_client = get_r2_client()
        bucket_name = os.environ.get('R2_BUCKET_NAME')

        r2_client.upload_fileobj(
            file,
            bucket_name,
            unique_filename,
            ExtraArgs={'ContentType': file.content_type}
        )

        public_url = os.environ.get('R2_PUBLIC_URL')
        return f"{public_url}/{unique_filename}"
    except Exception as e:
        print(f"R2 Upload Error: {e}")
        return None

@app.route('/upload/photo/<int:album_id>', methods=['POST'])
@login_required
def user_upload_photo(album_id):
    """Allow logged-in users to upload photos to an album"""
    album = Album.query.get(album_id)
    if not album:
        return jsonify({'status': 'error', 'message': 'Album not found'}), 404

    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No file selected'}), 400

    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    if not '.' in file.filename:
        return jsonify({'status': 'error', 'message': 'Invalid file type'}), 400

    ext = file.filename.rsplit('.', 1)[1].lower()
    if ext not in allowed_extensions:
        return jsonify({'status': 'error', 'message': 'Only images are allowed'}), 400

    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)

    if file_size > 10 * 1024 * 1024:
        return jsonify({'status': 'error', 'message': 'File too large (max 10MB)'}), 400

    url = upload_to_r2(file, folder=f'albums/{album_id}')
    if not url:
        return jsonify({'status': 'error', 'message': 'Upload failed'}), 500

    title = request.form.get('title', '')
    description = request.form.get('description', '')

    media_item = MediaItem(
        album_id=album_id,
        media_type='photo',
        url=url,
        title=title,
        description=description
    )

    db.session.add(media_item)
    db.session.commit()

    return jsonify({
        'status': 'success',
        'message': 'Photo uploaded successfully',
        'data': media_item.to_dict()
    })

@app.route('/upload/video/<int:album_id>', methods=['POST'])
@login_required
def user_upload_video(album_id):
    """Allow logged-in users to add YouTube videos to an album"""
    album = Album.query.get(album_id)
    if not album:
        return jsonify({'status': 'error', 'message': 'Album not found'}), 404

    data = request.get_json()
    url = data.get('url', '').strip()
    title = data.get('title', '').strip()
    description = data.get('description', '').strip()

    if not url:
        return jsonify({'status': 'error', 'message': 'Video URL is required'}), 400

    if not ('youtube.com' in url or 'youtu.be' in url):
        return jsonify({'status': 'error', 'message': 'Only YouTube URLs are supported'}), 400

    media_item = MediaItem(
        album_id=album_id,
        media_type='video',
        url=url,
        title=title,
        description=description
    )

    db.session.add(media_item)
    db.session.commit()

    return jsonify({
        'status': 'success',
        'message': 'Video added successfully',
        'data': media_item.to_dict()
    })

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5003))
    debug = os.environ.get('ENVIRONMENT') != 'production'

    if debug:
        print("Nerds do Kart - Development Server (Database Only)")
        print(f"Local access: http://localhost:{port}")
        print("Using PostgreSQL database")
        print("Server running... Press Ctrl+C to stop")
    else:
        print("Nerds do Kart - Production Server (Database Only)")
        print("Live at: https://nerdsdokart.com.br")
        print("Using PostgreSQL database")
    
    app.run(debug=debug, host='0.0.0.0', port=port)