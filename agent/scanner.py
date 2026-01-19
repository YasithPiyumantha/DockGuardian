"""
DockGuardian Scanner Agent
Scans Docker containers for vulnerabilities and security issues
"""

import docker
import json
import subprocess
import requests
import time
import logging
import os
import sys
import traceback
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

from cis_checks import CISChecker

# Load environment variables
load_dotenv()

# Configuration
BACKEND_URL = os.getenv('BACKEND_URL')
API_KEY = os.getenv('API_KEY')
AGENT_ID = os.getenv('AGENT_ID', f'agent-{os.uname().nodename}')
SCAN_INTERVAL = int(os.getenv('SCAN_INTERVAL', 3600))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def calculate_threat_score(vulnerabilities, cis_benchmarks):
    """Calculate threat score based on vulnerabilities and CIS benchmarks"""
    
    # Ensure we have valid lists (handle None or empty)
    if not vulnerabilities:
        vulnerabilities = []
    if not cis_benchmarks:
        cis_benchmarks = []
    
    # Count vulnerabilities by severity
    severity_counts = {
        'CRITICAL': 0,
        'HIGH': 0,
        'MEDIUM': 0,
        'LOW': 0
    }
    
    exploit_count = 0
    
    for vuln in vulnerabilities:
        severity = vuln.get('severity', 'UNKNOWN')
        if severity in severity_counts:
            severity_counts[severity] += 1
        
        if vuln.get('exploitAvailable'):
            exploit_count += 1
    
    # Count CIS failures
    cis_failed = sum(1 for check in cis_benchmarks if check.get('status') == 'FAIL')
    cis_total = len(cis_benchmarks)
    
    # Calculate component scores (0-100)
    vuln_score = min(100, (
        severity_counts['CRITICAL'] * 25 +
        severity_counts['HIGH'] * 15 +
        severity_counts['MEDIUM'] * 5 +
        severity_counts['LOW'] * 1
    ))
    
    exploit_score = min(100, exploit_count * 20)
    
    cis_score = (cis_failed / cis_total * 100) if cis_total > 0 else 0
    
    # Weighted final score (ensure all values are floats)
    final_score = (
        float(vuln_score) * 0.5 +
        float(exploit_score) * 0.3 +
        float(cis_score) * 0.2
    )
    
    # Determine risk level
    if final_score >= 80:
        risk_level = 'CRITICAL'
    elif final_score >= 60:
        risk_level = 'HIGH'
    elif final_score >= 40:
        risk_level = 'MEDIUM'
    elif final_score >= 20:
        risk_level = 'LOW'
    else:
        risk_level = 'MINIMAL'
    
    return {
        'total': round(final_score, 2),
        'riskLevel': risk_level,
        'components': {
            'vulnerabilityScore': round(vuln_score, 2),
            'exploitScore': round(exploit_score, 2),
            'cisScore': round(cis_score, 2)
        },
        'statistics': {
            'totalVulnerabilities': len(vulnerabilities),
            'criticalVulns': severity_counts['CRITICAL'],
            'highVulns': severity_counts['HIGH'],
            'mediumVulns': severity_counts['MEDIUM'],
            'lowVulns': severity_counts['LOW'],
            'exploitsAvailable': exploit_count,
            'cisChecksFailed': cis_failed,
            'cisChecksTotal': cis_total
        }
    }


