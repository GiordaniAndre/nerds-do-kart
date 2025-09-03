from flask import Flask, jsonify, render_template, send_file
import pandas as pd
from datetime import datetime
import os

app = Flask(__name__)

class KartRaceData:
    def __init__(self, data_dir='data'):
        self.data_dir = data_dir
        self.csv_files = {
            'racers': f'{data_dir}/racers.csv',
            'races': f'{data_dir}/races.csv',
            'results': f'{data_dir}/race_results.csv',
            'locations': f'{data_dir}/locations.csv'
        }
        self.last_modified = {}
        self.load_data()
    
    def check_files_modified(self):
        """Check if any CSV files have been modified since last load"""
        modified = False
        for name, file_path in self.csv_files.items():
            try:
                current_modified = os.path.getmtime(file_path)
                if name not in self.last_modified or current_modified > self.last_modified[name]:
                    self.last_modified[name] = current_modified
                    modified = True
            except Exception as e:
                print(f"Error checking file modification for {file_path}: {e}")
        return modified
    
    def load_data(self):
        """Load data from CSV files"""
        try:
            self.racers_df = pd.read_csv(self.csv_files['racers'])
            self.races_df = pd.read_csv(self.csv_files['races'])
            self.results_df = pd.read_csv(self.csv_files['results'])
            self.locations_df = pd.read_csv(self.csv_files['locations']) if os.path.exists(self.csv_files['locations']) else pd.DataFrame()
            
            # Update last modified times
            for name, file_path in self.csv_files.items():
                self.last_modified[name] = os.path.getmtime(file_path)
                
            print(f"Data reloaded from CSV files in {self.data_dir}")
        except Exception as e:
            print(f"Error loading data: {e}")
            self.racers_df = pd.DataFrame()
            self.races_df = pd.DataFrame()
            self.results_df = pd.DataFrame()
            self.locations_df = pd.DataFrame()
    
    def get_data(self, df_name):
        """Get data with auto-reload check"""
        if self.check_files_modified():
            self.load_data()
        return getattr(self, f'{df_name}_df')

data_manager = KartRaceData()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/logo_nerds.jpg')
def logo():
    return send_file('logo_nerds.jpg')

@app.route('/velopark-cover.jpg')
def velopark_cover():
    return send_file('c821b246-b93b-400f-a948-dfc6286d3df5.jpeg')

@app.route('/api/racers', methods=['GET'])
def get_racers():
    racers_df = data_manager.get_data('racers')
    racers = racers_df.to_dict('records')
    return jsonify({
        'status': 'success',
        'count': len(racers),
        'data': racers
    })

@app.route('/api/racers/<int:racer_id>', methods=['GET'])
def get_racer(racer_id):
    racers_df = data_manager.get_data('racers')
    results_df = data_manager.get_data('results')
    racer = racers_df[racers_df['racer_id'] == racer_id]
    if racer.empty:
        return jsonify({'status': 'error', 'message': 'Racer not found'}), 404
    
    racer_results = results_df[results_df['racer_id'] == racer_id]
    racer_data = racer.to_dict('records')[0]
    racer_data['recent_results'] = racer_results.head(10).to_dict('records')
    
    return jsonify({
        'status': 'success',
        'data': racer_data
    })

@app.route('/api/races', methods=['GET'])
def get_races():
    races_df = data_manager.get_data('races')
    races = races_df.to_dict('records')
    for race in races:
        race['date'] = str(race['date'])
    
    return jsonify({
        'status': 'success',
        'count': len(races),
        'data': races
    })

@app.route('/api/races/<int:race_id>', methods=['GET'])
def get_race(race_id):
    races_df = data_manager.get_data('races')
    results_df = data_manager.get_data('results')
    racers_df = data_manager.get_data('racers')
    race = races_df[races_df['race_id'] == race_id]
    if race.empty:
        return jsonify({'status': 'error', 'message': 'Race not found'}), 404
    
    race_results = results_df[results_df['race_id'] == race_id]
    race_results = race_results.merge(racers_df[['racer_id', 'name']], on='racer_id')
    race_results = race_results.sort_values('position')
    
    race_data = race.to_dict('records')[0]
    race_data['date'] = str(race_data['date'])
    race_data['results'] = race_results.to_dict('records')
    
    return jsonify({
        'status': 'success',
        'data': race_data
    })

