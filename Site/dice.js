const fs = require('fs');
const path = require('path');

const imagesToLoad = [
    'd1.png',
    'd2.png',
    'd3.png',
    'd4.png',
    'd5.png',
    'd6.png'
];

function getDiceImages() {
    const imagesDir = path.join(__dirname, 'public', 'assets', 'images');
    const images = {};

    imagesToLoad.forEach((imageName, index) => {
        const imagePath = path.join(imagesDir, imageName);

        if (fs.existsSync(imagePath)) {
            const imageUrl = `/assets/images/${imageName}`;
            images[index] = imageUrl;
        } else {
            console.error(`Image not found: ${imagePath}`);
        }
    });

    return images;
}

module.exports = { getDiceImages };
