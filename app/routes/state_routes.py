from flask import Blueprint, request, jsonify
import pandas as pd
from python_scripts.state_machine import DataState, DataStateMachine

state_blueprint = Blueprint('state', __name__)
@state_blueprint.route('/run-state-machine', methods=['POST'])
def run_state_machine():
    """Run the state machine on uploaded data."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    try:
        data = pd.read_csv(file)
    except Exception as e:
        return jsonify({'error': f'Failed to read file: {e}'}), 400

    # Initialize and run the state machine
    state_machine = DataStateMachine(data)
    while state_machine.state != DataState.FINAL:
        state_machine.process()

    # Return processed data
    return jsonify({'message': 'Data processed successfully', 'data': state_machine.data.to_dict(orient='records')})