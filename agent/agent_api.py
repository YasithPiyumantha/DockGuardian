"""
Agent API - HTTP server for receiving healing commands from backend
"""
from flask import Flask, request, jsonify
import subprocess
import os
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get API key from environment
AGENT_API_KEY = os.getenv('API_KEY')

def verify_api_key():
    """Verify API key from request"""
    api_key = request.headers.get('X-API-Key')
    if not api_key or api_key != AGENT_API_KEY:
        return False
    return True

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'agent_id': os.getenv('AGENT_ID'),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/heal', methods=['POST'])
def heal_container():
    """Execute healing on a container"""
    if not verify_api_key():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.json
        container_id = data.get('containerId')
        issue_type = data.get('issueType')
        
        if not container_id or not issue_type:
            return jsonify({'error': 'containerId and issueType required'}), 400
        
        logger.info(f"Healing request: {container_id} - {issue_type}")
        
        # Execute healer script
        result = subprocess.run(
            ['python3', 'healer.py', 'fix', container_id, issue_type],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            return jsonify({
                'success': True,
                'message': 'Container healed successfully',
                'output': result.stdout
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Healing failed',
                'details': result.stderr
            }), 500
            
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Healing timeout'}), 500
    except Exception as e:
        logger.error(f"Healing error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/rollback', methods=['POST'])
def rollback_container():
    """Rollback a container to backup"""
    if not verify_api_key():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.json
        backup_file = data.get('backupFile')
        
        if not backup_file:
            return jsonify({'error': 'backupFile required'}), 400
        
        logger.info(f"Rollback request: {backup_file}")
        
        # Execute rollback
        result = subprocess.run(
            ['python3', 'healer.py', 'rollback', backup_file],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            return jsonify({
                'success': True,
                'message': 'Container rolled back successfully',
                'output': result.stdout
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Rollback failed',
                'details': result.stderr
            }), 500
            
    except Exception as e:
        logger.error(f"Rollback error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/backups', methods=['GET'])
def list_backups():
    """List available backups"""
    if not verify_api_key():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        backup_dir = os.path.expanduser('~/container_backups')
        if not os.path.exists(backup_dir):
            return jsonify({'backups': []})
        
        backups = []
        for file in os.listdir(backup_dir):
            if file.endswith('.tar'):
                file_path = os.path.join(backup_dir, file)
                stat = os.stat(file_path)
                backups.append({
                    'filename': file,
                    'size': stat.st_size,
                    'created': stat.st_ctime
                })
        
        return jsonify({'backups': backups})
    except Exception as e:
        logger.error(f"List backups error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    from datetime import datetime
    port = int(os.getenv('AGENT_PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
