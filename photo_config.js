// CONFIGURAÇÃO DAS FOTOS - Nerds do Kart
// Substitua os IDs abaixo pelos IDs das suas fotos do Google Drive

const VELOPARK_PHOTOS = {
    // Para obter o ID: Abra a foto no Google Drive → Compartilhar → Copie o link
    // Do link https://drive.google.com/file/d/1ABC123DEF456/view?usp=sharing
    // Use apenas: 1ABC123DEF456
    
    largada: "1558618666-fcd25c85cd64", // Substitua pelo ID real da foto de largada
    corrida: "1583900985737-6d0495555783", // Substitua pelo ID real da foto durante a corrida
    podio: "1593766827228-8737b4534aa6", // Substitua pelo ID real da foto do pódio
    equipe: "1571019613454-1cb2f99b2d8b" // Substitua pelo ID real da foto da equipe
};

// EXEMPLO DE COMO SUBSTITUIR:
// 1. Abra sua foto no Google Drive
// 2. Clique em "Compartilhar" → "Qualquer pessoa com o link"
// 3. Copie o link: https://drive.google.com/file/d/1W3GVQ88dC5JCW6WL4UxfC1ecZGal2kpf/view
// 4. Extraia o ID: 1W3GVQ88dC5JCW6WL4UxfC1ecZGal2kpf
// 5. Substitua acima: largada: "1W3GVQ88dC5JCW6WL4UxfC1ecZGal2kpf"

// Para usar Imgur ao invés do Google Drive:
const IMGUR_PHOTOS = {
    largada: "https://i.imgur.com/EXEMPLO1.jpg", // Cole o link direto do Imgur
    corrida: "https://i.imgur.com/EXEMPLO2.jpg",
    podio: "https://i.imgur.com/EXEMPLO3.jpg",
    equipe: "https://i.imgur.com/EXEMPLO4.jpg"
};

// Escolha qual usar: 'drive' ou 'imgur'
const PHOTO_SOURCE = 'imgur'; // Mude para 'imgur' se preferir usar Imgur