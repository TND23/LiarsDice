const socket = io();

const aiDiceContainer = document.getElementById('ai-dice');
const humanDiceContainer = document.getElementById('human-dice');
const historyContainer = document.getElementById('history');
const quantityInput = document.getElementById('quantity');
const faceValueInput = document.getElementById('face-value');
const bidButton = document.getElementById('bid-button');
const liarButton = document.getElementById('liar-button');
//const playAgainButton = document.getElementById('play-again-button');

let counts = {
    human: 5,
    ai: 5
};

let gameState = {
    currentPlayer: 'human',
    lastBid: null,
    history: [],
    dice: {
        human: [],
        ai: []
    }
};

let diceImages = {};

socket.on('connect', () => {
    console.log('Connected to server');
});
socket.on('gameOver', () => {
    endGame();
});
socket.on('gameState', (state) => {
    gameState = state;
    updateUI();
    // If it's AI's turn, wait for its move
    if (gameState.currentPlayer === 'ai') {
        console.log('Waiting for AI move...');
    }
});

socket.on('rollDice', rollDice);

socket.on('diceImages', (images) => {
    diceImages = images;
    updateUI();
});

socket.on('removeDie', (player) => {
    if (player == 'human') {
        gameState.dice.human.pop();
    } else {
        gameState.dice.ai.pop();
    }
    updateUI();
});

socket.on('hands', (hands) => {
    gameState.dice = hands;
    updateUI();
});

socket.on('error', (message) => {
    alert(message);
});

function rollDice() {
    gameState.dice.human = [];

    try {
        for (let i = 0; i < counts.human; i++) {
            gameState.dice.human.push(Math.floor(Math.random() * 6) + 1);
        }
        updateDiceDisplay(humanDiceContainer, gameState.dice.human);
    } catch (error) {
        console.error('Error rolling dice:', error);
    }
}
function endGame() {
    alert('Game over!');
}
function updateUI() {
    updateDiceDisplay(aiDiceContainer, gameState.dice.ai);
    updateDiceDisplay(humanDiceContainer, gameState.dice.human);
    updateHistory();
    updateControls();
}

function check_liar_call(last_bid) {
    return gameState.dice.human.concat(gameState.dice.ai).filter(value => value === last_bid.faceValue).length >= last_bid.quantity;
}


function updateDiceDisplay(container, dice) {
    if (dice.length === 0) {
        return;
    }
    container.innerHTML = '';
    if (container == aiDiceContainer) {
        const aiDice = document.createElement('div');
        aiDice.className = 'aiDisplay';
        if (gameState.dice.ai.length == 1) {
            aiDice.textContent = 'AI has ' + gameState.dice.ai.length + ' die';
        } else {
            aiDice.textContent = 'AI has ' + gameState.dice.ai.length + ' dice';
        }
        container.appendChild(aiDice);
    } else if (container == humanDiceContainer) {
        dice.forEach(value => {
            const die = document.createElement('div');
            die.className = 'dice';
            const imageUrl = diceImages[value - 1];

            if (imageUrl) {
                die.style.backgroundImage = `url(${imageUrl})`;
                die.style.backgroundSize = 'cover';
                die.style.backgroundPosition = 'center';
            } else {
                console.warn(`Dice image not found for value ${value}`);
                die.textContent = value; // Fallback to showing the number
            }
            container.appendChild(die);
        });
    }

}

function updateHistory() {
    historyContainer.innerHTML = '';
    gameState.history.forEach(item => {
        const historyItem = document.createElement('div');
        historyItem.className = `history-item ${item.player}`;

        let moveText = '';
        if (item.move === 'liar') {
            moveText = `${item.player === 'human' ? 'You' : 'AI'} called liar!`;
        } else {
            moveText = `${item.player === 'human' ? 'You' : 'AI'} bid ${item.move.quantity} ${item.move.faceValue}s`;
        }

        historyItem.textContent = moveText;
        historyContainer.appendChild(historyItem);
    });
    historyContainer.scrollTop = historyContainer.scrollHeight;
}

function updateControls() {
    const isHumanTurn = gameState.currentPlayer === 'human';
    const isGameOver = gameState.dice.human.length === 0 || gameState.dice.ai.length === 0;

    bidButton.disabled = !isHumanTurn || isGameOver;
    liarButton.disabled = !isHumanTurn || isGameOver || !gameState.lastBid;
    quantityInput.disabled = !isHumanTurn || isGameOver;
    faceValueInput.disabled = !isHumanTurn || isGameOver;
}

function endGame() {
    alert('Game over!');
}

function getHands() {
    return {
        human: gameState.dice.human,
        ai: gameState.dice.ai
    }
}
function is_legal_bid(quantity, faceValue) {
    if (gameState.lastBid == null) {
        return true;
    }
    if (gameState.lastBid.quantity == quantity) {
        return gameState.lastBid.faceValue < faceValue;
    }
    if (gameState.lastBid.quantity < quantity) {
        return true;
    }
    return false;
}
bidButton.addEventListener('click', () => {
    const quantity = parseInt(quantityInput.value);
    const faceValue = parseInt(faceValueInput.value);

    if (isNaN(quantity) || isNaN(faceValue)) {
        alert('Please enter valid numbers');
        return;
    }

    if (quantity < 1 || quantity > 10) {
        alert('Quantity must be between 1 and 10');
        return;
    }

    if (faceValue < 1 || faceValue > 6) {
        alert('Face value must be between 1 and 6');
        return;
    }

    if (!is_legal_bid(quantity, faceValue)) {
        alert('Illegal bid');
        return;
    }

    socket.emit('playerMove', { quantity, faceValue });
});

liarButton.addEventListener('click', () => {
    socket.emit('playerMove', 'liar');
});

updateUI();