@app.route('/api/values', methods=['GET'])
@app.route('/api/results', methods=['GET'])
def get_race_results():
    results_df = data_manager.get_data('results')
    racers_df = data_manager.get_data('racers')
    races_df = data_manager.get_data('races')
    results = results_df.merge(
        racers_df[['racer_id', 'name']], 
        on='racer_id'
    ).merge(
        races_df[['race_id', 'race_name', 'date']], 
        on='race_id'
    )
    
    results_list = results.to_dict('records')
    for result in results_list:
        result['date'] = str(result['date'])
    
    return jsonify({
        'status': 'success',
        'count': len(results_list),
        'data': results_list
    })

@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    racers_df = data_manager.get_data('racers')
    leaderboard = racers_df.sort_values('wins', ascending=False)
    return jsonify({
        'status': 'success',
        'data': leaderboard.to_dict('records')
    })

@app.route('/api/standings', methods=['GET'])
def get_championship_standings():
    results_df = data_manager.get_data('results')
    racers_df = data_manager.get_data('racers')
    standings = results_df.groupby('racer_id').agg({
        'points_earned': 'sum',
        'position': lambda x: (x == 1).sum(),  # wins
        'result_id': 'count'  # total races
    }).reset_index()
    
    standings.columns = ['racer_id', 'total_points', 'wins', 'races_participated']
    standings = standings.merge(racers_df[['racer_id', 'name']], on='racer_id')
    standings = standings.sort_values('total_points', ascending=False)
    
    return jsonify({
        'status': 'success',
        'data': standings.to_dict('records')
    })

@app.route('/api/stats', methods=['GET'])
def get_stats():
    racers_df = data_manager.get_data('racers')
    races_df = data_manager.get_data('races')
    results_df = data_manager.get_data('results')
    total_racers = len(racers_df)
    total_races = len(races_df)
    total_results = len(results_df)
    
    if not results_df.empty:
        # Convert lap_time_best to numeric, handling any string values
        results_df_clean = results_df.copy()
        results_df_clean['lap_time_best'] = pd.to_numeric(results_df_clean['lap_time_best'], errors='coerce')
        
        # Find the fastest lap (excluding NaN values)
        valid_times = results_df_clean.dropna(subset=['lap_time_best'])
        if not valid_times.empty:
            fastest_lap = valid_times.loc[valid_times['lap_time_best'].idxmin()]
            fastest_racer = racers_df[racers_df['racer_id'] == fastest_lap['racer_id']]['name'].iloc[0]
        else:
            fastest_lap = None
            fastest_racer = None
    else:
        fastest_lap = None
        fastest_racer = None
    
    stats = {
        'total_racers': total_racers,
        'total_races': total_races,
        'total_results': total_results,
        'fastest_lap_time': float(fastest_lap['lap_time_best']) if fastest_lap is not None else None,
        'fastest_lap_racer': fastest_racer
    }
    
    return jsonify({
        'status': 'success',
        'data': stats
    })

@app.route('/api/recent-races', methods=['GET'])
def get_recent_races():
    races_df = data_manager.get_data('races')
    recent = races_df.sort_values('date', ascending=False).head(5)
    races_list = recent.to_dict('records')
    for race in races_list:
        race['date'] = str(race['date'])
    
    return jsonify({
        'status': 'success',
        'data': races_list
    })

@app.route('/api/reload', methods=['POST'])
def reload_data():
    """Manual endpoint to force reload data"""
    try:
        data_manager.load_data()
        return jsonify({
            'status': 'success',
            'message': 'Data reloaded successfully'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to reload data: {str(e)}'
        }), 500

@app.route('/api/locations', methods=['GET'])
def get_locations():
    """Get all racing locations"""
    locations_df = data_manager.get_data('locations')
    if locations_df.empty:
        return jsonify([])
    
    locations = locations_df.to_dict('records')
    return jsonify(locations)

@app.route('/api/locations/<int:location_id>', methods=['GET'])
def get_location(location_id):
    """Get specific location by ID"""
    locations_df = data_manager.get_data('locations')
    if locations_df.empty:
        return jsonify({'error': 'No locations data available'}), 404
    
    location = locations_df[locations_df['location_id'] == location_id]
    
    if location.empty:
        return jsonify({'error': f'Location {location_id} not found'}), 404
    
    return jsonify(location.to_dict('records')[0])

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5003))
    debug = os.environ.get('ENVIRONMENT') != 'production'
    
    if debug:
        print("🏁 Nerds do Kart - Development Server")
        print(f"📍 Local access: http://localhost:{port}")
        print("🚀 Server running... Press Ctrl+C to stop")
    else:
        print("🏁 Nerds do Kart - Production Server")
        print("🌐 Live at: https://nerdsdokart.com.br")
    
    app.run(debug=debug, host='0.0.0.0', port=port)