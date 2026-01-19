"""
Comprehensive Vulnerability Seed
Includes common packages found in Node.js containers
"""

import os
from pymongo import MongoClient, ASCENDING
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv('MONGODB_URI')

def seed_comprehensive():
    """Seed comprehensive vulnerabilities"""
    client = MongoClient(MONGODB_URI)
    db = client['dockguardian']
    collection = db.vulnerabilities
    
    collection.create_index([('cveId', ASCENDING)], unique=True)
    collection.create_index([('severity', ASCENDING)])
    collection.create_index([('affectedPackages.product', ASCENDING)])
    
    # Comprehensive list of vulnerabilities for common packages
    vulns = [
        # Node.js vulnerabilities
        {'cveId': 'CVE-2023-30581', 'description': 'Node.js mainModule.__proto__ bypass', 'cvssScore': 7.5, 'severity': 'HIGH',
         'affectedPackages': [{'vendor': 'nodejs', 'product': 'node', 'version': '18.0.0'}], 'exploitAvailable': False},
        {'cveId': 'CVE-2023-30589', 'description': 'Node.js CRLF injection', 'cvssScore': 6.5, 'severity': 'MEDIUM',
         'affectedPackages': [{'vendor': 'nodejs', 'product': 'node', 'version': '18.0.0'}], 'exploitAvailable': False},
        
        # npm/express vulnerabilities
        {'cveId': 'CVE-2024-29041', 'description': 'Express open redirect', 'cvssScore': 6.1, 'severity': 'MEDIUM',
         'affectedPackages': [{'vendor': 'expressjs', 'product': 'express', 'version': '4.0.0'}], 'exploitAvailable': False},
        
        # OpenSSL
        {'cveId': 'CVE-2023-0286', 'description': 'OpenSSL X.509 verification vulnerability', 'cvssScore': 7.4, 'severity': 'HIGH',
         'affectedPackages': [{'vendor': 'openssl', 'product': 'openssl', 'version': '3.0.0'}, {'vendor': 'openssl', 'product': 'libssl', 'version': '3.0.0'}], 'exploitAvailable': True},
        {'cveId': 'CVE-2023-2650', 'description': 'OpenSSL AES-SIV implementation vulnerability', 'cvssScore': 6.5, 'severity': 'MEDIUM',
         'affectedPackages': [{'vendor': 'openssl', 'product': 'openssl', 'version': '3.0.0'}], 'exploitAvailable': False},
        
        # curl/libcurl
        {'cveId': 'CVE-2023-38545', 'description': 'curl SOCKS5 heap buffer overflow', 'cvssScore': 9.8, 'severity': 'CRITICAL',
         'affectedPackages': [{'vendor': 'haxx', 'product': 'curl', 'version': '7.69.0'}, {'vendor': 'haxx', 'product': 'libcurl', 'version': '7.69.0'}], 'exploitAvailable': True},
        {'cveId': 'CVE-2023-38546', 'description': 'curl cookie injection', 'cvssScore': 3.7, 'severity': 'LOW',
         'affectedPackages': [{'vendor': 'haxx', 'product': 'curl', 'version': '7.69.0'}], 'exploitAvailable': False},
        
        # zlib
        {'cveId': 'CVE-2022-37434', 'description': 'zlib heap-based buffer overflow', 'cvssScore': 9.8, 'severity': 'CRITICAL',
         'affectedPackages': [{'vendor': 'gnu', 'product': 'zlib', 'version': '1.2.11'}, {'vendor': 'gnu', 'product': 'zlib1g', 'version': '1.2.11'}], 'exploitAvailable': False},
        
        # bash
        {'cveId': 'CVE-2022-3715', 'description': 'Bash heap overflow', 'cvssScore': 7.8, 'severity': 'HIGH',
         'affectedPackages': [{'vendor': 'gnu', 'product': 'bash', 'version': '5.0'}], 'exploitAvailable': False},
        
        # coreutils (common utilities)
        {'cveId': 'CVE-2022-26280', 'description': 'CoreUtils split command vulnerability', 'cvssScore': 7.5, 'severity': 'HIGH',
         'affectedPackages': [{'vendor': 'gnu', 'product': 'coreutils', 'version': '8.30'}], 'exploitAvailable': False},
        
        # libc/glibc
        {'cveId': 'CVE-2023-4911', 'description': 'glibc buffer overflow (Looney Tunables)', 'cvssScore': 7.8, 'severity': 'HIGH',
         'affectedPackages': [{'vendor': 'gnu', 'product': 'glibc', 'version': '2.34'}, {'vendor': 'gnu', 'product': 'libc6', 'version': '2.34'}], 'exploitAvailable': True},
        
        # systemd
        {'cveId': 'CVE-2023-26604', 'description': 'systemd privilege escalation', 'cvssScore': 7.8, 'severity': 'HIGH',
         'affectedPackages': [{'vendor': 'freedesktop', 'product': 'systemd', 'version': '250'}], 'exploitAvailable': False},
        
        # libxml2
        {'cveId': 'CVE-2023-39615', 'description': 'libxml2 out-of-bounds read', 'cvssScore': 6.5, 'severity': 'MEDIUM',
         'affectedPackages': [{'vendor': 'xmlsoft', 'product': 'libxml2', 'version': '2.9.0'}], 'exploitAvailable': False},
        
        # sqlite3
        {'cveId': 'CVE-2023-7104', 'description': 'SQLite heap buffer overflow', 'cvssScore': 7.3, 'severity': 'HIGH',
         'affectedPackages': [{'vendor': 'sqlite', 'product': 'sqlite', 'version': '3.40.0'}, {'vendor': 'sqlite', 'product': 'sqlite3', 'version': '3.40.0'}], 'exploitAvailable': False},
        
        # tar
        {'cveId': 'CVE-2022-48303', 'description': 'GNU tar directory traversal', 'cvssScore': 5.5, 'severity': 'MEDIUM',
         'affectedPackages': [{'vendor': 'gnu', 'product': 'tar', 'version': '1.34'}], 'exploitAvailable': False},
        
        # perl
        {'cveId': 'CVE-2023-31484', 'description': 'Perl HTTP::Tiny vulnerability', 'cvssScore': 8.1, 'severity': 'HIGH',
         'affectedPackages': [{'vendor': 'perl', 'product': 'perl', 'version': '5.30.0'}, {'vendor': 'perl', 'product': 'perl-base', 'version': '5.30.0'}], 'exploitAvailable': False},
        
        # git
        {'cveId': 'CVE-2023-29007', 'description': 'Git arbitrary configuration injection', 'cvssScore': 7.8, 'severity': 'HIGH',
         'affectedPackages': [{'vendor': 'git-scm', 'product': 'git', 'version': '2.30.0'}], 'exploitAvailable': False},
        
        # python
        {'cveId': 'CVE-2023-24329', 'description': 'Python URL parsing bypass', 'cvssScore': 7.5, 'severity': 'HIGH',
         'affectedPackages': [{'vendor': 'python', 'product': 'python', 'version': '3.9.0'}, {'vendor': 'python', 'product': 'python3', 'version': '3.9.0'}], 'exploitAvailable': False},
    ]
    
    inserted = 0
    for vuln in vulns:
        vuln['references'] = []
        vuln['publishedDate'] = '2023-01-01T00:00:00.000'
        vuln['lastModifiedDate'] = '2024-01-01T00:00:00.000'
        vuln['metadata'] = {'source': 'SEED'}
        
        try:
            collection.update_one({'cveId': vuln['cveId']}, {'$set': vuln}, upsert=True)
            inserted += 1
            print("✓ {}".format(vuln['cveId']))
        except Exception as e:
            print("✗ {}: {}".format(vuln['cveId'], e))
    
    stats = {
        'total': collection.count_documents({}),
        'critical': collection.count_documents({'severity': 'CRITICAL'}),
        'high': collection.count_documents({'severity': 'HIGH'}),
        'medium': collection.count_documents({'severity': 'MEDIUM'}),
        'low': collection.count_documents({'severity': 'LOW'})
    }
    
    print("\n" + "=" * 60)
    print("Seeded {} vulnerabilities".format(inserted))
    print("\nDatabase Statistics:")
    print("  Total: {}".format(stats['total']))
    print("  Critical: {}".format(stats['critical']))
    print("  High: {}".format(stats['high']))
    print("  Medium: {}".format(stats['medium']))
    print("  Low: {}".format(stats['low']))
    print("=" * 60)

if __name__ == '__main__':
    seed_comprehensive()
