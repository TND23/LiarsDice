const ort = require('onnxruntime-node');

// Constants matching Python implementation
const STATE_COMPONENTS = {
    'PLAYER_IDX': 0,
    'HANDS': 1,
    'MOST_FREQ_OPP_BID': 2,
    'LAST_BID': 3,
    'PLAYERS': 2
};

const FEATURE_WEIGHTS = {
    'PLAYER_IDX': 0.1,
    'HANDS': 0.9,
    'MOST_FREQ_OPP_BID': 2.0,
    'LAST_BID': 0.1,
    'PLAYERS': 0.1
};

const MAX_PLAYERS = 6; // Keep at 6 to match model's expected input size
const MAX_DICE_PER_PLAYER = 5;
const MAX_LAST_BID = 2;
const MAX_FACE_VALUE = 6;
const MIN_FACE_VALUE = 1;

class StateEncoder {
    static encodeState(gameState, playerIndex) {
        const inputVector = [];

        // Calculate vector sizes
        const vector_PLAYERS = 1;
        const vector_LAST_BID = 2; // quantity and face value
        const vector_HANDS = MAX_DICE_PER_PLAYER * MAX_PLAYERS; // 5 dice per player * 6 players
        const vector_MOST_FREQ_BID = 1; // quantity and face value of most frequent bid

        // Calculate total size needed
        const totalSize = vector_PLAYERS + vector_LAST_BID + vector_HANDS + vector_MOST_FREQ_BID;

        // Helper function to pad components
        const padComponent = (component, maxSize) => {
            let padded = [];
            if (!Array.isArray(component)) {
                component = [component];
            }
            if (component.length > maxSize) {
                padded = component.slice(0, maxSize);
            } else {
                padded = [...component];
                while (padded.length < maxSize) {
                    padded.push(0);
                }
            }
            return padded;
        };

        // Add current player index
        inputVector.push(playerIndex);

        // Encode hands - pad to represent all 6 players
        const humanHand = gameState.dice.human;
        const aiHand = gameState.dice.ai;
        const hands = [...humanHand, ...aiHand];

        // Pad with zeros for remaining players
        const remainingPlayers = MAX_PLAYERS - 2;
        const emptyHands = Array(remainingPlayers * MAX_DICE_PER_PLAYER).fill(0);
        const allHands = [...hands, ...emptyHands];

        const weight = FEATURE_WEIGHTS['HANDS'];
        const weightedHands = allHands.map(val => val * weight);
        inputVector.push(...padComponent(weightedHands, vector_HANDS));

        // Encode last bid
        if (gameState.lastBid && typeof gameState.lastBid === 'object') {
            const lastBid = gameState.lastBid;
            const bidWeight = FEATURE_WEIGHTS['LAST_BID'];
            const weightedBid = [lastBid.quantity * bidWeight, lastBid.faceValue * bidWeight];
            inputVector.push(...padComponent(weightedBid, vector_LAST_BID));
        } else {
            inputVector.push(...padComponent([0, 0], vector_LAST_BID));
        }

        // Encode most frequent bid with both quantity and face value
        const mostFreqBid = gameState.human_most_freq_bid || 0;
        const bidWeight = FEATURE_WEIGHTS['MOST_FREQ_OPP_BID'];
        const weightedBid = [mostFreqBid * bidWeight, 0]; // Add face value component
        inputVector.push(...padComponent(weightedBid, vector_MOST_FREQ_BID));

        // Verify the size matches
        if (inputVector.length !== totalSize) {
            throw new Error(`Expected size ${totalSize}, got ${inputVector.length}`);
        }

        // Create ONNX tensor
        return new ort.Tensor('float32', new Float32Array(inputVector), [1, totalSize]);
    }

    static decodeAction(actionProbs, gameState) {
        const output = actionProbs.data;

        // Get valid actions
        const validActions = [];
        const totalDice = gameState.dice.human.length + gameState.dice.ai.length;
        const aiHand = gameState.dice.ai;

        // Can always call liar if there's a previous bid
        if (gameState.lastBid) {
            validActions.push({ type: 'liar', index: 99 });
        }

        // Add valid bid actions
        if (gameState.lastBid) {
            const lastQuantity = gameState.lastBid.quantity;
            const lastFaceValue = gameState.lastBid.faceValue;

            // Same quantity, higher face
            for (let face = lastFaceValue + 1; face <= MAX_FACE_VALUE; face++) {
                if (aiHand.includes(face)) { // Only bid on faces the AI has
                    const index = (lastQuantity - 1) * MAX_FACE_VALUE + (face - 1);
                    validActions.push({ type: 'bid', index, quantity: lastQuantity, faceValue: face });
                }
            }

            // Higher quantity
            for (let quantity = lastQuantity + 1; quantity <= totalDice; quantity++) {
                for (let face = MIN_FACE_VALUE; face <= MAX_FACE_VALUE; face++) {
                    if (aiHand.includes(face)) { // Only bid on faces the AI has
                        const index = (quantity - 1) * MAX_FACE_VALUE + (face - 1);
                        validActions.push({ type: 'bid', index, quantity, faceValue: face });
                    }
                }
            }
        } else {
            // First bid - any valid combination
            for (let quantity = 1; quantity <= totalDice; quantity++) {
                for (let face = MIN_FACE_VALUE; face <= MAX_FACE_VALUE; face++) {
                    if (aiHand.includes(face)) { // Only bid on faces the AI has
                        const index = (quantity - 1) * MAX_FACE_VALUE + (face - 1);
                        validActions.push({ type: 'bid', index, quantity, faceValue: face });
                    }
                }
            }
        }

        // If no valid actions, call liar
        if (validActions.length === 0) {
            return 'liar';
        }

        // Get probabilities for valid actions
        const validProbs = validActions.map(action => output[action.index]);
        const maxProbIndex = validProbs.indexOf(Math.max(...validProbs));
        const chosenAction = validActions[maxProbIndex];

        if (chosenAction.type === 'liar') {
            return 'liar';
        }

        return { quantity: chosenAction.quantity, faceValue: chosenAction.faceValue };
    }
}

module.exports = StateEncoder;
