class KartRaceTracker {
    constructor() {
        this.apiBase = '/api';
        this.init();
    }

    async init() {
        await this.loadDashboard();
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

        if (stats) {
            document.getElementById('total-racers').textContent = stats.total_racers;
            document.getElementById('total-races').textContent = stats.total_races;
            document.getElementById('fastest-lap').textContent = 
                stats.fastest_lap_time ? `${stats.fastest_lap_time}s` : 'N/A';
            document.getElementById('fastest-racer').textContent = 
                stats.fastest_lap_racer || 'N/A';
        }

        if (recentRaces) {
            this.renderRecentRaces(recentRaces);
        }
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
            this.renderRacers(racers);
        }
    }

    renderRacers(racers) {
        const container = document.getElementById('racers-grid');
        container.innerHTML = racers.map(racer => `
            <div class="racer-card">
                <h3><i class="fas fa-user"></i> ${racer.name}</h3>
                <div class="racer-stats">
                    <div><strong>Idade:</strong> ${racer.age}</div>
                    <div><strong>Experiência:</strong> ${racer.experience_years} anos</div>
                    <div><strong>Total de Corridas:</strong> ${racer.total_races}</div>
                    <div><strong>Vitórias:</strong> ${racer.wins}</div>
                    <div><strong>Pódios:</strong> ${racer.podium_finishes}</div>
                    <div><strong>Taxa de Vitória:</strong> ${((racer.wins / racer.total_races) * 100).toFixed(1)}%</div>
                </div>
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
        container.innerHTML = races.map(race => `
            <div class="race-item">
                <div>
                    <h4>${race.race_name}</h4>
                    <p><i class="fas fa-map-marker-alt"></i> ${race.track_name}</p>
                </div>
                <div>
                    <p><strong>Data:</strong> ${this.formatDate(race.date)}</p>
                    <p><strong>Clima:</strong> ${this.translateWeather(race.weather)}</p>
                </div>
                <div>
                    <p><strong>Voltas:</strong> ${race.total_laps}</p>
                </div>
                <div>
                    <button class="nav-btn" onclick="app.showRaceDetails(${race.race_id})">
                        <i class="fas fa-eye"></i> Detalhes
                    </button>
                </div>
            </div>
        `).join('');
    }

    async showRaceDetails(raceId) {
        const race = await this.fetchAPI(`/races/${raceId}`);
        if (race) {
            alert(`Corrida: ${race.race_name}\nVencedor: ${race.results[0]?.name || 'Desconhecido'}\nResultados carregados no console`);
            console.log('Detalhes da Corrida:', race);
        }
    }

    async loadLeaderboard() {
        const leaderboard = await this.fetchAPI('/leaderboard');
        if (leaderboard) {
            this.renderTable('leaderboard-table', leaderboard, [
                { key: 'name', label: 'Piloto' },
                { key: 'wins', label: 'Vitórias' },
                { key: 'total_races', label: 'Total de Corridas' },
                { key: 'podium_finishes', label: 'Pódios' },
                { key: 'experience_years', label: 'Experiência (anos)' }
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
        // Load saved Drive IDs from localStorage if available
        const photosId = localStorage.getItem('photos-drive-id');
        const videosId = localStorage.getItem('videos-drive-id');
        
        if (photosId) {
            document.getElementById('photos-drive-id').value = photosId;
        }
        if (videosId) {
            document.getElementById('videos-drive-id').value = videosId;
        }

        // Load default photos immediately for demo
        this.loadDefaultPhotos();
    }

    loadDefaultPhotos() {
        const container = document.getElementById('photos-grid');
        
        // Load saved race albums from localStorage
        const savedAlbums = JSON.parse(localStorage.getItem('race-albums') || '[]');
        
        if (savedAlbums.length > 0) {
            this.displayRaceAlbums(savedAlbums, container);
        } else {
            // Show default content with instructions
            container.innerHTML = `
                <div class="media-upload-info">
                    <h3>📸 Álbuns das Corridas - Nerds do Kart</h3>
                    <p><i class="fas fa-info-circle"></i> Adicione álbuns do Google Photos das suas corridas</p>
                </div>

                <div class="add-album-section">
                    <h3>➕ Adicionar Álbum de Corrida</h3>
                    <div class="album-form">
                        <input type="text" id="race-name-input" placeholder="Nome da corrida (ex: Velopark - 30/08/2025)" />
                        <input type="text" id="race-album-link" placeholder="Link do Google Photos (ex: https://photos.app.goo.gl/...)" />
                        <input type="text" id="cover-photo-link" placeholder="Link da foto de capa (opcional - deixe vazio para usar ícone)" />
                        <button onclick="app.addRaceAlbum()" class="nav-btn">
                            <i class="fas fa-plus"></i> Adicionar Álbum
                        </button>
                    </div>
                    <div class="cover-photo-help">
                        <small><i class="fas fa-lightbulb"></i> 
                        <strong>Dica:</strong> Para foto de capa, abra uma foto do álbum no Google Photos → 
                        Compartilhar → "Qualquer pessoa com o link" → 
                        Cole o ID: <code>https://drive.google.com/uc?id=ID_DA_FOTO</code>
                        </small>
                    </div>
                </div>
                
                <div class="media-item demo-album">
                    <img src="/velopark-cover.jpg" 
                         alt="Velopark Photos" 
                         onclick="window.open('https://photos.app.goo.gl/A5rxNUdX5L49BUDM8', '_blank')" 
                         style="cursor: pointer;" />
                    <div class="media-item-info">
                        <h4>Velopark</h4>
                        <p>Fotos da corrida</p>
                        <small>📷 Clique para ver álbum completo</small>
                    </div>
                </div>

                <div class="google-photos-guide">
                    <h3>📋 Como usar com Google Photos:</h3>
                    <ol>
                        <li><strong>Após cada corrida:</strong> Peça para alguém criar um álbum compartilhado</li>
                        <li><strong>Todos compartilham fotos:</strong> Cada piloto adiciona suas fotos ao álbum</li>
                        <li><strong>Pegue o link:</strong> No Google Photos → Compartilhar → Copiar link</li>
                        <li><strong>Adicione aqui:</strong> Use o formulário acima para adicionar à galeria</li>
                        <li><strong>Resultado:</strong> Álbum aparece na galeria para todos verem</li>
                    </ol>
                    
                    <div class="workflow-example">
                        <h4>💡 Fluxo Recomendado:</h4>
                        <p><strong>1. Corrida no Velopark →</strong> Alguém cria álbum "Velopark 30/08"</p>
                        <p><strong>2. Todos enviam fotos →</strong> WhatsApp: "Galera, adicionem no álbum!"</p>
                        <p><strong>3. Link no site →</strong> Administrador adiciona o link aqui</p>
                        <p><strong>4. Galeria atualizada →</strong> Todos veem as fotos organizadas</p>
                    </div>
                </div>
            `;
        }
    }

    displayRaceAlbums(albums, container) {
        const albumCards = albums.map(album => {
            let thumbnailContent;
            
            if (album.coverPhoto) {
                // Use the cover photo if provided
                thumbnailContent = `<img src="${album.coverPhoto}" alt="${album.name}" style="width: 100%; height: 100%; object-fit: cover; border-radius: 10px 10px 0 0;" />`;
            } else {
                // Use default icon layout
                thumbnailContent = `
                    <i class="fas fa-images"></i>
                    <h4>${album.name}</h4>
                    <p>Clique para ver fotos</p>
                `;
            }

            return `
                <div class="media-item race-album">
                    <div class="album-thumbnail" onclick="window.open('${album.link}', '_blank')" style="cursor: pointer;">
                        ${thumbnailContent}
                    </div>
                    <div class="media-item-info">
                        <h4>${album.name}</h4>
                        <p><i class="fas fa-calendar"></i> ${album.date || 'Data não informada'}</p>
                        <p><i class="fas fa-external-link-alt"></i> <a href="${album.link}" target="_blank">Abrir álbum</a></p>
                        <button onclick="app.removeRaceAlbum('${album.id}')" class="remove-btn">
                            <i class="fas fa-trash"></i> Remover
                        </button>
                    </div>
                </div>
            `;
        }).join('');

        container.innerHTML = `
            <div class="media-upload-info">
                <h3>📸 Álbuns das Corridas - Nerds do Kart</h3>
                <p><i class="fas fa-camera"></i> ${albums.length} álbum${albums.length !== 1 ? 's' : ''} adicionado${albums.length !== 1 ? 's' : ''}</p>
            </div>

            <div class="add-album-section">
                <h3>➕ Adicionar Novo Álbum</h3>
                <div class="album-form">
                    <input type="text" id="race-name-input" placeholder="Nome da corrida (ex: Interlagos - 15/09/2025)" />
                    <input type="text" id="race-album-link" placeholder="Link do Google Photos" />
                    <input type="text" id="cover-photo-link" placeholder="Link da foto de capa (opcional)" />
                    <button onclick="app.addRaceAlbum()" class="nav-btn">
                        <i class="fas fa-plus"></i> Adicionar Álbum
                    </button>
                </div>
                <div class="cover-photo-help">
                    <small><i class="fas fa-lightbulb"></i> 
                    <strong>Dica:</strong> Para foto de capa do álbum, copie o ID de uma foto específica
                    </small>
                </div>
            </div>

            ${albumCards}
        `;
    }

    addRaceAlbum() {
        const nameInput = document.getElementById('race-name-input');
        const linkInput = document.getElementById('race-album-link');
        const coverInput = document.getElementById('cover-photo-link');
        
        const name = nameInput.value.trim();
        const link = linkInput.value.trim();
        const coverPhoto = coverInput.value.trim();
        
        if (!name || !link) {
            alert('Por favor, preencha o nome da corrida e o link do álbum');
            return;
        }

        if (!link.includes('photos.app.goo.gl') && !link.includes('photos.google.com')) {
            alert('Por favor, use um link válido do Google Photos');
            return;
        }

        // Process cover photo link if provided
        let processedCoverPhoto = '';
        if (coverPhoto) {
            if (coverPhoto.includes('drive.google.com/file/d/')) {
                // Extract ID from Google Drive link and convert to direct link
                const fileId = coverPhoto.split('/file/d/')[1].split('/')[0];
                processedCoverPhoto = `https://drive.google.com/uc?id=${fileId}`;
            } else if (coverPhoto.includes('drive.google.com/uc?id=') || coverPhoto.includes('imgur.com') || coverPhoto.startsWith('http')) {
                // Already a direct link
                processedCoverPhoto = coverPhoto;
            } else {
                // Assume it's just an ID
                processedCoverPhoto = `https://drive.google.com/uc?id=${coverPhoto}`;
            }
        }

        // Get existing albums
        const savedAlbums = JSON.parse(localStorage.getItem('race-albums') || '[]');
        
        // Add new album
        const newAlbum = {
            id: Date.now().toString(),
            name: name,
            link: link,
            coverPhoto: processedCoverPhoto,
            date: new Date().toLocaleDateString('pt-BR'),
            addedAt: new Date().toISOString()
        };

        savedAlbums.unshift(newAlbum); // Add to beginning
        localStorage.setItem('race-albums', JSON.stringify(savedAlbums));

        // Clear inputs
        nameInput.value = '';
        linkInput.value = '';
        coverInput.value = '';

        // Refresh display
        this.loadDefaultPhotos();
        
        alert(`Álbum "${name}" adicionado com sucesso!${processedCoverPhoto ? ' Com foto de capa personalizada.' : ''}`);
    }

    removeRaceAlbum(albumId) {
        if (!confirm('Tem certeza que deseja remover este álbum?')) return;

        const savedAlbums = JSON.parse(localStorage.getItem('race-albums') || '[]');
        const filteredAlbums = savedAlbums.filter(album => album.id !== albumId);
        
        localStorage.setItem('race-albums', JSON.stringify(filteredAlbums));
        this.loadDefaultPhotos();
    }

    async loadPhotos() {
        const input = document.getElementById('photos-drive-id').value.trim();
        if (!input) {
            alert('Por favor, insira um link do Google Photos ou Google Drive');
            return;
        }

        // Save the input for future use
        localStorage.setItem('photos-drive-id', input);

        const container = document.getElementById('photos-grid');
        container.innerHTML = '<div class="loading-media"><i class="fas fa-spinner"></i><p>Carregando fotos...</p></div>';

        // Check if it's a Google Photos link
        if (input.includes('photos.app.goo.gl') || input.includes('photos.google.com')) {
            this.loadGooglePhotos(input, container);
        } else {
            this.loadGoogleDrivePhotos(input, container);
        }
    }

    loadGooglePhotos(link, container) {
        // Handle your specific Velopark album - with actual demo photos
        if (link === 'https://photos.app.goo.gl/A5rxNUdX5L49BUDM8') {
            container.innerHTML = `
                <div class="media-upload-info">
                    <h3>📸 Velopark - 2025-08-30</h3>
                    <p><i class="fas fa-calendar"></i> Corrida no Velopark</p>
                    <p><i class="fas fa-external-link-alt"></i> <a href="${link}" target="_blank">Ver álbum completo no Google Photos</a></p>
                    <p><i class="fas fa-info-circle"></i> <strong>Para mostrar fotos reais:</strong> Adicione os links diretos das imagens abaixo</p>
                </div>
                
                <div class="media-item">
                    <img src="https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=300&fit=crop&auto=format" 
                         alt="Largada Velopark" 
                         onclick="app.openGooglePhotos('${link}')" 
                         style="cursor: pointer;" />
                    <div class="media-item-info">
                        <h4>Largada - Velopark</h4>
                        <p>Momentos antes da corrida começar</p>
                        <small>📷 Clique para ver no Google Photos</small>
                    </div>
                </div>

                <div class="media-item">
                    <img src="https://images.unsplash.com/photo-1583900985737-6d0495555783?w=400&h=300&fit=crop&auto=format" 
                         alt="Corrida em andamento" 
                         onclick="app.openGooglePhotos('${link}')" 
                         style="cursor: pointer;" />
                    <div class="media-item-info">
                        <h4>Ação na Pista</h4>
                        <p>Disputas acirradas no Velopark</p>
                        <small>📷 Clique para ver no Google Photos</small>
                    </div>
                </div>

                <div class="media-item">
                    <img src="https://images.unsplash.com/photo-1593766827228-8737b4534aa6?w=400&h=300&fit=crop&auto=format" 
                         alt="Pódio da corrida" 
                         onclick="app.openGooglePhotos('${link}')" 
                         style="cursor: pointer;" />
                    <div class="media-item-info">
                        <h4>Celebração</h4>
                        <p>Momento da vitória!</p>
                        <small>📷 Clique para ver no Google Photos</small>
                    </div>
                </div>

                <div class="media-item">
                    <img src="https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400&h=300&fit=crop&auto=format" 
                         alt="Equipe dos Nerds" 
                         onclick="app.openGooglePhotos('${link}')" 
                         style="cursor: pointer;" />
                    <div class="media-item-info">
                        <h4>Equipe Completa</h4>
                        <p>Todos os pilotos reunidos</p>
                        <small>📷 Clique para ver no Google Photos</small>
                    </div>
                </div>

                <div class="photo-upload-instructions">
                    <h3>🔧 Como adicionar suas fotos reais:</h3>
                    <p><strong>Método 1 - Google Drive (Recomendado):</strong></p>
                    <ol>
                        <li>Faça upload das fotos para uma pasta no Google Drive</li>
                        <li>Para cada foto: botão direito → "Obter link" → "Qualquer pessoa com o link"</li>
                        <li>Copie o ID da foto (parte entre /file/d/ e /view)</li>
                        <li>Use: <code>https://drive.google.com/uc?id=SEU_ID_AQUI</code></li>
                        <li>Substitua os links acima pelos seus links reais</li>
                    </ol>
                    
                    <p><strong>Método 2 - Upload direto:</strong></p>
                    <ol>
                        <li>Faça upload das fotos para a pasta <code>static/images/</code> do projeto</li>
                        <li>Use: <code>{{ url_for('static', filename='images/foto1.jpg') }}</code></li>
                    </ol>
                    
                    <p><strong>Método 3 - Imgur (Gratuito):</strong></p>
                    <ol>
                        <li>Faça upload das fotos no <a href="https://imgur.com" target="_blank">imgur.com</a></li>
                        <li>Copie o link direto da imagem</li>
                        <li>Substitua os links acima</li>
                    </ol>
                </div>
            `;
        } else {
            // Generic Google Photos album
            container.innerHTML = `
                <div class="media-upload-info">
                    <h3>📸 Álbum do Google Photos</h3>
                    <p><i class="fas fa-external-link-alt"></i> <a href="${link}" target="_blank">Ver álbum completo</a></p>
                </div>
                <div class="media-item">
                    <div class="photo-placeholder" onclick="app.openGooglePhotos('${link}')">
                        <i class="fas fa-images"></i>
                        <h4>Álbum de Fotos</h4>
                        <p>Clique para abrir no Google Photos</p>
                    </div>
                    <div class="media-item-info">
                        <h4>Fotos da Corrida</h4>
                        <p>Ver todas as fotos</p>
                    </div>
                </div>
            `;
        }
    }

    loadGoogleDrivePhotos(input, container) {
        // Extract folder ID from the Drive link
        let folderId = input;
        if (input.includes('drive.google.com/drive/folders/')) {
            folderId = input.split('/folders/')[1].split('?')[0];
        }

        container.innerHTML = `
            <div class="media-upload-info">
                <h3>📁 Pasta do Google Drive</h3>
                <p><i class="fas fa-folder"></i> ID da Pasta: <code>${folderId}</code></p>
                <p><i class="fas fa-external-link-alt"></i> <a href="https://drive.google.com/drive/folders/${folderId}" target="_blank">Abrir pasta no Google Drive</a></p>
                <br>
                <p><i class="fas fa-exclamation-triangle"></i> <strong>Problema:</strong> Google Drive não permite exibir fotos de pastas diretamente em sites por questões de segurança.</p>
            </div>

            <div class="photo-upload-instructions">
                <h3>🔧 SOLUÇÃO - Como mostrar suas fotos reais:</h3>
                
                <p><strong>Método 1 - Links individuais (Funciona 100%):</strong></p>
                <ol>
                    <li><strong>Abra sua pasta:</strong> <a href="https://drive.google.com/drive/folders/${folderId}" target="_blank">Clique aqui para abrir</a></li>
                    <li><strong>Para cada foto:</strong> Clique na foto → Clique nos 3 pontos (...) → "Compartilhar"</li>
                    <li><strong>Torne pública:</strong> "Qualquer pessoa com o link pode visualizar" → "Copiar link"</li>
                    <li><strong>Extraia o ID:</strong> Do link <code>https://drive.google.com/file/d/<span style="background: yellow;">ID_AQUI</span>/view</code></li>
                    <li><strong>Use este formato:</strong> <code>https://drive.google.com/uc?id=ID_AQUI</code></li>
                </ol>

                <p><strong>Método 2 - Imgur (Mais Fácil):</strong></p>
                <ol>
                    <li>Baixe suas fotos do Google Drive</li>
                    <li>Faça upload em <a href="https://imgur.com" target="_blank">imgur.com</a> (gratuito, sem cadastro)</li>
                    <li>Copie os links diretos das imagens</li>
                    <li>Use os links do Imgur no código</li>
                </ol>

                <p><strong>Exemplo prático com suas fotos:</strong></p>
                <div style="background: #f0f0f0; padding: 15px; border-radius: 5px; margin: 10px 0;">
                    <p>Se você tem uma foto com link:</p>
                    <code>https://drive.google.com/file/d/1ABC123DEF456/view</code>
                    <p>Use:</p>
                    <code>https://drive.google.com/uc?id=1ABC123DEF456</code>
                </div>
            </div>

            <div class="demo-replacement">
                <h3>📝 Substitua as fotos demo:</h3>
                <p>Edite o arquivo <code>static/js/app.js</code> na função <code>loadDefaultPhotos()</code> e substitua os links do Unsplash pelos seus links do Google Drive ou Imgur.</p>
                
                <div class="media-item">
                    <div style="background: linear-gradient(135deg, #0088FF, #FF0066); color: white; height: 200px; display: flex; align-items: center; justify-content: center; border-radius: 10px;">
                        <div style="text-align: center;">
                            <i class="fas fa-image" style="font-size: 3rem; margin-bottom: 1rem;"></i>
                            <h4>Suas Fotos Aqui</h4>
                            <p>Siga as instruções acima</p>
                        </div>
                    </div>
                    <div class="media-item-info">
                        <h4>Exemplo de Substituição</h4>
                        <p>Cole os links das suas fotos reais</p>
                    </div>
                </div>
            </div>
        `;
    }

    openGooglePhotos(link) {
        window.open(link, '_blank');
    }

    async loadVideos() {
        const driveId = document.getElementById('videos-drive-id').value.trim();
        if (!driveId) {
            alert('Por favor, insira o ID da pasta do Google Drive');
            return;
        }

        localStorage.setItem('videos-drive-id', driveId);

        const container = document.getElementById('videos-grid');
        container.innerHTML = '<div class="loading-media"><i class="fas fa-spinner"></i><p>Carregando vídeos...</p></div>';

        container.innerHTML = `
            <div class="media-upload-info">
                <h3>Configure manualmente seus vídeos:</h3>
                <p><strong>ID da pasta:</strong> ${driveId}</p>
                <p><strong>Link da pasta:</strong> <a href="https://drive.google.com/drive/folders/${driveId}" target="_blank">Abrir pasta no Google Drive</a></p>
                <br>
                <p><strong>Para incorporar vídeos:</strong></p>
                <ol>
                    <li>Abra o vídeo no Google Drive</li>
                    <li>Clique nos 3 pontos → "Compartilhar" → "Obter link"</li>
                    <li>Altere para "Qualquer pessoa com o link"</li>
                    <li>Para vídeos, use o player incorporado do Google Drive</li>
                </ol>
            </div>
            <div class="media-item">
                <div style="position: relative; width: 100%; height: 200px; background: #f0f0f0; border-radius: 10px; display: flex; align-items: center; justify-content: center;">
                    <p style="text-align: center; color: #666;">
                        <i class="fas fa-video" style="font-size: 2rem; margin-bottom: 0.5rem; display: block;"></i>
                        Vídeo de exemplo<br>
                        <small>Configure com seus próprios IDs</small>
                    </p>
                </div>
                <div class="media-item-info">
                    <h4>Melhores momentos</h4>
                    <p>Grandes disputas na pista!</p>
                </div>
            </div>
        `;
    }

    openMediaOverlay(src) {
        const overlay = document.createElement('div');
        overlay.className = 'media-overlay active';
        overlay.innerHTML = `
            <span class="media-overlay-close" onclick="this.parentElement.remove()">&times;</span>
            <div class="media-overlay-content">
                <img src="${src}" alt="Foto ampliada" />
            </div>
        `;
        document.body.appendChild(overlay);
    }
}

// Global functions for onclick handlers
function showSection(sectionName) {
    app.showSection(sectionName);
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