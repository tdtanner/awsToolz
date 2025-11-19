"""
Burn It All Down - AWS Resource Cleanup Tool
Flask web application for discovering and deleting AWS resources
"""
from flask import Flask, render_template, request, jsonify, session
from aws_inventory import AWSInventory
from aws_destroyer import AWSDestroyer
import logging
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')


@app.route('/api/inventory', methods=['POST'])
def inventory():
    """Run inventory on AWS account/region"""
    try:
        data = request.json
        profile = data.get('profile')
        region = data.get('region')

        if not profile or not region:
            return jsonify({'error': 'Profile and region are required'}), 400

        # Store in session for later use
        session['profile'] = profile
        session['region'] = region

        # Run inventory
        logger.info(f"Running inventory for profile={profile}, region={region}")
        inventory_manager = AWSInventory(profile, region)
        resources = inventory_manager.discover_all()

        return jsonify({
            'success': True,
            'resources': resources
        })

    except Exception as e:
        logger.error(f"Error running inventory: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/delete', methods=['POST'])
def delete_resources():
    """Delete selected resources"""
    try:
        data = request.json
        selections = data.get('selections', {})

        profile = session.get('profile')
        region = session.get('region')

        if not profile or not region:
            return jsonify({'error': 'Session expired. Please run inventory again.'}), 400

        logger.info(f"Starting deletion for profile={profile}, region={region}")
        destroyer = AWSDestroyer(profile, region)

        all_results = []

        # Delete resources by type
        for resource_type, resource_ids in selections.items():
            if resource_ids:
                logger.info(f"Deleting {len(resource_ids)} {resource_type} resources")
                results = destroyer.delete_resources(resource_type, resource_ids)
                all_results.extend(results)

        return jsonify({
            'success': True,
            'results': all_results
        })

    except Exception as e:
        logger.error(f"Error deleting resources: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=8080)
