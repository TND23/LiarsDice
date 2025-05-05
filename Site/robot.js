// robot module
const ort = require('onnxruntime-node');
const StateEncoder = require('./stateEncoder');
const path = require('path');

let model = null;

async function load_model() {
    try {
        // Get the directory of the current file
        const currentDir = __dirname;
        // Construct the path to the model file relative to the current directory
        const modelPath = path.join(currentDir, '..', 'models', 'deep_q', 'KidGloves2_model.pt.onnx');
        const session = await ort.InferenceSession.create(modelPath);
        model = session;
        return session;
    } catch (err) {
        console.error('Failed to load model:', err);
        throw err;
    }
}

async function load_custom_model(model_name) {
    try {
        // Get the directory of the current file
        const currentDir = __dirname;
        // Construct the path to the model file relative to the current directory
        const modelPath = path.join(currentDir, '..', 'models', 'custom', 'custom_model.onnx');
        const session = await ort.InferenceSession.create(modelPath);
        model = session;
        return session;
    } catch (err) {
        console.error('Failed to load custom model:', err);
        throw err;
    }
}

async function getAIMove(model, gameState) {
    try {
        // Encode the game state
        const inputTensor = StateEncoder.encodeState(gameState, 1); // 1 for AI player index

        // Run the model
        const feeds = { 'input': inputTensor };
        const results = await model.run(feeds);

        const action = StateEncoder.decodeAction(results.output, gameState);

        return action;
    } catch (err) {
        console.error('Error getting AI move:', err);
        throw err;
    }
}

module.exports = {
    load_model,
    getAIMove
};







