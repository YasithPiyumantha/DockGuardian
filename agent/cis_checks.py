"""
CIS Docker Benchmark Checks
Implements 8+ security checks based on CIS Docker Benchmark v1.6.0
"""

import docker
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CISChecker:
    """Performs CIS Docker Benchmark security checks"""
    
    def __init__(self, docker_client):
        self.docker_client = docker_client
    
    def check_all(self, container_id):
        """Run all CIS checks on a container"""
        container = self.docker_client.containers.get(container_id)
        
        checks = [
            self.check_non_root_user(container),
            self.check_unnecessary_capabilities(container),
            self.check_privileged_containers(container),
            self.check_host_network_mode(container),
            self.check_memory_limits(container),
            self.check_readonly_filesystem(container),
            self.check_cpu_limits(container),
            self.check_pids_cgroup_limit(container),
        ]
        
        return checks
    
    def check_non_root_user(self, container):
        """CIS 4.1: Ensure that a user for the container has been created"""
        config = container.attrs['Config']
        user = config.get('User', '')
        
        is_root = user == '' or user == 'root' or user == '0'
        
        return {
            'checkId': 'CIS-4.1',
            'title': 'Non-root User',
            'description': 'Ensure that a user for the container has been created',
            'status': 'FAIL' if is_root else 'PASS',
            'severity': 'HIGH',
            'remediation': 'Add USER directive in Dockerfile or use --user flag'
        }
    
    def check_unnecessary_capabilities(self, container):
        """CIS 5.3: Ensure Linux Kernel Capabilities are restricted"""
        host_config = container.attrs['HostConfig']
        cap_add = host_config.get('CapAdd', [])
        
        dangerous_caps = ['SYS_ADMIN', 'NET_ADMIN', 'SYS_PTRACE', 'SYS_MODULE']
        has_dangerous = any(cap in dangerous_caps for cap in (cap_add or []))
        
        return {
            'checkId': 'CIS-5.3',
            'title': 'Kernel Capabilities Restriction',
            'description': 'Ensure Linux Kernel Capabilities are restricted',
            'status': 'FAIL' if has_dangerous else 'PASS',
            'severity': 'MEDIUM',
            'remediation': 'Remove unnecessary capabilities: ' + ', '.join(cap_add or [])
        }
    
    def check_privileged_containers(self, container):
        """CIS 5.4: Ensure privileged containers are not used"""
        host_config = container.attrs['HostConfig']
        privileged = host_config.get('Privileged', False)
        
        return {
            'checkId': 'CIS-5.4',
            'title': 'Privileged Containers',
            'description': 'Ensure privileged containers are not used',
            'status': 'FAIL' if privileged else 'PASS',
            'severity': 'CRITICAL',
            'remediation': 'Remove --privileged flag'
        }
    
    def check_host_network_mode(self, container):
        """CIS 5.10: Ensure the host\'s network namespace is not shared"""
        host_config = container.attrs['HostConfig']
        network_mode = host_config.get('NetworkMode', '')
        
        using_host_network = network_mode == 'host'
        
        return {
            'checkId': 'CIS-5.10',
            'title': 'Host Network Mode',
            'description': 'Ensure the host\'s network namespace is not shared',
            'status': 'FAIL' if using_host_network else 'PASS',
            'severity': 'HIGH',
            'remediation': 'Avoid using --network=host'
        }
    
    def check_memory_limits(self, container):
        """CIS 5.11: Ensure memory usage for container is limited"""
        host_config = container.attrs['HostConfig']
        memory = host_config.get('Memory', 0)
        
        # FIXED: Handle None values
        has_limit = memory is not None and memory > 0
        
        return {
            'checkId': 'CIS-5.11',
            'title': 'Memory Limits',
            'description': 'Ensure memory usage for container is limited',
            'status': 'PASS' if has_limit else 'WARN',
            'severity': 'MEDIUM',
            'remediation': 'Set memory limit using --memory flag'
        }
    
    def check_readonly_filesystem(self, container):
        """CIS 5.12: Ensure container root filesystem is mounted as read only"""
        host_config = container.attrs['HostConfig']
        readonly = host_config.get('ReadonlyRootfs', False)
        
        return {
            'checkId': 'CIS-5.12',
            'title': 'Read-only Root Filesystem',
            'description': 'Ensure container root filesystem is mounted as read only',
            'status': 'PASS' if readonly else 'WARN',
            'severity': 'MEDIUM',
            'remediation': 'Use --read-only flag when starting container'
        }
    
    def check_cpu_limits(self, container):
        """CIS 5.13: Ensure CPU priority is set appropriately"""
        host_config = container.attrs['HostConfig']
        cpu_shares = host_config.get('CpuShares', 0)
        cpu_period = host_config.get('CpuPeriod', 0)
        cpu_quota = host_config.get('CpuQuota', 0)
        
        # FIXED: Handle None values
        has_cpu_limit = (cpu_shares is not None and cpu_shares > 0) or \
                       (cpu_period is not None and cpu_period > 0 and 
                        cpu_quota is not None and cpu_quota > 0)
        
        return {
            'checkId': 'CIS-5.13',
            'title': 'CPU Limits',
            'description': 'Ensure CPU priority is set appropriately',
            'status': 'PASS' if has_cpu_limit else 'WARN',
            'severity': 'LOW',
            'remediation': 'Set CPU limits using --cpu-shares or --cpus flag'
        }
    
    def check_pids_cgroup_limit(self, container):
        """CIS 5.28: Ensure PIDs cgroup limit is used"""
        host_config = container.attrs['HostConfig']
        pids_limit = host_config.get('PidsLimit', 0)
        
        # FIXED: Handle None values - THIS WAS THE ORIGINAL ERROR
        has_limit = pids_limit is not None and pids_limit > 0
        
        return {
            'checkId': 'CIS-5.28',
            'title': 'PIDs cgroup Limit',
            'description': 'Ensure PIDs cgroup limit is used',
            'status': 'PASS' if has_limit else 'WARN',
            'severity': 'LOW',
            'remediation': 'Set PIDs limit using --pids-limit flag'
        }
