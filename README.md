# Kart Race Tracker 🏁

A comprehensive Flask web application for tracking kart racing data among friends. Features a beautiful responsive frontend and powerful REST API endpoints for managing racers, races, and results.

## Features

- **Dashboard**: Overview statistics and recent race information
- **Racers Management**: Complete racer profiles with statistics
- **Race Results**: Detailed race results and standings  
- **Leaderboards**: Championship standings and win-based rankings
- **Excel Integration**: Reads data from Excel file with multiple sheets
- **Responsive Design**: Beautiful UI that works on all devices
- **REST API**: Complete set of API endpoints for data access

## Quick Start

1. **Clone and Setup**:
   ```bash
   cd kart-race-tracker
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Run the Application**:
   ```bash
   python app.py
   ```

3. **Access the Application**:
   - Web Interface: http://localhost:5000
   - API Documentation: See endpoints below

## Project Structure

```
kart-race-tracker/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── data/
│   └── kart_racing_data.xlsx  # Excel file with race data
├── templates/
│   └── index.html        # Main HTML template
├── static/
│   ├── css/
│   │   └── style.css     # Styling
│   └── js/
│       └── app.js        # Frontend JavaScript
└── venv/                 # Virtual environment (created after setup)
```

## Excel Data Structure

The application reads from `data/kart_racing_data.xlsx` with three sheets:

### Racers Sheet
- `racer_id`: Unique identifier
- `name`: Racer name
- `age`: Age
- `experience_years`: Years of experience
- `total_races`: Total races participated
- `wins`: Number of wins
- `podium_finishes`: Number of podium finishes

### Races Sheet
- `race_id`: Unique identifier
- `race_name`: Race name
- `date`: Race date
- `track_name`: Track name
- `weather`: Weather conditions
- `total_laps`: Number of laps
- `winner_id`: ID of the winner

### Race_Results Sheet
- `result_id`: Unique identifier
- `race_id`: Race reference
- `racer_id`: Racer reference
- `position`: Final position
- `lap_time_best`: Best lap time
- `lap_time_average`: Average lap time
- `total_time`: Total race time
- `points_earned`: Championship points
- `dnf`: Did not finish (boolean)

## API Endpoints

### Racers
- `GET /api/racers` - Get all racers
- `GET /api/racers/<id>` - Get specific racer with recent results

### Races
- `GET /api/races` - Get all races
- `GET /api/races/<id>` - Get specific race with results
- `GET /api/recent-races` - Get 5 most recent races

### Results/Values
- `GET /api/results` - Get all race results (with racer and race info)
- `GET /api/values` - Alias for results endpoint

### Statistics & Rankings
- `GET /api/leaderboard` - Racers ranked by wins
- `GET /api/standings` - Championship standings by points
- `GET /api/stats` - General statistics (totals, fastest lap, etc.)

### Example API Response
```json
{
  "status": "success",
  "count": 10,
  "data": [
    {
      "racer_id": 1,
      "name": "Alex Thunder",
      "age": 22,
      "wins": 8,
      "total_races": 45
    }
  ]
}
```

## Editing Race Data

### 🔄 Auto-Reload Feature (No Restart Needed!)
The application automatically detects when you edit the Excel file and reloads data on the next API request. Just:

1. **Edit Excel File**: Open `data/kart_racing_data.xlsx` in Excel/LibreOffice
2. **Change Racer Names**: Edit any data in the Racers, Races, or Race_Results sheets
3. **Save the File**: The website will automatically update on the next page refresh!

### Manual Methods
- **Force Reload**: Send POST to `/api/reload` 
- **Restart Server**: Stop and restart `python app.py` (old method)

### Example: Changing Racer Names
1. Open `data/kart_racing_data.xlsx`
2. Go to "Racers" sheet
3. Change "Alex Thunder" to "Alex Lightning" 
4. Save the file
5. Refresh the website - the change appears immediately!

## Customization

### Modifying the Frontend
- Edit `templates/index.html` for structure changes
- Modify `static/css/style.css` for styling
- Update `static/js/app.js` for functionality changes

### Adding New API Endpoints
Add new routes in `app.py` following the existing pattern:

```python
@app.route('/api/my-endpoint', methods=['GET'])
def my_endpoint():
    # Your logic here
    return jsonify({
        'status': 'success',
        'data': your_data
    })
```

## Mock Data

The project includes comprehensive mock data with:
- 10 racers with varied statistics
- 25 races across 5 different tracks
- Realistic race results with lap times and points
- Weather conditions and track variations

## Requirements

- Python 3.7+
- Flask 3.1.2
- pandas 2.3.2
- openpyxl 3.1.5

## License

This project is open source. Feel free to modify and extend it for your kart racing adventures!

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

Race on! 🏎️💨