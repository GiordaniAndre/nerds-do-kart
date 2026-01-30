class KartRaceTracker {
    constructor() {
        this.apiBase = '/api';
        this.init();
    }

    async init() {
        await this.loadDashboard();
        await this.loadLocations();
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const section = e.target.closest('.nav-btn').getAttribute('onclick').match(/'(.+)'/)[1];
                this.showSection(section);
            });
        });
    }

    showSection(sectionName) {
        // Hide all sections
        document.querySelectorAll('.section').forEach(section => {
            section.classList.remove('active');
        });

        // Remove active class from all nav buttons
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.classList.remove('active');
        });

        // Show selected section
        document.getElementById(sectionName).classList.add('active');

        // Add active class to corresponding nav button
        document.querySelector(`[onclick="showSection('${sectionName}')"]`).classList.add('active');

        // Load section data
        this.loadSectionData(sectionName);
    }

    async loadSectionData(section) {
        switch (section) {
            case 'dashboard':
                await this.loadDashboard();
                break;
            case 'racers':
                await this.loadRacers();
                break;
            case 'races':
                await this.loadRaces();
                break;
            case 'leaderboard':
                await this.loadLeaderboard();
                break;
            case 'standings':
                await this.loadStandings();
                break;
            case 'media':
                this.initMediaSection();
                break;
        }
    }

    async fetchAPI(endpoint) {
        try {
            const response = await fetch(`${this.apiBase}${endpoint}`);
            const data = await response.json();
            if (data.status === 'success') {
                return data.data;
            }
            throw new Error(data.message || 'API Error');
        } catch (error) {
            console.error('API Error:', error);
            return null;
        }
    }

    async loadDashboard() {
        const stats = await this.fetchAPI('/stats');
        const recentRaces = await this.fetchAPI('/recent-races');
        const fastestByLocation = await this.fetchAPI('/fastest-by-location');

        if (stats) {
            document.getElementById('total-racers').textContent = stats.total_racers;
            document.getElementById('total-races').textContent = stats.total_races;
        }

        if (fastestByLocation) {
            this.renderFastestByLocation(fastestByLocation);
        }

        if (recentRaces) {
            this.renderRecentRaces(recentRaces);
        }
    }

    renderFastestByLocation(data) {
        const container = document.getElementById('fastest-by-location-grid');
        if (!container) return;

        if (data.length === 0) {
            container.innerHTML = '<p class="no-data">Nenhum dado disponivel</p>';
            return;
        }

        container.innerHTML = data.map(item => `
            <div class="fastest-location-card">
                <div class="location-name">
                    <i class="fas fa-map-marker-alt"></i>
                    ${item.location_name}
                </div>
                <div class="weather-times">
                    ${item.dry ? `
                        <div class="weather-time dry">
                            <div class="weather-label">
                                <i class="fas fa-sun"></i> Seco
                            </div>
                            <div class="fastest-time">
                                <i class="fas fa-stopwatch"></i>
                                ${item.dry.fastest_lap}
                            </div>
                            <div class="fastest-racer-name">
                                <i class="fas fa-user"></i>
                                ${item.dry.fastest_racer}
                            </div>
                        </div>
                    ` : ''}
                    ${item.wet ? `
                        <div class="weather-time wet">
                            <div class="weather-label">
                                <i class="fas fa-cloud-rain"></i> Molhado
                            </div>
                            <div class="fastest-time">
                                <i class="fas fa-stopwatch"></i>
                                ${item.wet.fastest_lap}
                            </div>
                            <div class="fastest-racer-name">
                                <i class="fas fa-user"></i>
                                ${item.wet.fastest_racer}
                            </div>
                        </div>
                    ` : ''}
                    ${item.indoor ? `
                        <div class="weather-time indoor">
                            <div class="weather-label">
                                <i class="fas fa-warehouse"></i> Indoor
                            </div>
                            <div class="fastest-time">
                                <i class="fas fa-stopwatch"></i>
                                ${item.indoor.fastest_lap}
                            </div>
                            <div class="fastest-racer-name">
                                <i class="fas fa-user"></i>
                                ${item.indoor.fastest_racer}
                            </div>
                        </div>
                    ` : ''}
                </div>
            </div>
        `).join('');
    }

    renderRecentRaces(races) {
        const container = document.getElementById('recent-races-list');
        container.innerHTML = races.map(race => `
            <div class="race-card">
                <h4>${race.race_name}</h4>
                <p><i class="fas fa-calendar"></i> ${this.formatDate(race.date)}</p>
                <p><i class="fas fa-map-marker-alt"></i> ${race.track_name}</p>
                <p><i class="fas fa-cloud"></i> ${this.translateWeather(race.weather)}</p>
                <p><i class="fas fa-flag"></i> ${race.total_laps} voltas</p>
            </div>
        `).join('');
    }

    async loadRacers() {
        const racers = await this.fetchAPI('/racers');
        if (racers) {
            this.racersData = racers;
            this.renderRacers(racers);
        }
    }

    filterRacers(searchTerm) {
        if (!this.racersData) return;

        const term = searchTerm.toLowerCase().trim();
        if (term === '') {
            this.renderRacers(this.racersData);
            return;
        }

        const filtered = this.racersData.filter(racer =>
            racer.name.toLowerCase().includes(term)
        );
        this.renderRacers(filtered);
    }

    renderRacers(racers) {
        const container = document.getElementById('racers-grid');
        if (!container) return;

        if (racers.length === 0) {
            container.innerHTML = '<p class="no-results">Nenhum piloto encontrado</p>';
            return;
        }

        container.innerHTML = racers.map(racer => `
            <div class="racer-card">
                <h3><i class="fas fa-user"></i> ${racer.name}</h3>
                <div class="racer-stats">
                    <div class="racer-stat-row">
                        <span class="stat-label"><i class="fas fa-birthday-cake"></i> Idade:</span>
                        <span class="stat-value">${racer.age || '-'}</span>
                    </div>
                    <div class="racer-stat-row">
                        <span class="stat-label"><i class="fas fa-flag-checkered"></i> Corridas:</span>
                        <span class="stat-value">${racer.total_races || 0}</span>
                    </div>
                    <div class="racer-stat-row">
                        <span class="stat-label"><i class="fas fa-trophy"></i> Vitorias:</span>
                        <span class="stat-value">${racer.wins || 0}</span>
                    </div>
                    <div class="racer-stat-row">
                        <span class="stat-label"><i class="fas fa-medal"></i> Podios:</span>
                        <span class="stat-value">${racer.podium_finishes || 0}</span>
                    </div>
                </div>
                ${racer.best_laps_by_location && racer.best_laps_by_location.length > 0 ? `
                    <div class="racer-best-laps">
                        <h4><i class="fas fa-stopwatch"></i> Melhores Voltas</h4>
                        <div class="best-laps-list">
                            ${racer.best_laps_by_location.map(loc => `
                                <div class="best-lap-location">
                                    <div class="lap-location-name">${loc.location_name}</div>
                                    <div class="lap-conditions">
                                        ${loc.dry ? `<span class="lap-condition dry"><i class="fas fa-sun"></i> ${loc.dry}</span>` : ''}
                                        ${loc.wet ? `<span class="lap-condition wet"><i class="fas fa-cloud-rain"></i> ${loc.wet}</span>` : ''}
                                        ${loc.indoor ? `<span class="lap-condition indoor"><i class="fas fa-warehouse"></i> ${loc.indoor}</span>` : ''}
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}
            </div>
        `).join('');
    }

    async loadRaces() {
        const races = await this.fetchAPI('/races');
        if (races) {
            this.renderRaces(races);
        }
    }

    renderRaces(races) {
        const container = document.getElementById('races-list');
        container.innerHTML = races.map((race, index) => `
            <div class="race-dropdown">
                <div class="race-dropdown-header" onclick="app.toggleRaceResults(${index}, ${race.race_id})">
                    <div class="race-dropdown-info">
                        <h4>${race.race_name}</h4>
                        <p class="race-meta">
                            <span><i class="fas fa-calendar"></i> ${this.formatDate(race.date)}</span>
                            <span><i class="fas fa-map-marker-alt"></i> ${race.track_name || 'N/A'}</span>
                            <span><i class="fas fa-cloud"></i> ${this.translateWeather(race.weather)}</span>
                            <span><i class="fas fa-flag"></i> ${race.total_laps || 'N/A'} voltas</span>
                        </p>
                    </div>
                    <div class="race-dropdown-toggle">
                        <i class="fas fa-chevron-down" id="race-toggle-icon-${index}"></i>
                    </div>
                </div>
                <div class="race-results-container collapsed" id="race-results-${index}">
                    <div class="race-results-loading">
                        <i class="fas fa-spinner fa-spin"></i> Carregando resultados...
                    </div>
                </div>
            </div>
        `).join('');
    }

    async toggleRaceResults(index, raceId) {
        const container = document.getElementById(`race-results-${index}`);
        const icon = document.getElementById(`race-toggle-icon-${index}`);

        if (container.classList.contains('collapsed')) {
            container.classList.remove('collapsed');
            icon.classList.remove('fa-chevron-down');
            icon.classList.add('fa-chevron-up');

            // Load results if not already loaded
            if (container.dataset.loaded !== 'true') {
                const race = await this.fetchAPI(`/races/${raceId}`);
                if (race && race.results && race.results.length > 0) {
                    container.innerHTML = `
                        <table class="race-results-table">
                            <thead>
                                <tr>
                                    <th>Pos</th>
                                    <th>Piloto</th>
                                    <th>Voltas</th>
                                    <th>Tempo Total</th>
                                    <th>Melhor Volta</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${race.results.map(result => `
                                    <tr class="${result.dnf ? 'dnf-row' : ''}">
                                        <td>${result.position || '-'}</td>
                                        <td>${result.name}${result.dnf ? ' <span class="dnf-badge">DNF</span>' : ''}</td>
                                        <td>${result.laps || '-'}</td>
                                        <td>${result.total_time || '-'}</td>
                                        <td>${result.lap_time_best || '-'}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    `;
                } else {
                    container.innerHTML = '<p class="no-results">Nenhum resultado registrado para esta corrida.</p>';
                }
                container.dataset.loaded = 'true';
            }
        } else {
            container.classList.add('collapsed');
            icon.classList.remove('fa-chevron-up');
            icon.classList.add('fa-chevron-down');
        }
    }

    async loadLeaderboard() {
        const leaderboard = await this.fetchAPI('/leaderboard');
        if (leaderboard) {
            this.renderTable('leaderboard-table', leaderboard, [
                { key: 'name', label: 'Piloto' },
                { key: 'total_races', label: 'Corridas' },
                { key: 'wins', label: 'Vitorias' },
                { key: 'podium_finishes', label: 'Podios' }
            ]);
        }
    }

    async loadStandings() {
        const standings = await this.fetchAPI('/standings');
        if (standings) {
            this.renderTable('standings-table', standings, [
                { key: 'name', label: 'Piloto' },
                { key: 'total_points', label: 'Pontos' },
                { key: 'wins', label: 'Vitórias' },
                { key: 'races_participated', label: 'Corridas' }
            ], true);
        }
    }

    renderTable(containerId, data, columns, showPositions = false) {
        const container = document.getElementById(containerId);
        const headers = showPositions ? 
            ['Posição', ...columns.map(col => col.label)] : 
            columns.map(col => col.label);

        const tableHTML = `
            <table class="table">
                <thead>
                    <tr>
                        ${headers.map(header => `<th>${header}</th>`).join('')}
                    </tr>
                </thead>
                <tbody>
                    ${data.map((row, index) => `
                        <tr class="${showPositions && index < 3 ? `position-${index + 1}` : ''}">
                            ${showPositions ? `<td><strong>${index + 1}</strong></td>` : ''}
                            ${columns.map(col => `<td>${row[col.key]}</td>`).join('')}
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;

        container.innerHTML = tableHTML;
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('pt-BR', { 
            year: 'numeric', 
            month: 'short', 
            day: 'numeric' 
        });
    }

    translateWeather(weather) {
        const translations = {
            'Sunny': 'Ensolarado',
            'Cloudy': 'Nublado',
            'Rainy': 'Chuvoso',
            'Windy': 'Ventoso'
        };
        return translations[weather] || weather;
    }

    // Media Section Functions
    initMediaSection() {
        // Load albums from API
        this.loadAlbums();
    }

    async loadAlbums() {
        try {
            const response = await fetch('/api/albums');
            const result = await response.json();

            if (result.status === 'success' && result.data.length > 0) {
                this.displayAlbums(result.data);
            } else {
                this.showEmptyMediaState();
            }
        } catch (error) {
            console.error('Error loading albums:', error);
            this.showEmptyMediaState();
        }
    }

    displayAlbums(albums) {
        const albumsGrid = document.getElementById('albums-grid');

        if (albums.length > 0) {
            albumsGrid.innerHTML = albums.map(album => this.createAlbumCard(album)).join('');
        } else {
            albumsGrid.innerHTML = '<div class="empty-state"><i class="fas fa-folder"></i><p>Nenhum álbum ainda</p></div>';
        }

        this.loadVideos();
        this.loadPhotosByRace();
    }

    async loadVideos() {
        const videosGrid = document.getElementById('videos-grid');
        try {
            const response = await fetch('/api/videos');
            const result = await response.json();

            if (result.status === 'success' && result.data.length > 0) {
                videosGrid.innerHTML = result.data.map(video => this.createVideoCard(video)).join('');
            } else {
                videosGrid.innerHTML = '<div class="empty-state"><i class="fas fa-video"></i><p>Nenhum vídeo ainda</p></div>';
            }
        } catch (error) {
            console.error('Error loading videos:', error);
            videosGrid.innerHTML = '<div class="empty-state"><i class="fas fa-video"></i><p>Erro ao carregar vídeos</p></div>';
        }
    }

    async loadPhotosByRace() {
        try {
            const response = await fetch('/api/photos/by-race');
            const result = await response.json();

            if (result.status === 'success' && result.data.length > 0) {
                this.displayPhotosByRace(result.data);
            } else {
                this.showEmptyPhotosState();
            }
        } catch (error) {
            console.error('Error loading photos by race:', error);
            this.showEmptyPhotosState();
        }
    }

    displayPhotosByRace(raceAlbums) {
        const container = document.getElementById('photos-by-race-container');

        const html = raceAlbums.map((raceAlbum, index) => `
            <div class="race-photos-section">
                <div class="race-photos-header collapsible" onclick="app.toggleRacePhotos(${index})">
                    <div class="race-photos-header-content">
                        <h3>
                            <i class="fas fa-flag-checkered"></i>
                            ${raceAlbum.race_name}
                        </h3>
                        <p class="album-subtitle">
                            ${raceAlbum.album_name} • ${raceAlbum.photo_count} foto${raceAlbum.photo_count !== 1 ? 's' : ''}
                            ${raceAlbum.race_date ? ` • ${new Date(raceAlbum.race_date).toLocaleDateString('pt-BR')}` : ''}
                        </p>
                    </div>
                    <div class="race-photos-toggle">
                        <i class="fas fa-chevron-down" id="toggle-icon-${index}"></i>
                    </div>
                </div>
                <div class="race-photos-grid collapsed" id="race-photos-grid-${index}">
                    ${raceAlbum.photos.map(photo => `
                        <div class="photo-item" onclick="app.openImage('${photo.url}')">
                            <img src="${photo.url}" alt="${photo.title || 'Foto'}" loading="lazy">
                        </div>
                    `).join('')}
                </div>
            </div>
        `).join('');

        container.innerHTML = html;
    }

    toggleRacePhotos(index) {
        const grid = document.getElementById(`race-photos-grid-${index}`);
        const icon = document.getElementById(`toggle-icon-${index}`);

        if (grid.classList.contains('collapsed')) {
            grid.classList.remove('collapsed');
            icon.classList.remove('fa-chevron-down');
            icon.classList.add('fa-chevron-up');
        } else {
            grid.classList.add('collapsed');
            icon.classList.remove('fa-chevron-up');
            icon.classList.add('fa-chevron-down');
        }
    }

    showEmptyPhotosState() {
        const container = document.getElementById('photos-by-race-container');
        container.innerHTML = `
            <div class="empty-state-card">
                <i class="fas fa-images"></i>
                <h3>Nenhuma foto ainda</h3>
                <p>As fotos das corridas aparecerão aqui organizadas por corrida</p>
            </div>
        `;
    }

    createAlbumCard(album) {
        // Prioritize photos for cover image
        let coverImage = album.cover_url;

        // If no cover_url, find first photo in media_preview
        if (!coverImage && album.media_preview) {
            const firstPhoto = album.media_preview.find(item => item.media_type === 'photo');
            if (firstPhoto) {
                coverImage = firstPhoto.url;
            }
        }

        const raceName = album.race_name ? `<div class="album-race"><i class="fas fa-flag-checkered"></i> ${album.race_name}</div>` : '';

        return `
            <div class="album-card" onclick="app.openAlbum(${album.id})">
                <div class="album-cover">
                    ${coverImage ?
                        `<img src="${coverImage}" alt="${album.name}" onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 200 200%22><rect fill=%22%23667%22 width=%22200%22 height=%22200%22/><text x=%2250%%22 y=%2250%%22 text-anchor=%22middle%22 dy=%22.3em%22 fill=%22%23fff%22 font-size=%2216%22>Foto</text></svg>'">`
                        : `<div class="album-placeholder"><i class="fas fa-images"></i></div>`
                    }
                    ${album.media_count ? `<div class="album-count"><i class="fas fa-photo-video"></i> ${album.media_count}</div>` : ''}
                </div>
                <div class="album-info">
                    <h3>${album.name}</h3>
                    ${raceName}
                    ${album.description ? `<p class="album-description">${album.description}</p>` : ''}
                    ${album.google_photos_link ? `<a href="${album.google_photos_link}" target="_blank" class="album-link" onclick="event.stopPropagation()"><i class="fas fa-external-link-alt"></i> Ver no Google Photos</a>` : ''}
                </div>
            </div>
        `;
    }

    createVideoCard(video) {
        const youtubeId = this.extractYouTubeId(video.url);
        const thumbnail = youtubeId ?
            `https://img.youtube.com/vi/${youtubeId}/mqdefault.jpg` :
            'data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 200 200%22><rect fill=%22%23c00%22 width=%22200%22 height=%22200%22/><text x=%2250%%22 y=%2250%%22 text-anchor=%22middle%22 dy=%22.3em%22 fill=%22%23fff%22 font-size=%2216%22>Video</text></svg>';

        return `
            <div class="video-card" onclick="app.openVideo('${video.url}')">
                <div class="video-thumbnail">
                    <img src="${thumbnail}" alt="${video.title || 'Video'}">
                    <div class="video-play-overlay"><i class="fas fa-play-circle"></i></div>
                </div>
                <div class="video-info">
                    <h4>${video.title || 'Vídeo'}</h4>
                    ${video.description ? `<p>${video.description}</p>` : ''}
                    ${video.album_name ? `<small><i class="fas fa-folder"></i> ${video.album_name}</small>` : ''}
                </div>
            </div>
        `;
    }

    extractYouTubeId(url) {
        if (!url) return null;
        const patterns = [
            /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)/,
            /^([a-zA-Z0-9_-]{11})$/
        ];

        for (const pattern of patterns) {
            const match = url.match(pattern);
            if (match) return match[1];
        }
        return null;
    }

    async openAlbum(albumId) {
        try {
            const response = await fetch(`/api/albums/${albumId}`);
            const result = await response.json();

            if (result.status === 'success') {
                this.showAlbumModal(result.data);
            }
        } catch (error) {
            console.error('Error loading album:', error);
        }
    }

    showAlbumModal(album) {
        // Separate photos and videos
        const photos = album.media_items ? album.media_items.filter(item => item.media_type === 'photo') : [];
        const videos = album.media_items ? album.media_items.filter(item => item.media_type === 'video') : [];

        const modal = document.createElement('div');
        modal.className = 'media-modal active';
        modal.innerHTML = `
            <div class="media-modal-content album-modal">
                <div class="media-modal-header">
                    <div>
                        <h2>${album.name}</h2>
                        ${album.race_name ? `<p><i class="fas fa-flag-checkered"></i> ${album.race_name}</p>` : ''}
                    </div>
                    <button onclick="this.closest('.media-modal').remove()" class="modal-close-btn">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="media-modal-body">
                    <!-- Upload Actions (if logged in) -->
                    ${this.isAuthenticated ? `
                        <div class="upload-actions" id="upload-actions-${album.id}">
                            <button class="upload-btn" onclick="app.showUploadPhotoModal(${album.id})">
                                <i class="fas fa-image"></i> Adicionar Foto
                            </button>
                            <button class="upload-btn" onclick="app.showUploadVideoModal(${album.id})">
                                <i class="fas fa-video"></i> Adicionar Vídeo
                            </button>
                        </div>
                    ` : ''}

                    <!-- Photos Section -->
                    <div class="album-section">
                        <h3><i class="fas fa-images"></i> Fotos (${photos.length})</h3>
                        <div class="media-grid-modal">
                            ${photos.length > 0 ?
                                photos.map(item => `
                                    <div class="media-item-modal" onclick="app.openImage('${item.url}')">
                                        <img src="${item.url}" alt="${item.title || 'Foto'}" loading="lazy">
                                        ${item.title ? `<div class="media-item-title">${item.title}</div>` : ''}
                                    </div>
                                `).join('')
                                : '<p class="empty-section">Nenhuma foto ainda</p>'
                            }
                        </div>
                    </div>

                    <!-- Videos Section -->
                    <div class="album-section">
                        <h3><i class="fas fa-video"></i> Vídeos (${videos.length})</h3>
                        <div class="media-grid-modal">
                            ${videos.length > 0 ?
                                videos.map(item => {
                                    const youtubeId = this.extractYouTubeId(item.url);
                                    return `
                                        <div class="media-item-modal" onclick="app.openVideo('${item.url}')">
                                            <img src="https://img.youtube.com/vi/${youtubeId}/mqdefault.jpg" alt="${item.title || 'Video'}">
                                            <div class="video-play-overlay"><i class="fas fa-play-circle"></i></div>
                                            ${item.title ? `<div class="media-item-title">${item.title}</div>` : ''}
                                        </div>
                                    `;
                                }).join('')
                                : '<p class="empty-section">Nenhum vídeo ainda</p>'
                            }
                        </div>
                    </div>
                </div>
                ${album.google_photos_link ? `
                    <div class="media-modal-footer">
                        <a href="${album.google_photos_link}" target="_blank" class="nav-btn">
                            <i class="fas fa-external-link-alt"></i> Ver no Google Photos
                        </a>
                    </div>
                ` : ''}
            </div>
        `;
        document.body.appendChild(modal);
    }

    openVideo(url) {
        const youtubeId = this.extractYouTubeId(url);
        const embedUrl = youtubeId ?
            `https://www.youtube.com/embed/${youtubeId}?autoplay=1` :
            url;

        const modal = document.createElement('div');
        modal.className = 'media-modal active';
        modal.innerHTML = `
            <div class="media-modal-content video-modal">
                <button onclick="this.closest('.media-modal').remove()" class="modal-close-btn">
                    <i class="fas fa-times"></i>
                </button>
                <div class="video-container">
                    <iframe src="${embedUrl}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }

    openImage(url) {
        const modal = document.createElement('div');
        modal.className = 'media-modal active';
        modal.innerHTML = `
            <div class="media-modal-content image-modal">
                <button onclick="this.closest('.media-modal').remove()" class="modal-close-btn">
                    <i class="fas fa-times"></i>
                </button>
                <img src="${url}" alt="Foto" onclick="event.stopPropagation()">
            </div>
        `;
        modal.onclick = () => modal.remove();
        document.body.appendChild(modal);
    }

    showEmptyMediaState() {
        const photosGrid = document.getElementById('photos-grid');
        const videosGrid = document.getElementById('videos-grid');

        photosGrid.innerHTML = `
            <div class="empty-state-card">
                <i class="fas fa-images"></i>
                <h3>Nenhum álbum ainda</h3>
                <p>Os álbuns de fotos das corridas aparecerão aqui</p>
                ${app.isAdmin ? '<p><small>Use o painel admin para adicionar álbuns</small></p>' : ''}
            </div>
        `;

        videosGrid.innerHTML = `
            <div class="empty-state-card">
                <i class="fas fa-video"></i>
                <h3>Nenhum vídeo ainda</h3>
                <p>Os vídeos das corridas aparecerão aqui</p>
                ${app.isAdmin ? '<p><small>Use o painel admin para adicionar vídeos</small></p>' : ''}
            </div>
        `;
    }

    showUploadPhotoModal(albumId) {
        const modal = document.createElement('div');
        modal.className = 'media-modal active';
        modal.innerHTML = `
            <div class="media-modal-content upload-modal">
                <div class="media-modal-header">
                    <h2><i class="fas fa-image"></i> Adicionar Fotos</h2>
                    <button onclick="this.closest('.media-modal').remove()" class="modal-close-btn">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="media-modal-body">
                    <form id="photo-upload-form" enctype="multipart/form-data">
                        <div class="form-group">
                            <label for="photo-file">Selecione uma ou mais fotos</label>
                            <input type="file" id="photo-file" accept="image/jpeg,image/png,image/gif,image/webp" multiple required>
                            <small>Formatos: JPG, PNG, GIF, WEBP | Tamanho máx por foto: 10MB</small>
                        </div>
                        <div id="file-preview" class="file-preview"></div>
                        <div class="form-group">
                            <label for="photo-title">Título geral (opcional)</label>
                            <input type="text" id="photo-title" placeholder="Ex: Corrida do dia 15/01">
                            <small>Este título será aplicado a todas as fotos</small>
                        </div>
                        <div class="upload-progress" id="photo-upload-progress" style="display: none;">
                            <div class="progress-bar"><div class="progress-fill" id="photo-progress-fill"></div></div>
                            <p id="photo-progress-text">Enviando...</p>
                        </div>
                        <button type="submit" class="upload-submit-btn" id="upload-submit-btn">
                            <i class="fas fa-upload"></i> Enviar Fotos
                        </button>
                    </form>
                </div>
            </div>
        `;
        document.body.appendChild(modal);

        // Show file preview when files are selected
        document.getElementById('photo-file').addEventListener('change', (e) => {
            this.showFilePreview(e.target.files);
        });

        document.getElementById('photo-upload-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.uploadPhotos(albumId, modal);
        });
    }

    showFilePreview(files) {
        const preview = document.getElementById('file-preview');
        preview.innerHTML = '';

        if (files.length === 0) return;

        preview.innerHTML = `<h4>Fotos selecionadas: ${files.length}</h4>`;
        const grid = document.createElement('div');
        grid.className = 'preview-grid';

        Array.from(files).forEach((file, index) => {
            const reader = new FileReader();
            reader.onload = (e) => {
                const item = document.createElement('div');
                item.className = 'preview-item';
                item.innerHTML = `
                    <img src="${e.target.result}" alt="${file.name}">
                    <small>${file.name}</small>
                `;
                grid.appendChild(item);
            };
            reader.readAsDataURL(file);
        });

        preview.appendChild(grid);
    }

    showUploadVideoModal(albumId) {
        const modal = document.createElement('div');
        modal.className = 'media-modal active';
        modal.innerHTML = `
            <div class="media-modal-content upload-modal">
                <div class="media-modal-header">
                    <h2><i class="fas fa-video"></i> Adicionar Vídeo</h2>
                    <button onclick="this.closest('.media-modal').remove()" class="modal-close-btn">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="media-modal-body">
                    <form id="video-upload-form">
                        <div class="form-group">
                            <label for="video-url">URL do YouTube</label>
                            <input type="url" id="video-url" placeholder="https://www.youtube.com/watch?v=..." required>
                            <small>Cole o link do vídeo no YouTube</small>
                        </div>
                        <div class="form-group">
                            <label for="video-title">Título (opcional)</label>
                            <input type="text" id="video-title" placeholder="Ex: Highlights da corrida">
                        </div>
                        <div class="form-group">
                            <label for="video-description">Descrição (opcional)</label>
                            <textarea id="video-description" rows="3" placeholder="Adicione uma descrição..."></textarea>
                        </div>
                        <button type="submit" class="upload-submit-btn">
                            <i class="fas fa-plus"></i> Adicionar Vídeo
                        </button>
                    </form>
                </div>
            </div>
        `;
        document.body.appendChild(modal);

        document.getElementById('video-upload-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.uploadVideo(albumId, modal);
        });
    }

    async uploadPhotos(albumId, modal) {
        const fileInput = document.getElementById('photo-file');
        const title = document.getElementById('photo-title').value;

        if (!fileInput.files.length) {
            alert('Por favor, selecione pelo menos uma foto');
            return;
        }

        const files = Array.from(fileInput.files);
        const progressDiv = document.getElementById('photo-upload-progress');
        const progressFill = document.getElementById('photo-progress-fill');
        const progressText = document.getElementById('photo-progress-text');
        const submitBtn = document.getElementById('upload-submit-btn');

        progressDiv.style.display = 'block';
        submitBtn.disabled = true;

        let successCount = 0;
        let errorCount = 0;

        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            const progress = ((i + 1) / files.length) * 100;

            progressFill.style.width = `${progress}%`;
            progressText.textContent = `Enviando ${i + 1} de ${files.length}...`;

            const formData = new FormData();
            formData.append('file', file);
            formData.append('title', title || file.name);
            formData.append('description', '');

            try {
                const response = await fetch(`/upload/photo/${albumId}`, {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();

                if (result.status === 'success') {
                    successCount++;
                } else {
                    errorCount++;
                    console.error('Upload failed for', file.name, result.message);
                }
            } catch (error) {
                errorCount++;
                console.error('Upload error for', file.name, error);
            }
        }

        progressFill.style.width = '100%';
        progressText.textContent = `Concluído! ${successCount} foto(s) enviada(s)${errorCount > 0 ? `, ${errorCount} erro(s)` : ''}`;

        setTimeout(() => {
            modal.remove();
            // Reload album
            this.openAlbum(albumId);
        }, 1500);
    }

    async uploadVideo(albumId, modal) {
        const url = document.getElementById('video-url').value;
        const title = document.getElementById('video-title').value;
        const description = document.getElementById('video-description').value;

        try {
            const response = await fetch(`/upload/video/${albumId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ url, title, description })
            });

            const result = await response.json();

            if (result.status === 'success') {
                modal.remove();
                // Reload album
                this.openAlbum(albumId);
            } else {
                alert('Erro: ' + result.message);
            }
        } catch (error) {
            console.error('Upload error:', error);
            alert('Erro ao adicionar vídeo');
        }
    }

    // Old localStorage functions - kept for backwards compatibility
    loadDefaultPhotos() { return; }
    displayRaceAlbums() { return; }
    addRaceAlbum() { return; }
    removeRaceAlbum() { return; }
    async loadPhotos() { return; }
    async loadLocations() {
        try {
            const response = await fetch(`${this.apiBase}/locations`);
            const locations = await response.json();
            this.displayLocations(locations);
        } catch (error) {
            console.error('Error loading locations:', error);
            document.getElementById('locations-grid').innerHTML = '<p>Erro ao carregar locais</p>';
        }
    }

    displayLocations(locations) {
        const container = document.getElementById('locations-grid');
        if (!locations || locations.length === 0) {
            container.innerHTML = '<p>Nenhum local encontrado</p>';
            return;
        }

        const locationsHTML = locations.map(location => this.createLocationCard(location)).join('');
        container.innerHTML = locationsHTML;
    }

    createLocationCard(location) {
        const formatPrice = (price) => {
            if (parseFloat(price) === 0 || location.rental_duration === 'Consultar') {
                return 'Consultar';
            }
            return new Intl.NumberFormat('pt-BR', {
                style: 'currency',
                currency: 'BRL'
            }).format(parseFloat(price));
        };

        const thumbnailSrc = location.thumbnail_url || '/static/images/default-track.jpg';

        return `
            <div class="location-card">
                <div class="location-header">
                    <img src="${thumbnailSrc}" alt="${location.name}" class="location-thumbnail" 
                         onerror="this.src='/static/images/default-track.jpg'">
                    <div class="location-name-overlay">
                        <h3>${location.name}</h3>
                    </div>
                </div>
                <div class="location-body">
                    <div class="location-info">
                        <div class="info-row">
                            <i class="fas fa-clock"></i>
                            Duração: ${location.rental_duration}
                            <span class="price-tag">${formatPrice(location.price_per_person)}</span>
                        </div>
                        <div class="info-row">
                            <i class="fas fa-users"></i>
                            ${location.min_participants} - ${location.max_participants} participantes
                        </div>
                        <div class="info-row">
                            <i class="fas fa-ruler-vertical"></i>
                            Altura mínima: ${location.min_height}
                        </div>
                        <div class="info-row">
                            <i class="fas fa-map-marker-alt"></i>
                            ${location.address}, ${location.neighborhood}, ${location.city}
                        </div>
                        ${location.exclusive_info ? `<div class="exclusive-badge">${location.exclusive_info}</div>` : ''}
                    </div>
                    
                    <div class="schedule-section">
                        <h4 style="color: #0088FF; margin-bottom: 0.8rem;">
                            <i class="fas fa-calendar-alt"></i> Horários de Funcionamento
                        </h4>
                        <div class="schedule-item">
                            <span class="schedule-label">Segunda à Sexta:</span>
                            <span>${location.schedule_weekday}</span>
                        </div>
                        <div class="schedule-item">
                            <span class="schedule-label">Sábados:</span>
                            <span>${location.schedule_saturday}</span>
                        </div>
                        <div class="schedule-item">
                            <span class="schedule-label">Dom/Feriados:</span>
                            <span>${location.schedule_sunday}</span>
                        </div>
                    </div>
                </div>
                <div class="location-footer">
                    <div class="social-links">
                        ${location.instagram ? `<a href="https://instagram.com/${location.instagram.replace('@', '')}" target="_blank" class="social-link" title="Instagram"><i class="fab fa-instagram"></i></a>` : ''}
                        ${location.website ? `<a href="${location.website}" target="_blank" class="social-link" title="Website"><i class="fas fa-globe"></i></a>` : ''}
                    </div>
                    <div style="font-size: 0.9rem; color: #1A1A3A;">
                        ${location.description}
                    </div>
                </div>
            </div>
        `;
    }
}

// Global functions for onclick handlers
function showSection(sectionName) {
    app.showSection(sectionName);

    // Update sidebar nav active states
    document.querySelectorAll('.sidebar-nav-item').forEach(item => {
        item.classList.remove('active');
    });
    const activeLink = document.querySelector(`.sidebar-nav-item[href="#${sectionName}"]`);
    if (activeLink) {
        activeLink.classList.add('active');
    }
}

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');

    if (sidebar && overlay) {
        sidebar.classList.toggle('open');
        overlay.classList.toggle('active');
    }
}

function showMediaTab(tabName) {
    // Hide all media tabs
    document.querySelectorAll('.media-tab-content').forEach(tab => {
        tab.classList.remove('active');
    });

    // Remove active class from all media tab buttons
    document.querySelectorAll('.media-tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    // Show selected tab
    document.getElementById(`${tabName}-tab`).classList.add('active');

    // Add active class to corresponding button
    event.target.classList.add('active');
}

// Initialize the application
const app = new KartRaceTracker();