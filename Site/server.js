const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const cors = require('cors');
const path = require('path');
const { load_model, getAIMove } = require('./robot');
const { getDiceImages } = require('./dice');
const app = express();
const server = http.createServer(app);
const io = socketIo(server);

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// Verify image paths
app.get('/verify-images', (req, res) => {
    const imagesDir = path.join(__dirname, 'public', 'assets', 'images');
    const images = getDiceImages();
    res.json({
        imagesDir,
        images
    });
});

// Game state
let gameState = {
    currentPlayer: 'human',
    lastBid: null,
    history: [],
    dice: {
        human: [],
        ai: []
    },
    human_most_freq_bid: 1, // track the faec value most used by human each round
};

humanDiceCount = 5;
aiDiceCount = 5;
humanMostFreqBid = {};
gameOver = false;

// Initialize dice images
const diceImages = getDiceImages();

// Initialize model
let model = null;
load_model().then(session => {
    model = session;
}).catch(err => {
    console.error('Failed to load model:', err);
});

// Socket events
io.on('connection', (socket) => {
    gameState.dice.human = Array.from({ length: humanDiceCount },
        () => Math.floor(Math.random() * 6) + 1);
    gameState.dice.ai = Array.from({ length: aiDiceCount },
        () => Math.floor(Math.random() * 6) + 1);
    // Send initial game state and dice images to the client
    socket.emit('gameState', gameState);
    socket.emit('diceImages', diceImages);
    socket.emit('hands', gameState.dice);
    function check_liar_call(bid) {
        let all_dice = [...gameState.dice.human, ...gameState.dice.ai];
        let count = 0;
        for (let i = 0; i < all_dice.length; i++) {
            if (all_dice[i] == bid.faceValue) {
                count++;
            }
        }
        // Return true if the bid was incorrect (count < quantity)
        return count < bid.quantity;
    }
    function check_game_over() {
        if (gameState.dice.human.length === 0 || gameState.dice.ai.length === 0) {
            const winner = gameState.dice.human.length === 0 ? 'ai' : 'human';
            io.emit('gameOver', { winner, gameState });
            return true;
        }
        return false;
    }


    socket.on('playerMove', async (move) => {
        if (gameState.currentPlayer !== 'human') {
            socket.emit('error', 'Not your turn');
            return;
        }

        gameState.lastBid = move;
        if (move === 'liar') {
            // Get the last actual bid from history
            const lastBid = gameState.history[gameState.history.length - 1]?.move;
            if (!lastBid) {
                console.error('No previous bid found');
                return;
            }
            const isCorrect = check_liar_call(lastBid);

            // Update game state based on liar call
            if (isCorrect) {
                if (gameState.dice.ai.length > 0) {
                    gameState.dice.ai.pop();
                    socket.emit('removeDie', 'ai');
                }
                console.log('AI loses a die');
                // AI gets to start the next round
                gameState.currentPlayer = 'ai';
            } else {
                console.log('Human loses a die');
                if (gameState.dice.human.length > 0) {
                    gameState.dice.human.pop();
                    socket.emit('removeDie', 'human');
                }
                // Human gets to start the next round
                gameState.currentPlayer = 'human';
            }

            // Reset round state
            gameState.history = [];
            gameState.lastBid = null;
            humanMostFreqBid = {};

            // Check for game over
            if (check_game_over()) {
                return;
            }

            // Broadcast updated state
            io.emit('gameState', gameState);

            // If it's AI's turn, get its move
            if (gameState.currentPlayer === 'ai') {
                setTimeout(async () => {
                    try {
                        if (model) {
                            const aiMove = await getAIMove(model, gameState);
                            gameState.lastBid = aiMove;
                            gameState.history.push({ player: 'ai', move: aiMove });
                            gameState.currentPlayer = 'human';
                            io.emit('gameState', gameState);
                        } else {
                            console.error('Model not loaded');
                        }
                    } catch (err) {
                        console.error('Error getting AI move:', err);
                    }
                }, 500);
            }
        } else {
            // Handle regular bid
            if (move.faceValue in humanMostFreqBid) {
                humanMostFreqBid[move.faceValue]++;
            } else {
                humanMostFreqBid[move.faceValue] = 1;
            }
            gameState.human_most_freq_bid = Math.max(...Object.values(humanMostFreqBid));
            gameState.history.push({ player: 'human', move });
            gameState.currentPlayer = 'ai';

            // Broadcast updated state
            io.emit('gameState', gameState);

            // Get AI move
            try {
                if (model) {
                    const aiMove = await getAIMove(model, gameState);
                    gameState.lastBid = aiMove;
                    gameState.history.push({ player: 'ai', move: aiMove });

                    if (aiMove === 'liar') {
                        // Get the last actual bid from history
                        const lastBid = gameState.history[gameState.history.length - 1]?.move;
                        if (!lastBid) {
                            console.error('No previous bid found');
                            return;
                        }
                        const isCorrect = check_liar_call(lastBid);

                        if (isCorrect) {
                            // AI was correct - human loses a die
                            gameState.dice.human.pop();
                            socket.emit('removeDie', 'human');
                            // AI gets to start the next round
                            gameState.currentPlayer = 'ai';
                        } else {
                            // AI was wrong - AI loses a die
                            gameState.dice.ai.pop();
                            socket.emit('removeDie', 'ai');
                            // Human gets to start the next round
                            gameState.currentPlayer = 'human';
                        }

                        // Reset round state
                        gameState.history = [];
                        gameState.lastBid = null;
                        humanMostFreqBid = {};

                        // Check for game over
                        if (check_game_over()) {
                            return;
                        }
                    } else {
                        gameState.currentPlayer = 'human';
                    }

                    io.emit('gameState', gameState);
                }
            } catch (err) {
                console.error('Error getting AI move:', err);
            }
        }
    });

    socket.emit('rollDice', gameState);

    socket.on('playAgain', () => {
        // Reset game state
        gameState = {
            currentPlayer: 'human',
            lastBid: null,
            history: [],
            dice: {
                human: Array.from({ length: humanDiceCount }, () => Math.floor(Math.random() * 6) + 1),
                ai: Array.from({ length: aiDiceCount }, () => Math.floor(Math.random() * 6) + 1)
            }
        };
        humanMostFreqBid = {};

        // Send new game state to all clients
        io.emit('playAgain', gameState);
    });

    socket.on('disconnect', () => {
        console.log('Client disconnected');
    });
});

// Start server
const PORT = 3001;
server.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});




