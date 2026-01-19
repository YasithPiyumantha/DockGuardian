"""
Autonomous Security Issue Healer
Automatically fixes container security issues with rollback capability
"""

import docker
import json
import os
import sys
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContainerHealer:
    """Autonomous container security healer with rollback"""
    
    def __init__(self, docker_client):
        self.docker_client = docker_client
        self.backups_dir = os.path.join(os.path.dirname(__file__), 'backups')
        os.makedirs(self.backups_dir, exist_ok=True)
    
    def create_backup(self, container_id):
        """Create a backup of container configuration"""
        try:
            container = self.docker_client.containers.get(container_id)
            
            backup_data = {
                'containerId': container.id,
                'containerName': container.name,
                'image': container.attrs['Config']['Image'],
                'config': container.attrs['Config'],
                'hostConfig': container.attrs['HostConfig'],
                'timestamp': datetime.now().isoformat()
            }
            
            backup_filename = f"backup_{container.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            backup_path = os.path.join(self.backups_dir, backup_filename)
            
            with open(backup_path, 'w') as f:
                json.dump(backup_data, f, indent=2)
            
            # Set restrictive permissions
            os.chmod(backup_path, 0o600)
            
            logger.info(f"✅ Backup created: {backup_path}")
            return backup_path
        
        except Exception as e:
            logger.error(f"❌ Backup failed: {e}")
            raise
    
    def fix_running_as_root(self, container_id):
        """Fix container running as root user"""
        try:
            container = self.docker_client.containers.get(container_id)
            
            # Create backup first
            backup_path = self.create_backup(container_id)
            
            logger.info(f"Fixing 'running as root' for {container.name}")
            
            # Get current configuration
            config = container.attrs['Config']
            host_config = container.attrs['HostConfig']
            image = config['Image']
            
            # Stop the container
            container.stop()
            logger.info("Container stopped")
            
            # Remove the old container
            container.remove()
            logger.info("Old container removed")
            
            # Create new container with non-root user
            # Prepare port mappings (expose ports but don't bind to host)
            exposed_ports = config.get('ExposedPorts')
            
            new_container = self.docker_client.containers.create(
                image=image,
                name=container.name,
                user='1000:1000',  # Non-root user
                command=config.get('Cmd'),
                environment=config.get('Env'),
                volumes=host_config.get('Binds'),
                detach=True
            )
            
            # Start the new container
            new_container.start()
            logger.info(f"✅ Container fixed and restarted as non-root user")
            
            return {
                'success': True,
                'backup': backup_path,
                'message': 'Container now running as non-root user'
            }
        
        except Exception as e:
            logger.error(f"❌ Fix failed: {e}")
            raise
    
    def fix_privileged_mode(self, container_id):
        """Remove privileged mode from container"""
        try:
            container = self.docker_client.containers.get(container_id)
            backup_path = self.create_backup(container_id)
            
            logger.info(f"Removing privileged mode from {container.name}")
            
            config = container.attrs['Config']
            host_config = container.attrs['HostConfig']
            image = config['Image']
            
            container.stop()
            container.remove()
            
            # Recreate without privileged flag
            new_container = self.docker_client.containers.create(
                image=image,
                name=container.name,
                privileged=False,  # Disable privileged mode
                command=config.get('Cmd'),
                environment=config.get('Env'),
                volumes=host_config.get('Binds'),
                ports=config.get('ExposedPorts'),
                detach=True
            )
            
            new_container.start()
            logger.info(f"✅ Privileged mode removed")
            
            return {
                'success': True,
                'backup': backup_path,
                'message': 'Privileged mode disabled'
            }
        
        except Exception as e:
            logger.error(f"❌ Fix failed: {e}")
            raise
    
    def fix_readonly_filesystem(self, container_id):
        """Enable read-only root filesystem"""
        try:
            container = self.docker_client.containers.get(container_id)
            backup_path = self.create_backup(container_id)
            
            logger.info(f"Enabling read-only filesystem for {container.name}")
            
            config = container.attrs['Config']
            host_config = container.attrs['HostConfig']
            image = config['Image']
            
            container.stop()
            container.remove()
            
            # Recreate with read-only root filesystem
            new_container = self.docker_client.containers.create(
                image=image,
                name=container.name,
                read_only=True,  # Enable read-only root
                command=config.get('Cmd'),
                environment=config.get('Env'),
                volumes=host_config.get('Binds'),
                ports=config.get('ExposedPorts'),
                detach=True
            )
            
            new_container.start()
            logger.info(f"✅ Read-only filesystem enabled")
            
            return {
                'success': True,
                'backup': backup_path,
                'message': 'Read-only root filesystem enabled'
            }
        
        except Exception as e:
            logger.error(f"❌ Fix failed: {e}")
            raise
    
    def rollback(self, backup_file):
        """Rollback container to backed up configuration"""
        try:
            backup_path = os.path.join(self.backups_dir, backup_file)
            
            if not os.path.exists(backup_path):
                raise FileNotFoundError(f"Backup file not found: {backup_file}")
            
            # Load backup
            with open(backup_path, 'r') as f:
                backup_data = json.load(f)
            
            container_name = backup_data['containerName']
            logger.info(f"Rolling back {container_name}")
            
            # Try to remove current container if it exists
            try:
                current_container = self.docker_client.containers.get(container_name)
                current_container.stop()
                current_container.remove()
                logger.info("Current container removed")
            except docker.errors.NotFound:
                logger.info("No existing container to remove")
            
            # Restore from backup
            config = backup_data['config']
            host_config = backup_data['hostConfig']
            
            restored_container = self.docker_client.containers.create(
                image=config['Image'],
                name=container_name,
                user=config.get('User'),
                command=config.get('Cmd'),
                environment=config.get('Env'),
                volumes=host_config.get('Binds'),
                privileged=host_config.get('Privileged'),
                read_only=host_config.get('ReadonlyRootfs'),
                detach=True
            )
            
            restored_container.start()
            logger.info(f"✅ Container rolled back successfully")
            
            return {
                'success': True,
                'message': f'Container {container_name} restored from backup'
            }
        
        except Exception as e:
            logger.error(f"❌ Rollback failed: {e}")
            raise


def main():
    """Command-line interface"""
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python healer.py fix <container_id> <issue_type>")
        print("  python healer.py rollback <backup_file>")
        print("\nIssue types: running_as_root, privileged, readonly_fs")
        sys.exit(1)
    
    command = sys.argv[1]
    
    try:
        docker_client = docker.from_env()
        healer = ContainerHealer(docker_client)
        
        if command == 'fix':
            container_id = sys.argv[2]
            issue_type = sys.argv[3]
            
            if issue_type == 'running_as_root':
                result = healer.fix_running_as_root(container_id)
            elif issue_type == 'privileged':
                result = healer.fix_privileged_mode(container_id)
            elif issue_type == 'readonly_fs':
                result = healer.fix_readonly_filesystem(container_id)
            else:
                print(f"Unknown issue type: {issue_type}")
                sys.exit(1)
            
            print(json.dumps(result, indent=2))
        
        elif command == 'rollback':
            backup_file = sys.argv[2]
            result = healer.rollback(backup_file)
            print(json.dumps(result, indent=2))
        
        else:
            print(f"Unknown command: {command}")
            sys.exit(1)
    
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
