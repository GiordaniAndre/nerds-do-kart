from functools import wraps
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
from models import db, User, Racer, Race, RaceResult, Location, Championship, Album, MediaItem
import boto3
import os
import uuid
from werkzeug.utils import secure_filename

admin = Blueprint('admin', __name__, url_prefix='/admin')

def get_r2_client():
    """Get configured R2 client"""
    return boto3.client(
        's3',
        endpoint_url=os.environ.get('R2_ENDPOINT_URL'),
        aws_access_key_id=os.environ.get('R2_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('R2_SECRET_ACCESS_KEY'),
        region_name='auto'
    )

def upload_to_r2(file, folder='media'):
    """Upload file to R2 and return public URL"""
    try:
        filename = secure_filename(file.filename)
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        unique_filename = f"{folder}/{uuid.uuid4().hex}.{ext}"

        r2_client = get_r2_client()
        bucket_name = os.environ.get('R2_BUCKET_NAME')

        r2_client.upload_fileobj(
            file,
            bucket_name,
            unique_filename,
            ExtraArgs={
                'ContentType': file.content_type,
                'CacheControl': 'public, max-age=31536000'
            }
        )

        public_url = os.environ.get('R2_PUBLIC_URL')
        return f"{public_url}/{unique_filename}"
    except Exception as e:
        print(f"Error uploading to R2: {e}")
        raise


def admin_required(f):
    """Decorator that requires the user to be an admin."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.url))
        if not current_user.is_admin:
            flash('Acesso negado. Voce precisa ser administrador.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


@admin.route('/')
@login_required
@admin_required
def dashboard():
    stats = {
        'racers': Racer.query.count(),
        'races': Race.query.count(),
        'results': RaceResult.query.count(),
        'locations': Location.query.count(),
        'championships': Championship.query.count(),
        'albums': Album.query.count(),
        'users': User.query.count()
    }
    return render_template('admin/dashboard.html', stats=stats)


# ============== RACERS ==============

@admin.route('/racers')
@login_required
@admin_required
def racers():
    racers_list = Racer.query.order_by(Racer.name).all()
    return render_template('admin/racers.html', racers=racers_list)


@admin.route('/racers', methods=['POST'])
@login_required
@admin_required
def create_racer():
    data = request.get_json() if request.is_json else request.form

    name = data.get('name')
    if not name:
        return jsonify({'success': False, 'message': 'Nome e obrigatorio'}), 400

    racer = Racer(
        name=name,
        age=int(data.get('age')) if data.get('age') else None,
        experience_years=int(data.get('experience_years')) if data.get('experience_years') else 0,
        total_races=int(data.get('total_races')) if data.get('total_races') else 0,
        wins=int(data.get('wins')) if data.get('wins') else 0,
        podium_finishes=int(data.get('podium_finishes')) if data.get('podium_finishes') else 0
    )

    db.session.add(racer)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Piloto criado com sucesso', 'racer': racer.to_dict()})


@admin.route('/racers/<int:id>', methods=['PUT'])
@login_required
@admin_required
def update_racer(id):
    racer = Racer.query.get_or_404(id)
    data = request.get_json() if request.is_json else request.form

    if data.get('name'):
        racer.name = data.get('name')
    if data.get('age') is not None:
        racer.age = int(data.get('age')) if data.get('age') else None
    if data.get('experience_years') is not None:
        racer.experience_years = int(data.get('experience_years')) if data.get('experience_years') else 0
    if data.get('total_races') is not None:
        racer.total_races = int(data.get('total_races')) if data.get('total_races') else 0
    if data.get('wins') is not None:
        racer.wins = int(data.get('wins')) if data.get('wins') else 0
    if data.get('podium_finishes') is not None:
        racer.podium_finishes = int(data.get('podium_finishes')) if data.get('podium_finishes') else 0

    db.session.commit()

    return jsonify({'success': True, 'message': 'Piloto atualizado com sucesso', 'racer': racer.to_dict()})


@admin.route('/racers/<int:id>', methods=['DELETE'])
@login_required
@admin_required
def delete_racer(id):
    racer = Racer.query.get_or_404(id)

    # Check if racer has race results
    results_count = RaceResult.query.filter_by(racer_id=id).count()
    if results_count > 0:
        return jsonify({'success': False, 'message': f'Nao e possivel excluir: piloto tem {results_count} resultados de corridas'}), 400

    db.session.delete(racer)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Piloto excluido com sucesso'})


@admin.route('/racers/recalculate-stats', methods=['POST'])
@login_required
@admin_required
def recalculate_racer_stats():
    """Recalculate wins, podiums, total races, best laps, and location fastest laps"""
    from models import RacerBestLap, LocationFastestLap

    def parse_lap_time(lap_time_str):
        try:
            if ':' in lap_time_str:
                parts = lap_time_str.split(':')
                minutes = int(parts[0])
                seconds = float(parts[1])
                return minutes * 60 + seconds
            else:
                return float(lap_time_str)
        except (ValueError, TypeError, IndexError):
            return None

    def get_weather_condition(weather):
        weather = (weather or '').lower()
        wet_conditions = ['chuvoso', 'molhado', 'wet', 'rain', 'chuva']
        indoor_conditions = ['indoor', 'coberto', 'fechado']

        if any(cond in weather for cond in indoor_conditions):
            return 'indoor'
        elif any(cond in weather for cond in wet_conditions):
            return 'wet'
        else:
            return 'dry'

    racers = Racer.query.all()
    locations = Location.query.all()
    updated_count = 0
    best_laps_count = 0
    location_fastest_count = 0

    RacerBestLap.query.delete()
    LocationFastestLap.query.delete()

    for racer in racers:
        results = RaceResult.query.filter_by(racer_id=racer.id).all()

        total_races = len(results)
        wins = sum(1 for r in results if r.position == 1)
        podiums = sum(1 for r in results if r.position is not None and r.position <= 3)

        racer.total_races = total_races
        racer.wins = wins
        racer.podium_finishes = podiums
        updated_count += 1

        for location in locations:
            location_results = db.session.query(RaceResult, Race).join(
                Race, RaceResult.race_id == Race.id
            ).filter(
                RaceResult.racer_id == racer.id,
                Race.location_id == location.id,
                RaceResult.lap_time_best.isnot(None),
                RaceResult.lap_time_best != '',
                RaceResult.lap_time_best != '-'
            ).all()

            if location_results:
                condition_bests = {'dry': (None, None), 'wet': (None, None), 'indoor': (None, None)}

                for result, race in location_results:
                    condition = get_weather_condition(race.weather)
                    time_seconds = parse_lap_time(result.lap_time_best)

                    if time_seconds is not None:
                        current_best_time, current_best_lap = condition_bests[condition]
                        if current_best_time is None or time_seconds < current_best_time:
                            condition_bests[condition] = (time_seconds, result.lap_time_best)

                for condition, (best_time, best_lap_str) in condition_bests.items():
                    if best_lap_str:
                        best_lap = RacerBestLap(
                            racer_id=racer.id,
                            location_id=location.id,
                            condition=condition,
                            best_lap=best_lap_str,
                            best_lap_seconds=best_time
                        )
                        db.session.add(best_lap)
                        best_laps_count += 1

    # Calculate fastest lap per location per condition (dry/wet/indoor)
    for location in locations:
        races = Race.query.filter_by(location_id=location.id).all()

        # Group races by condition
        condition_races = {'dry': [], 'wet': [], 'indoor': []}
        for race in races:
            condition = get_weather_condition(race.weather)
            condition_races[condition].append(race.id)

        # Find fastest for each condition
        for condition, race_ids in condition_races.items():
            if not race_ids:
                continue

            results = db.session.query(RaceResult, Racer).join(
                Racer, RaceResult.racer_id == Racer.id
            ).filter(
                RaceResult.race_id.in_(race_ids),
                RaceResult.lap_time_best.isnot(None),
                RaceResult.lap_time_best != '',
                RaceResult.lap_time_best != '-'
            ).all()

            best_time = None
            best_lap_str = None
            best_racer_id = None

            for result, racer in results:
                time_seconds = parse_lap_time(result.lap_time_best)
                if time_seconds is not None and (best_time is None or time_seconds < best_time):
                    best_time = time_seconds
                    best_lap_str = result.lap_time_best
                    best_racer_id = racer.id

            if best_lap_str and best_racer_id:
                fastest = LocationFastestLap(
                    location_id=location.id,
                    condition=condition,
                    racer_id=best_racer_id,
                    best_lap=best_lap_str,
                    best_lap_seconds=best_time
                )
                db.session.add(fastest)
                location_fastest_count += 1

    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Estatisticas recalculadas: {updated_count} piloto(s), {best_laps_count} melhores voltas, {location_fastest_count} recordes por local',
        'updated': updated_count,
        'best_laps': best_laps_count,
        'location_fastest': location_fastest_count
    })


@admin.route('/racers/bulk-delete', methods=['POST'])
@login_required
@admin_required
def bulk_delete_racers():
    data = request.get_json()
    racer_ids = data.get('racer_ids', [])

    if not racer_ids:
        return jsonify({'success': False, 'message': 'Nenhum piloto selecionado'}), 400

    # Check which racers have results
    racers_with_results = []
    racers_to_delete = []

    for racer_id in racer_ids:
        racer = Racer.query.get(racer_id)
        if racer:
            results_count = RaceResult.query.filter_by(racer_id=racer_id).count()
            if results_count > 0:
                racers_with_results.append(racer.name)
            else:
                racers_to_delete.append(racer)

    # Delete racers without results
    for racer in racers_to_delete:
        db.session.delete(racer)

    db.session.commit()

    if racers_with_results and not racers_to_delete:
        return jsonify({
            'success': False,
            'message': f'Nenhum piloto excluido. Os seguintes pilotos tem resultados: {", ".join(racers_with_results)}'
        }), 400

    message = f'{len(racers_to_delete)} piloto(s) excluido(s) com sucesso'
    if racers_with_results:
        message += f'. Nao foi possivel excluir: {", ".join(racers_with_results)} (tem resultados)'

    return jsonify({
        'success': True,
        'message': message,
        'count': len(racers_to_delete)
    })


# ============== RACES ==============

@admin.route('/races')
@login_required
@admin_required
def races():
    races_list = Race.query.order_by(Race.date.desc()).all()
    locations = Location.query.order_by(Location.name).all()
    championships = Championship.query.order_by(Championship.name).all()
    racers = Racer.query.order_by(Racer.name).all()
    return render_template('admin/races.html', races=races_list, locations=locations,
                         championships=championships, racers=racers)


@admin.route('/races', methods=['POST'])
@login_required
@admin_required
def create_race():
    data = request.get_json() if request.is_json else request.form

    race_name = data.get('race_name')
    date_str = data.get('date')

    if not race_name or not date_str:
        return jsonify({'success': False, 'message': 'Nome e data sao obrigatorios'}), 400

    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'success': False, 'message': 'Formato de data invalido'}), 400

    race = Race(
        race_name=race_name,
        date=date,
        location_id=int(data.get('location_id')) if data.get('location_id') else None,
        championship_id=int(data.get('championship_id')) if data.get('championship_id') else None,
        track_name=data.get('track_name'),
        weather=data.get('weather'),
        total_laps=int(data.get('total_laps')) if data.get('total_laps') else None,
        winner_id=int(data.get('winner_id')) if data.get('winner_id') else None
    )

    db.session.add(race)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Corrida criada com sucesso', 'race': race.to_dict()})


@admin.route('/races/<int:id>', methods=['PUT'])
@login_required
@admin_required
def update_race(id):
    race = Race.query.get_or_404(id)
    data = request.get_json() if request.is_json else request.form

    if data.get('race_name'):
        race.race_name = data.get('race_name')
    if data.get('date'):
        try:
            race.date = datetime.strptime(data.get('date'), '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'success': False, 'message': 'Formato de data invalido'}), 400
    if 'location_id' in data:
        race.location_id = int(data.get('location_id')) if data.get('location_id') else None
    if 'championship_id' in data:
        race.championship_id = int(data.get('championship_id')) if data.get('championship_id') else None
    if 'track_name' in data:
        race.track_name = data.get('track_name')
    if 'weather' in data:
        race.weather = data.get('weather')
    if 'total_laps' in data:
        race.total_laps = int(data.get('total_laps')) if data.get('total_laps') else None
    if 'winner_id' in data:
        race.winner_id = int(data.get('winner_id')) if data.get('winner_id') else None

    db.session.commit()

    return jsonify({'success': True, 'message': 'Corrida atualizada com sucesso', 'race': race.to_dict()})


@admin.route('/races/<int:id>', methods=['DELETE'])
@login_required
@admin_required
def delete_race(id):
    race = Race.query.get_or_404(id)

    # Check if race has results
    results_count = RaceResult.query.filter_by(race_id=id).count()
    if results_count > 0:
        return jsonify({'success': False, 'message': f'Nao e possivel excluir: corrida tem {results_count} resultados'}), 400

    db.session.delete(race)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Corrida excluida com sucesso'})


# ============== RACE RESULTS ==============

@admin.route('/results')
@login_required
@admin_required
def results():
    race_id = request.args.get('race_id', type=int)

    query = db.session.query(RaceResult, Racer.name, Race.race_name).join(
        Racer, RaceResult.racer_id == Racer.id
    ).join(
        Race, RaceResult.race_id == Race.id
    )

    if race_id:
        query = query.filter(RaceResult.race_id == race_id)

    results_list = query.order_by(Race.date.desc(), RaceResult.position).all()
    races = Race.query.order_by(Race.date.desc()).all()
    racers = Racer.query.order_by(Racer.name).all()

    return render_template('admin/results.html', results=results_list, races=races,
                         racers=racers, selected_race_id=race_id)


@admin.route('/results', methods=['POST'])
@login_required
@admin_required
def create_result():
    data = request.get_json() if request.is_json else request.form

    race_id = data.get('race_id')
    racer_id = data.get('racer_id')

    if not race_id or not racer_id:
        return jsonify({'success': False, 'message': 'Corrida e piloto sao obrigatorios'}), 400

    # Check if result already exists for this race/racer combination
    existing = RaceResult.query.filter_by(race_id=race_id, racer_id=racer_id).first()
    if existing:
        return jsonify({'success': False, 'message': 'Ja existe um resultado para este piloto nesta corrida'}), 400

    result = RaceResult(
        race_id=int(race_id),
        racer_id=int(racer_id),
        position=int(data.get('position')) if data.get('position') else None,
        lap_time_best=data.get('lap_time_best'),
        lap_time_average=data.get('lap_time_average'),
        total_time=data.get('total_time'),
        points_earned=int(data.get('points_earned', 0)) if data.get('points_earned') else 0,
        dnf=data.get('dnf') == 'true' or data.get('dnf') == True,
        laps=int(data.get('laps')) if data.get('laps') else None
    )

    db.session.add(result)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Resultado criado com sucesso', 'result': result.to_dict()})


@admin.route('/results/<int:id>', methods=['PUT'])
@login_required
@admin_required
def update_result(id):
    result = RaceResult.query.get_or_404(id)
    data = request.get_json() if request.is_json else request.form

    if 'position' in data:
        result.position = int(data.get('position')) if data.get('position') else None
    if 'lap_time_best' in data:
        result.lap_time_best = data.get('lap_time_best')
    if 'lap_time_average' in data:
        result.lap_time_average = data.get('lap_time_average')
    if 'total_time' in data:
        result.total_time = data.get('total_time')
    if 'points_earned' in data:
        result.points_earned = int(data.get('points_earned', 0)) if data.get('points_earned') else 0
    if 'dnf' in data:
        result.dnf = data.get('dnf') == 'true' or data.get('dnf') == True
    if 'laps' in data:
        result.laps = int(data.get('laps')) if data.get('laps') else None

    db.session.commit()

    return jsonify({'success': True, 'message': 'Resultado atualizado com sucesso', 'result': result.to_dict()})


@admin.route('/results/<int:id>', methods=['DELETE'])
@login_required
@admin_required
def delete_result(id):
    result = RaceResult.query.get_or_404(id)

    db.session.delete(result)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Resultado excluido com sucesso'})


@admin.route('/results/bulk-create', methods=['POST'])
@login_required
@admin_required
def bulk_create_results():
    data = request.get_json()
    race_id = data.get('race_id')
    results = data.get('results', [])

    if not race_id:
        return jsonify({'success': False, 'message': 'Corrida e obrigatoria'}), 400

    if not results:
        return jsonify({'success': False, 'message': 'Nenhum resultado fornecido'}), 400

    created_count = 0
    skipped = []

    for result_data in results:
        racer_id = result_data.get('racer_id')
        if not racer_id:
            continue

        # Check if result already exists
        existing = RaceResult.query.filter_by(race_id=race_id, racer_id=racer_id).first()
        if existing:
            racer = Racer.query.get(racer_id)
            skipped.append(racer.name if racer else f'ID {racer_id}')
            continue

        result = RaceResult(
            race_id=int(race_id),
            racer_id=int(racer_id),
            position=int(result_data.get('position')) if result_data.get('position') else None,
            lap_time_best=result_data.get('lap_time_best') or None,
            lap_time_average=result_data.get('lap_time_average') or None,
            total_time=result_data.get('total_time') or None,
            points_earned=int(result_data.get('points_earned')) if result_data.get('points_earned') else 0,
            dnf=result_data.get('dnf') == True or result_data.get('dnf') == 'true',
            laps=int(result_data.get('laps')) if result_data.get('laps') else None
        )

        db.session.add(result)
        created_count += 1

    db.session.commit()

    message = f'{created_count} resultado(s) criado(s) com sucesso'
    if skipped:
        message += f'. Ignorados (ja existem): {", ".join(skipped)}'

    return jsonify({
        'success': True,
        'message': message,
        'created': created_count,
        'skipped': skipped
    })


@admin.route('/results/bulk-delete', methods=['POST'])
@login_required
@admin_required
def bulk_delete_results():
    data = request.get_json()
    result_ids = data.get('result_ids', [])

    if not result_ids:
        return jsonify({'success': False, 'message': 'Nenhum resultado selecionado'}), 400

    results = RaceResult.query.filter(RaceResult.id.in_(result_ids)).all()

    if not results:
        return jsonify({'success': False, 'message': 'Nenhum resultado encontrado'}), 404

    count = len(results)
    for result in results:
        db.session.delete(result)

    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'{count} resultado(s) excluido(s) com sucesso',
        'count': count
    })


# ============== LOCATIONS ==============

@admin.route('/locations')
@login_required
@admin_required
def locations():
    locations_list = Location.query.order_by(Location.name).all()
    return render_template('admin/locations.html', locations=locations_list)


@admin.route('/locations', methods=['POST'])
@login_required
@admin_required
def create_location():
    data = request.get_json() if request.is_json else request.form

    name = data.get('name')
    if not name:
        return jsonify({'success': False, 'message': 'Nome e obrigatorio'}), 400

    location = Location(
        name=name,
        rental_duration=data.get('rental_duration'),
        price_per_person=float(data.get('price_per_person')) if data.get('price_per_person') else None,
        min_participants=int(data.get('min_participants')) if data.get('min_participants') else None,
        max_participants=int(data.get('max_participants')) if data.get('max_participants') else None,
        exclusive_info=data.get('exclusive_info'),
        min_height=data.get('min_height'),
        schedule_weekday=data.get('schedule_weekday'),
        schedule_saturday=data.get('schedule_saturday'),
        schedule_sunday=data.get('schedule_sunday'),
        address=data.get('address'),
        neighborhood=data.get('neighborhood'),
        city=data.get('city'),
        instagram=data.get('instagram'),
        website=data.get('website'),
        description=data.get('description'),
        thumbnail_url=data.get('thumbnail_url')
    )

    db.session.add(location)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Local criado com sucesso', 'location': location.to_dict()})


@admin.route('/locations/<int:id>', methods=['PUT'])
@login_required
@admin_required
def update_location(id):
    location = Location.query.get_or_404(id)
    data = request.get_json() if request.is_json else request.form

    if data.get('name'):
        location.name = data.get('name')
    if 'rental_duration' in data:
        location.rental_duration = data.get('rental_duration')
    if 'price_per_person' in data:
        location.price_per_person = float(data.get('price_per_person')) if data.get('price_per_person') else None
    if 'min_participants' in data:
        location.min_participants = int(data.get('min_participants')) if data.get('min_participants') else None
    if 'max_participants' in data:
        location.max_participants = int(data.get('max_participants')) if data.get('max_participants') else None
    if 'exclusive_info' in data:
        location.exclusive_info = data.get('exclusive_info')
    if 'min_height' in data:
        location.min_height = data.get('min_height')
    if 'schedule_weekday' in data:
        location.schedule_weekday = data.get('schedule_weekday')
    if 'schedule_saturday' in data:
        location.schedule_saturday = data.get('schedule_saturday')
    if 'schedule_sunday' in data:
        location.schedule_sunday = data.get('schedule_sunday')
    if 'address' in data:
        location.address = data.get('address')
    if 'neighborhood' in data:
        location.neighborhood = data.get('neighborhood')
    if 'city' in data:
        location.city = data.get('city')
    if 'instagram' in data:
        location.instagram = data.get('instagram')
    if 'website' in data:
        location.website = data.get('website')
    if 'description' in data:
        location.description = data.get('description')
    if 'thumbnail_url' in data:
        location.thumbnail_url = data.get('thumbnail_url')

    db.session.commit()

    return jsonify({'success': True, 'message': 'Local atualizado com sucesso', 'location': location.to_dict()})


@admin.route('/locations/<int:id>', methods=['DELETE'])
@login_required
@admin_required
def delete_location(id):
    location = Location.query.get_or_404(id)

    # Check if location has races
    races_count = Race.query.filter_by(location_id=id).count()
    if races_count > 0:
        return jsonify({'success': False, 'message': f'Nao e possivel excluir: local tem {races_count} corridas'}), 400

    db.session.delete(location)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Local excluido com sucesso'})


# ============== CHAMPIONSHIPS ==============

@admin.route('/championships')
@login_required
@admin_required
def championships():
    championships_list = Championship.query.order_by(Championship.start_date.desc()).all()
    return render_template('admin/championships.html', championships=championships_list)


@admin.route('/championships', methods=['POST'])
@login_required
@admin_required
def create_championship():
    data = request.get_json() if request.is_json else request.form

    name = data.get('name')
    if not name:
        return jsonify({'success': False, 'message': 'Nome e obrigatorio'}), 400

    start_date = None
    end_date = None

    if data.get('start_date'):
        try:
            start_date = datetime.strptime(data.get('start_date'), '%Y-%m-%d').date()
        except ValueError:
            pass

    if data.get('end_date'):
        try:
            end_date = datetime.strptime(data.get('end_date'), '%Y-%m-%d').date()
        except ValueError:
            pass

    championship = Championship(
        name=name,
        description=data.get('description'),
        start_date=start_date,
        end_date=end_date,
        is_active=data.get('is_active') == 'true' or data.get('is_active') == True or data.get('is_active') == 'on'
    )

    db.session.add(championship)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Campeonato criado com sucesso', 'championship': championship.to_dict()})


@admin.route('/championships/<int:id>', methods=['PUT'])
@login_required
@admin_required
def update_championship(id):
    championship = Championship.query.get_or_404(id)
    data = request.get_json() if request.is_json else request.form

    if data.get('name'):
        championship.name = data.get('name')
    if 'description' in data:
        championship.description = data.get('description')
    if 'start_date' in data:
        if data.get('start_date'):
            try:
                championship.start_date = datetime.strptime(data.get('start_date'), '%Y-%m-%d').date()
            except ValueError:
                pass
        else:
            championship.start_date = None
    if 'end_date' in data:
        if data.get('end_date'):
            try:
                championship.end_date = datetime.strptime(data.get('end_date'), '%Y-%m-%d').date()
            except ValueError:
                pass
        else:
            championship.end_date = None
    if 'is_active' in data:
        championship.is_active = data.get('is_active') == 'true' or data.get('is_active') == True or data.get('is_active') == 'on'

    db.session.commit()

    return jsonify({'success': True, 'message': 'Campeonato atualizado com sucesso', 'championship': championship.to_dict()})


@admin.route('/championships/<int:id>', methods=['DELETE'])
@login_required
@admin_required
def delete_championship(id):
    championship = Championship.query.get_or_404(id)

    # Check if championship has races
    races_count = Race.query.filter_by(championship_id=id).count()
    if races_count > 0:
        return jsonify({'success': False, 'message': f'Nao e possivel excluir: campeonato tem {races_count} corridas'}), 400

    db.session.delete(championship)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Campeonato excluido com sucesso'})


# ============== ALBUMS ==============

@admin.route('/albums')
@login_required
@admin_required
def albums():
    # Sort albums by race date (most recent first), albums without race go to the end
    albums_list = Album.query.outerjoin(Race).order_by(
        Race.date.desc().nullslast(),
        Album.created_at.desc()
    ).all()
    races = Race.query.order_by(Race.date.desc()).all()
    return render_template('admin/albums.html', albums=albums_list, races=races)


@admin.route('/albums/<int:id>', methods=['GET'])
@login_required
@admin_required
def get_album(id):
    album = Album.query.get_or_404(id)
    return jsonify(album.to_dict())


@admin.route('/albums', methods=['POST'])
@login_required
@admin_required
def create_album():
    data = request.get_json() if request.is_json else request.form

    name = data.get('name')
    if not name:
        return jsonify({'success': False, 'message': 'Nome e obrigatorio'}), 400

    album = Album(
        name=name,
        description=data.get('description'),
        race_id=int(data.get('race_id')) if data.get('race_id') else None,
        cover_url=data.get('cover_url'),
        google_photos_link=data.get('google_photos_link')
    )

    db.session.add(album)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Album criado com sucesso', 'album': album.to_dict()})


@admin.route('/albums/<int:id>', methods=['PUT'])
@login_required
@admin_required
def update_album(id):
    album = Album.query.get_or_404(id)
    data = request.get_json() if request.is_json else request.form

    if data.get('name'):
        album.name = data.get('name')
    if 'description' in data:
        album.description = data.get('description')
    if 'race_id' in data:
        album.race_id = int(data.get('race_id')) if data.get('race_id') else None
    if 'cover_url' in data:
        album.cover_url = data.get('cover_url')
    if 'google_photos_link' in data:
        album.google_photos_link = data.get('google_photos_link')

    db.session.commit()

    return jsonify({'success': True, 'message': 'Album atualizado com sucesso', 'album': album.to_dict()})


@admin.route('/albums/<int:id>', methods=['DELETE'])
@login_required
@admin_required
def delete_album(id):
    album = Album.query.get_or_404(id)

    db.session.delete(album)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Album excluido com sucesso'})


@admin.route('/albums/<int:album_id>/set-cover', methods=['POST'])
@login_required
@admin_required
def set_album_cover(album_id):
    album = Album.query.get_or_404(album_id)
    data = request.get_json()

    cover_url = data.get('cover_url')
    if not cover_url:
        return jsonify({'success': False, 'message': 'URL da capa e obrigatoria'}), 400

    album.cover_url = cover_url
    db.session.commit()

    return jsonify({'success': True, 'message': 'Capa do album definida com sucesso'})


# ============== MEDIA ITEMS ==============

@admin.route('/albums/<int:album_id>/media', methods=['POST'])
@login_required
@admin_required
def create_media_item(album_id):
    album = Album.query.get_or_404(album_id)
    data = request.get_json() if request.is_json else request.form

    url = data.get('url')
    if not url:
        return jsonify({'success': False, 'message': 'URL e obrigatoria'}), 400

    media_item = MediaItem(
        album_id=album_id,
        media_type=data.get('media_type', 'photo'),
        url=url,
        title=data.get('title'),
        description=data.get('description')
    )

    db.session.add(media_item)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Midia adicionada com sucesso', 'media_item': media_item.to_dict()})


@admin.route('/media/<int:id>', methods=['DELETE'])
@login_required
@admin_required
def delete_media_item(id):
    media_item = MediaItem.query.get_or_404(id)

    db.session.delete(media_item)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Midia excluida com sucesso'})


# ============== FILE UPLOAD ==============

@admin.route('/upload', methods=['POST'])
@login_required
@admin_required
def upload_file():
    """Upload file to R2 storage"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'Nenhum arquivo enviado'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'Nenhum arquivo selecionado'}), 400

        # Validate file type - ONLY PHOTOS ALLOWED
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''

        if ext not in allowed_extensions:
            return jsonify({'success': False, 'message': f'Apenas fotos sao permitidas. Use: JPG, PNG, GIF, WebP'}), 400

        # Validate file size (max 10MB for photos)
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)

        if file_size > 10 * 1024 * 1024:  # 10MB
            return jsonify({'success': False, 'message': 'Arquivo muito grande. Maximo: 10MB'}), 400

        # All uploads are photos
        media_type = 'photo'

        # Upload to R2
        folder = 'photos'
        public_url = upload_to_r2(file, folder)

        return jsonify({
            'success': True,
            'message': 'Arquivo enviado com sucesso',
            'url': public_url,
            'media_type': media_type
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao enviar arquivo: {str(e)}'}), 500


# ============== API ENDPOINTS FOR DROPDOWNS ==============

@admin.route('/api/racers')
@login_required
@admin_required
def api_racers():
    racers = Racer.query.order_by(Racer.name).all()
    return jsonify([{'id': r.id, 'name': r.name} for r in racers])


@admin.route('/api/races')
@login_required
@admin_required
def api_races():
    races = Race.query.order_by(Race.date.desc()).all()
    return jsonify([{'id': r.id, 'race_name': r.race_name, 'date': r.date.isoformat() if r.date else None} for r in races])


@admin.route('/api/locations')
@login_required
@admin_required
def api_locations():
    locations = Location.query.order_by(Location.name).all()
    return jsonify([{'id': l.id, 'name': l.name} for l in locations])


@admin.route('/api/championships')
@login_required
@admin_required
def api_championships():
    championships = Championship.query.order_by(Championship.name).all()
    return jsonify([{'id': c.id, 'name': c.name} for c in championships])


@admin.route('/api/albums/<int:album_id>/media')
@login_required
@admin_required
def api_album_media(album_id):
    """Get all media items for a specific album"""
    album = Album.query.get_or_404(album_id)
    media_items = MediaItem.query.filter_by(album_id=album_id).order_by(MediaItem.created_at.desc()).all()
    return jsonify([item.to_dict() for item in media_items])


# ============== USERS MANAGEMENT ==============

@admin.route('/users')
@login_required
@admin_required
def users():
    users_list = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users_list)


@admin.route('/users', methods=['POST'])
@login_required
@admin_required
def create_user():
    data = request.get_json() if request.is_json else request.form

    email = data.get('email')
    name = data.get('name')
    password = data.get('password')

    if not email or not name or not password:
        return jsonify({'success': False, 'message': 'Email, nome e senha sao obrigatorios'}), 400

    # Check if email already exists
    existing = User.query.filter_by(email=email).first()
    if existing:
        return jsonify({'success': False, 'message': 'Email ja cadastrado'}), 400

    user = User(
        email=email,
        name=name,
        is_admin=data.get('is_admin') == 'true' or data.get('is_admin') == True or data.get('is_admin') == 'on',
        is_active=data.get('is_active', 'true') == 'true' or data.get('is_active', True) == True or data.get('is_active') == 'on'
    )
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Usuario criado com sucesso', 'user': user.to_dict()})


@admin.route('/users/<int:id>', methods=['PUT'])
@login_required
@admin_required
def update_user(id):
    user = User.query.get_or_404(id)
    data = request.get_json() if request.is_json else request.form

    # Prevent user from removing their own admin status
    if user.id == current_user.id and 'is_admin' in data:
        if not (data.get('is_admin') == 'true' or data.get('is_admin') == True or data.get('is_admin') == 'on'):
            return jsonify({'success': False, 'message': 'Voce nao pode remover seu proprio status de administrador'}), 400

    if data.get('name'):
        user.name = data.get('name')
    if data.get('email'):
        # Check if email is already taken by another user
        existing = User.query.filter_by(email=data.get('email')).first()
        if existing and existing.id != id:
            return jsonify({'success': False, 'message': 'Email ja cadastrado por outro usuario'}), 400
        user.email = data.get('email')
    if 'is_admin' in data:
        user.is_admin = data.get('is_admin') == 'true' or data.get('is_admin') == True or data.get('is_admin') == 'on'
    if 'is_active' in data:
        user.is_active = data.get('is_active') == 'true' or data.get('is_active') == True or data.get('is_active') == 'on'
    if 'has_13hp_permission' in data:
        has_permission = data.get('has_13hp_permission') == 'true' or data.get('has_13hp_permission') == True or data.get('has_13hp_permission') == 'on'
        user.has_13hp_permission = has_permission
        # If granting 13HP permission, also set interested to True
        if has_permission:
            user.interested_in_13hp = True
    if data.get('password'):
        user.set_password(data.get('password'))

    db.session.commit()

    return jsonify({'success': True, 'message': 'Usuario atualizado com sucesso', 'user': user.to_dict()})


@admin.route('/users/<int:id>', methods=['DELETE'])
@login_required
@admin_required
def delete_user(id):
    # Prevent user from deleting themselves
    if id == current_user.id:
        return jsonify({'success': False, 'message': 'Voce nao pode excluir sua propria conta'}), 400

    user = User.query.get_or_404(id)

    db.session.delete(user)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Usuario excluido com sucesso'})