class DockGuardianScanner:
    """Main scanner class"""
    
    def __init__(self):
        self.docker_client = docker.from_env()
        self.cis_checker = CISChecker(self.docker_client)
        self.backend_url = BACKEND_URL
        self.api_key = API_KEY
        self.agent_id = AGENT_ID
    
    def scan_image_with_syft(self, image):
        """Scan container image with Syft for vulnerabilities"""
        try:
            logger.info(f"Running Syft scan on {image}")
            
            # Run Syft
            result = subprocess.run(
                ['syft', image, '-o', 'json'],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                logger.error(f"Syft scan failed: {result.stderr}")
                return []
            
            # Parse Syft output
            syft_data = json.loads(result.stdout)
            artifacts = syft_data.get('artifacts', [])
            
            logger.info(f"Found {len(artifacts)} packages")
            
            # Extract package information
            packages = []
            for artifact in artifacts:
                packages.append({
                    'name': artifact.get('name'),
                    'version': artifact.get('version'),
                    'type': artifact.get('type'),
                    'locations': artifact.get('locations', [])
                })
            
            return packages
        
        except subprocess.TimeoutExpired:
            logger.error(f"Syft scan timed out for {image}")
            return []
        except Exception as e:
            logger.error(f"Syft scan error: {e}")
            return []
    
    def match_vulnerabilities(self, packages):
        """Match packages against vulnerability database"""
        try:
            if not packages:
                return []
            
            # Query backend for vulnerabilities
            vulnerabilities = []
            
            for package in packages:
                response = requests.get(
                    f"{self.backend_url}/api/vulnerabilities/search",
                    params={'package': package['name']},
                    headers={'X-API-Key': self.api_key},
                    timeout=60
                )
                
                if response.status_code == 200:
                    data = response.json()
                    for vuln in data.get('vulnerabilities', []):
                        vulnerabilities.append({
                            'cveId': vuln['cveId'],
                            'package': package['name'],
                            'version': package['version'],
                            'severity': vuln['severity'],
                            'cvssScore': vuln['cvssScore'],
                            'description': vuln['description'],
                            'fixAvailable': False,
                            'exploitAvailable': vuln.get('exploitAvailable', False),
                            'metadata': vuln.get('metadata', {})
                        })
            
            logger.info(f"Matched {len(vulnerabilities)} vulnerabilities")
            return vulnerabilities
        
        except Exception as e:
            logger.error(f"Vulnerability matching error: {e}")
            return []

    def scan_container(self, container_id):
        """Scan a single container"""
        try:
            start_time = time.time()
            
            container = self.docker_client.containers.get(container_id)
            logger.info(f"Scanning container: {container.name} ({container.id[:12]})")
            
            # Get container details
            image = container.attrs['Config']['Image']
            
            # 1. Scan image with Syft
            packages = self.scan_image_with_syft(image)
            if packages is None:
                logger.warning(f"Syft scan returned None for {container.name}, using empty list")
                packages = []
            
            # 2. Match vulnerabilities
            vulnerabilities = self.match_vulnerabilities(packages)
            if vulnerabilities is None:
                logger.warning(f"Vulnerability matching returned None for {container.name}, using empty list")
                vulnerabilities = []
            
            # 3. Run CIS benchmarks
            cis_benchmarks = self.cis_checker.check_all(container_id)
            if cis_benchmarks is None:
                logger.warning(f"CIS checks returned None for {container.name}, using empty list")
                cis_benchmarks = []
            
            # Ensure all vulnerabilities have required fields
            validated_vulns = []
            for vuln in vulnerabilities:
                if isinstance(vuln, dict):
                    # Ensure severity exists and is valid
                    if 'severity' not in vuln or vuln['severity'] is None:
                        vuln['severity'] = 'UNKNOWN'
                    # Ensure exploitAvailable is boolean
                    if 'exploitAvailable' not in vuln:
                        vuln['exploitAvailable'] = False
                    validated_vulns.append(vuln)
            
            # Ensure all CIS checks have required fields
            validated_cis = []
            for check in cis_benchmarks:
                if isinstance(check, dict):
                    # Ensure status exists
                    if 'status' not in check or check['status'] is None:
                        check['status'] = 'UNKNOWN'
                    # Ensure severity exists
                    if 'severity' not in check or check['severity'] is None:
                        check['severity'] = 'INFO'
                    validated_cis.append(check)
            
            # Calculate threat score with validated data
            threat_score = calculate_threat_score(validated_vulns, validated_cis)
            
            scan_duration = time.time() - start_time
            
            scan_result = {
                'scanId': f"{self.agent_id}-{container.id[:12]}-{int(time.time())}",
                'agentId': self.agent_id,
                'containerId': container.id,
                'containerName': container.name,
                'image': image,
                'vulnerabilities': validated_vulns,
                'cisBenchmarks': validated_cis,
                'threatScore': threat_score,
                'scanDuration': scan_duration,
                'packagesScanned': len(packages),
                'scanDate': datetime.now().isoformat()
            }
            
            logger.info(f"✅ Scan completed: {container.name}")
            logger.info(f"   Vulnerabilities: {len(validated_vulns)}")
            logger.info(f"   CIS checks: {len(validated_cis)}")
            logger.info(f"   Threat Score: {threat_score['total']}/100 ({threat_score['riskLevel']})")
            logger.info(f"   Duration: {scan_duration:.2f}s")
            
            return scan_result
        
        except Exception as e:
            logger.error(f"❌ Container scan failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def scan_all_containers_parallel(self, max_workers=5):
        """Scan all containers in parallel"""
        containers = self.docker_client.containers.list()
        
        if not containers:
            logger.info("No running containers found")
            return []
        
        logger.info(f"Found {len(containers)} running containers")
        logger.info(f"Starting parallel scan with {max_workers} workers")
        
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all scan tasks
            future_to_container = {
                executor.submit(self.scan_container, container.id): container
                for container in containers
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_container):
                container = future_to_container[future]
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                except Exception as e:
                    logger.error(f"Scan failed for {container.name}: {e}")
        
        logger.info(f"✅ Parallel scan complete: {len(results)} containers scanned")
        return results
    
    def submit_results(self, scan_results):
        """Submit scan results to backend"""
        for result in scan_results:
            try:
                response = requests.post(
                    f"{self.backend_url}/api/scans/submit",
                    json=result,
                    headers={'X-API-Key': self.api_key},
                    timeout=30
                )
                
                if response.status_code == 201:
                    logger.info(f"✅ Results submitted for {result['containerName']}")
                else:
                    logger.error(f"❌ Submit failed: {response.text}")
            
            except Exception as e:
                logger.error(f"❌ Submit error: {e}")
    
    def run_once(self):
        """Run a single scan cycle"""
        logger.info("=" * 60)
        logger.info("Starting scan cycle")
        logger.info("=" * 60)
        
        # Scan all containers in parallel
        results = self.scan_all_containers_parallel()
        
        # Submit results to backend
        if results:
            self.submit_results(results)
        
        logger.info("=" * 60)
        logger.info("Scan cycle complete")
        logger.info("=" * 60)
    
    def run_continuous(self):
        """Run scanner continuously"""
        logger.info(f"DockGuardian Scanner started (Agent ID: {self.agent_id})")
        logger.info(f"Scan interval: {SCAN_INTERVAL} seconds")
        
        while True:
            try:
                self.run_once()
                logger.info(f"Sleeping for {SCAN_INTERVAL} seconds...")
                time.sleep(SCAN_INTERVAL)
            
            except KeyboardInterrupt:
                logger.info("Scanner stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in scan cycle: {e}")
                time.sleep(60)  # Wait before retrying


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='DockGuardian Scanner')
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    parser.add_argument('--container', type=str, help='Scan specific container by ID')
    
    args = parser.parse_args()
    
    scanner = DockGuardianScanner()
    
    if args.container:
        # Scan specific container
        logger.info(f"Scanning specific container: {args.container}")
        result = scanner.scan_container(args.container)
        
        if result:
            # Submit single result
            scanner.submit_results([result])
            logger.info("✅ Container scan completed and submitted")
        else:
            logger.error("❌ Container scan failed")
            sys.exit(1)
    elif args.once:
        # Run once and exit
        scanner.run_once()
    else:
        # Run continuously
        scanner.run_continuous()


if __name__ == '__main__':
    main()
