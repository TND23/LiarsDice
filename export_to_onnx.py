import torch
from model import LiarsDiceModel, StateEncoder
from GameState import GameState
import os
from const import CUR_MODEL_PATH, CUR_MODEL_ONNX_PATH

def export_model_to_onnx(model_path: str = CUR_MODEL_PATH,
                        output_path: str = CUR_MODEL_ONNX_PATH):
    """
    Export a trained LiarsDiceModel to ONNX format.

    Args:
        model_path: Path to the trained PyTorch model
        output_path: Path where to save the ONNX model
    """
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Create a dummy game state
    dummy_state = GameState(
        current_player=0,
        hands=[(1,), (2,)],  # Two players with 1 die each, using single-integer tuples
        most_freq_opp_face=1,
        last_bid=None,
        players=2
    )

    # Load the trained model
    state_tensor = StateEncoder.encode_state(dummy_state, 0)  # Create dummy state
    input_size = state_tensor.size(1)
    model = LiarsDiceModel(input_size, 128, 100)
    model.load(model_path)

    # Set model to evaluation mode
    model.policy_network.eval()

    # Create dummy input for tracing
    dummy_input = torch.randn(1, input_size, dtype=torch.float32)

    # Export the policy network to ONNX
    torch.onnx.export(
        model.policy_network,  # Model to export
        (dummy_input,),        # Model input wrapped in tuple
        output_path,           # Output path
        export_params=True,    # Store the trained parameter weights inside the model file
        opset_version=12,      # ONNX version to export the model to
        do_constant_folding=True,  # Whether to execute constant folding for optimization
        input_names=['input'],     # Model input name
        output_names=['output'],   # Model output name
        dynamic_axes={
            'input': {0: 'batch_size'},  # Variable length axes
            'output': {0: 'batch_size'}
        }
    )

    print(f"Model successfully exported to {output_path}")

if __name__ == "__main__":
    export_model_to_onnx()
