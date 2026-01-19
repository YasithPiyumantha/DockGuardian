"""
Agent Task Poller - Polls backend for healing and scan tasks and executes them
"""
from dotenv import load_dotenv
import requests
import time
import subprocess
import os
import logging
from datetime import datetime

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BACKEND_URL = os.getenv('BACKEND_URL', 'https://dockguardian-backend-69812048898.us-central1.run.app')
AGENT_ID = os.getenv('AGENT_ID')
API_KEY = os.getenv('API_KEY')
POLL_INTERVAL = 5
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

CIS_TO_ISSUE_TYPE = {
    'CIS-4.1': 'running_as_root',
    'CIS-5.4': 'privileged',
    'CIS-5.12': 'readonly_fs'
}

def get_pending_tasks():
    """Fetch pending healing tasks from backend"""
    try:
        url = f"{BACKEND_URL}/api/healer/tasks/{AGENT_ID}/pending"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('tasks', [])
        else:
            logger.error(f"Failed to get healing tasks: {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"Error fetching healing tasks: {e}")
        return []

def get_pending_scan_tasks():
    """Fetch pending scan tasks from backend"""
    try:
        url = f"{BACKEND_URL}/api/scans/tasks/pending"
        headers = {'X-API-Key': API_KEY}
        params = {'agentId': AGENT_ID}
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('tasks', [])
        else:
            logger.error(f"Failed to get scan tasks: {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"Error fetching scan tasks: {e}")
        return []

def update_task_status(task_id, status, result=None, error=None):
    """Update task status in backend"""
    try:
        url = f"{BACKEND_URL}/api/healer/tasks/{task_id}/status"
        payload = {'status': status}
        
        if result:
            payload['result'] = result
        if error:
            payload['error'] = error
        
        response = requests.put(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            logger.info(f"✅ Task {task_id} updated to {status}")
        else:
            logger.error(f"Failed to update task: {response.status_code}")
    except Exception as e:
        logger.error(f"Error updating task: {e}")

def execute_healing(task):
    """Execute healing for a task"""
    # Skip if this is a scan task (not a healing task)
    if task.get('taskType') == 'scan':
        return
    
    task_id = task['taskId']
    container_id = task['containerId']
    issue_type = task.get('issueType')
    
    if not issue_type:
        logger.error(f"❌ No issueType for healing task: {task_id}")
        update_task_status(task_id, 'failed', error='Missing issueType')
        return
    
    if issue_type.startswith('rollback:'):
        execute_rollback(task)
        return
    
    healer_issue_type = CIS_TO_ISSUE_TYPE.get(issue_type)
    
    if not healer_issue_type:
        logger.error(f"❌ Unknown CIS issue type: {issue_type}")
        update_task_status(task_id, 'failed', error=f'Unknown issue type: {issue_type}')
        return
    
    logger.info(f"🔧 Executing healing: {container_id} - {issue_type} -> {healer_issue_type}")
    
    update_task_status(task_id, 'running')
    
    try:
        healer_path = os.path.join(SCRIPT_DIR, 'healer.py')
        
        logger.info(f"Running: python3 {healer_path} fix {container_id} {healer_issue_type}")
        
        result = subprocess.run(
            ['python3', healer_path, 'fix', container_id, healer_issue_type],
            capture_output=True,
            text=True,
            timeout=300,
            cwd=SCRIPT_DIR
        )
        
        if result.returncode == 0:
            logger.info(f"✅ Healing successful: {task_id}")
            logger.info(f"Output: {result.stdout}")
            update_task_status(
                task_id, 
                'completed',
                result={'output': result.stdout, 'success': True}
            )
        else:
            logger.error(f"❌ Healing failed: {task_id}")
            logger.error(f"stdout: {result.stdout}")
            logger.error(f"stderr: {result.stderr}")
            update_task_status(
                task_id,
                'failed',
                error=result.stderr or result.stdout or 'Unknown error'
            )
    except subprocess.TimeoutExpired:
        logger.error(f"⏱️  Healing timeout: {task_id}")
        update_task_status(task_id, 'failed', error='Healing timeout')
    except Exception as e:
        logger.error(f"❌ Healing error: {e}")
        update_task_status(task_id, 'failed', error=str(e))

def execute_rollback(task):
    """Execute rollback for a task"""
    task_id = task['taskId']
    issue_type = task['issueType']
    
    # Extract backup filename (format: "rollback:filename")
    backup_file = issue_type.replace('rollback:', '')
    
    logger.info(f"🔄 Executing rollback: {backup_file}")
    
    update_task_status(task_id, 'running')
    
    try:
        healer_path = os.path.join(SCRIPT_DIR, 'healer.py')
        
        # Pass just the filename, healer.py will add backups/ folder
        logger.info(f"Running: python3 {healer_path} rollback {backup_file}")
        
        result = subprocess.run(
            ['python3', healer_path, 'rollback', backup_file],
            capture_output=True,
            text=True,
            timeout=300,
            cwd=SCRIPT_DIR
        )
        
        if result.returncode == 0:
            logger.info(f"✅ Rollback successful: {task_id}")
            logger.info(f"Output: {result.stdout}")
            update_task_status(
                task_id, 
                'completed',
                result={'output': result.stdout, 'success': True}
            )
        else:
            logger.error(f"❌ Rollback failed: {task_id}")
            logger.error(f"stdout: {result.stdout}")
            logger.error(f"stderr: {result.stderr}")
            update_task_status(
                task_id,
                'failed',
                error=result.stderr or result.stdout or 'Unknown error'
            )
    except subprocess.TimeoutExpired:
        logger.error(f"⏱️  Rollback timeout: {task_id}")
        update_task_status(task_id, 'failed', error='Rollback timeout')
    except Exception as e:
        logger.error(f"❌ Rollback error: {e}")
        update_task_status(task_id, 'failed', error=str(e))

def execute_scan(task):
    """Execute scan for a task"""
    task_id = task['taskId']
    container_id = task['containerId']
    
    logger.info(f"🔍 Executing scan: {container_id}")
    
    update_task_status(task_id, 'running')
    
    try:
        scanner_path = os.path.join(SCRIPT_DIR, 'scanner.py')
        
        # Run scanner for specific container
        logger.info(f"Running: python3 {scanner_path} --container {container_id}")
        
        result = subprocess.run(
            ['python3', scanner_path, '--container', container_id],
            capture_output=True,
            text=True,
            timeout=600,  # Scans can take longer
            cwd=SCRIPT_DIR
        )
        
        if result.returncode == 0:
            logger.info(f"✅ Scan successful: {task_id}")
            logger.info(f"Output: {result.stdout}")
            update_task_status(
                task_id, 
                'completed',
                result={'output': result.stdout, 'success': True}
            )
        else:
            logger.error(f"❌ Scan failed: {task_id}")
            logger.error(f"stdout: {result.stdout}")
            logger.error(f"stderr: {result.stderr}")
            update_task_status(
                task_id,
                'failed',
                error=result.stderr or result.stdout or 'Scan failed'
            )
    except subprocess.TimeoutExpired:
        logger.error(f"⏱️  Scan timeout: {task_id}")
        update_task_status(task_id, 'failed', error='Scan timeout')
    except Exception as e:
        logger.error(f"❌ Scan error: {e}")
        update_task_status(task_id, 'failed', error=str(e))

def main():
    """Main polling loop"""
    if not AGENT_ID:
        logger.error("❌ AGENT_ID environment variable not set")
        return
    
    if not API_KEY:
        logger.error("❌ API_KEY environment variable not set")
        return
    
    logger.info(f"🤖 Agent poller started: {AGENT_ID}")
    logger.info(f"🔌 Backend URL: {BACKEND_URL}")
    logger.info(f"⏱️  Poll interval: {POLL_INTERVAL}s")
    logger.info(f"📁 Script directory: {SCRIPT_DIR}")
    
    while True:
        try:
            # Poll for healing tasks
            heal_tasks = get_pending_tasks()
            if heal_tasks:
                logger.info(f"🔧 Found {len(heal_tasks)} pending healing task(s)")
                for task in heal_tasks:
                    execute_healing(task)
            
            # Poll for scan tasks
            scan_tasks = get_pending_scan_tasks()
            if scan_tasks:
                logger.info(f"🔍 Found {len(scan_tasks)} pending scan task(s)")
                for task in scan_tasks:
                    execute_scan(task)
            
            time.sleep(POLL_INTERVAL)
            
        except KeyboardInterrupt:
            logger.info("👋 Poller stopped by user")
            break
        except Exception as e:
            logger.error(f"❌ Poller error: {e}")
            time.sleep(POLL_INTERVAL)

if __name__ == '__main__':
    main()
