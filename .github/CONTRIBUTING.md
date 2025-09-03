# Contribuindo para Nerds do Kart 🏁

## Como contribuir

### 1. Fork e Clone
```bash
git clone https://github.com/GiordaniAndre/nerds-do-kart.git
cd nerds-do-kart
```

### 2. Configurar ambiente local
```bash
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate no Windows
pip install -r requirements.txt
```

### 3. Executar localmente
```bash
python app.py
# Acesse http://localhost:5003
```

### 4. Fazer mudanças
- Crie uma branch: `git checkout -b feature/nova-funcionalidade`
- Faça suas alterações
- Teste localmente
- Commit: `git commit -m "Adiciona nova funcionalidade"`

### 5. Abrir Pull Request
- Push da branch: `git push origin feature/nova-funcionalidade`
- Abra PR no GitHub usando o template

## Estrutura do projeto
```
├── app.py              # Flask app principal
├── data/               # Dados Excel
├── static/
│   ├── css/           # Estilos
│   └── js/            # JavaScript
├── templates/         # HTML templates
└── requirements.txt   # Dependências
```

## Guidelines
- **Português**: Interface em português brasileiro
- **Responsivo**: Teste em mobile e desktop
- **Performance**: Mantenha carregamento rápido
- **Dados**: Não quebre a leitura do Excel
- **Estilo**: Use as cores do tema (#FF0066, #0088FF, #00FF88, #1A1A3A)

## Deploy automático
- Mudanças na `master` fazem deploy automático
- Site: https://nerdsdokart.com.br
- Aguarde 1-2 minutos para ver mudanças

## Dúvidas?
- Abra uma issue no GitHub
- Ou entre em contato com @GiordaniAndre

Acelera! 🏎️