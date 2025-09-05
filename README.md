# Nerds do Kart 🏁

A comprehensive Flask web application for tracking kart racing data among friends. Features a beautiful responsive frontend, PostgreSQL database, and powerful REST API endpoints.

## Features

- **Dashboard**: Overview statistics and recent race information
- **Racers Management**: Complete racer profiles with statistics  
- **Race Results**: Detailed race results and standings
- **Leaderboards**: Championship standings and win-based rankings
- **Racing Locations**: Display karting venues with details, schedules, and pricing
- **PostgreSQL Database**: Real-time data with proper relationships and performance
- **Responsive Design**: Beautiful UI that works on all devices
- **REST API**: Complete set of API endpoints for data access

## Quick Start

1. **Clone and Setup**:
   ```bash
   git clone <repository-url>
   cd kart-race-tracker
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Environment Setup**:
   ```bash
   cp .env.example .env
   # Edit .env and set your DATABASE_URL for local development
   ```

3. **Run the Application**:
   ```bash
   python app.py
   ```

4. **Access the Application**:
   - Web Interface: http://localhost:5003
   - API Documentation: See endpoints below

## Project Structure

```
kart-race-tracker/
├── app.py                 # Main Flask application
├── models.py              # SQLAlchemy database models
├── requirements.txt       # Python dependencies
├── Procfile              # Railway/Heroku deployment
├── runtime.txt           # Python version specification
├── .env.example          # Environment variables template
├── templates/
│   └── index.html        # Main HTML template
├── static/
│   ├── css/
│   │   └── style.css     # Styling
│   ├── js/
│   │   └── app.js        # Frontend JavaScript
│   └── images/           # Venue photos
└── logo_nerds.jpg        # App logo
```

## Database Schema

The application uses PostgreSQL with these main tables:
- **Racers**: Racer profiles and statistics
- **Locations**: Racing venues with details and pricing
- **Races**: Individual race events
- **RaceResults**: Detailed race results and lap times

## API Endpoints

### Racers
- `GET /api/racers` - Get all racers
- `GET /api/racers/<id>` - Get specific racer with recent results

### Races
- `GET /api/races` - Get all races
- `GET /api/races/<id>` - Get specific race with results
- `GET /api/recent-races` - Get 5 most recent races

### Results
- `GET /api/results` - Get all race results (with racer and race info)
- `GET /api/values` - Alias for results endpoint

### Statistics & Rankings
- `GET /api/leaderboard` - Racers ranked by wins
- `GET /api/standings` - Championship standings by points
- `GET /api/stats` - General statistics (totals, fastest lap, etc.)

### Locations
- `GET /api/locations` - Get all racing locations
- `GET /api/locations/<id>` - Get specific location details

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

## Deployment

### Railway (Recommended)
1. Connect your GitHub repository to Railway
2. Railway automatically provides `DATABASE_URL` for PostgreSQL
3. Deploy with zero configuration

### Environment Variables
- `DATABASE_URL`: PostgreSQL connection string (automatically provided by Railway)
- `PORT`: Server port (optional, defaults to 5003)
- `ENVIRONMENT`: Set to "production" for production deployment

## Development

### Local Development
```bash
# Set your database URL in .env
DATABASE_URL=postgresql://username:password@host:port/database

# Run the application
python app.py
```

### Technologies Used
- **Backend**: Flask, SQLAlchemy, PostgreSQL
- **Frontend**: HTML5, CSS3, JavaScript (ES6)
- **Database**: PostgreSQL with proper relationships
- **Deployment**: Railway, GitHub

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

Race on! 🏎️💨