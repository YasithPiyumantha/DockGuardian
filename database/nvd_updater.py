
"""
NVD Database Updater 
"""

import os
import sys
import requests
import time
from datetime import datetime
from pymongo import MongoClient, ASCENDING
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv('MONGODB_URI')
NVD_API_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"

def connect_to_mongodb():
    try:
        client = MongoClient(MONGODB_URI)
        db = client['dockguardian']
        print("✓ Connected to MongoDB")
        return db
    except Exception as e:
        print(f"✗ MongoDB connection failed: {e}")
        sys.exit(1)

def fetch_cves_by_month(year, month):
    """Fetch CVEs for a specific month"""
    # Calculate month boundaries
    if month == 12:
        next_month = 1
        next_year = year + 1
    else:
        next_month = month + 1
        next_year = year
    
    start_date = f"{year}-{month:02d}-01T00:00:00.000Z"
    end_date = f"{next_year}-{next_month:02d}-01T00:00:00.000Z"
    
    print(f"  Fetching {year}-{month:02d}...", end=' ', flush=True)
    
    vulnerabilities = []
    start_index = 0
    results_per_page = 2000
    
    while True:
        try:
            params = {
                'lastModStartDate': start_date,
                'lastModEndDate': end_date,
                'resultsPerPage': results_per_page,
                'startIndex': start_index
            }
            
            response = requests.get(NVD_API_URL, params=params, timeout=120)
            
            if response.status_code != 200:
                print(f"✗ HTTP {response.status_code}")
                break
            
            data = response.json()
            cves = data.get('vulnerabilities', [])
            total_results = data.get('totalResults', 0)
            
            if not cves:
                break
            
            for item in cves:
                try:
                    cve_data = item.get('cve', {})
                    cve_id = cve_data.get('id')
                    if not cve_id:
                        continue
                    
                    descriptions = cve_data.get('descriptions', [])
                    description = 'No description available'
                    for desc in descriptions:
                        if desc.get('lang') == 'en':
                            description = desc.get('value', 'No description available')
                            break
                    
                    cvss_score = 0.0
                    severity = 'UNKNOWN'
                    metrics = cve_data.get('metrics', {})
                    
                    if 'cvssMetricV31' in metrics and metrics['cvssMetricV31']:
                        cvss_data = metrics['cvssMetricV31'][0].get('cvssData', {})
                        cvss_score = cvss_data.get('baseScore', 0.0)
                        severity = cvss_data.get('baseSeverity', 'UNKNOWN')
                    elif 'cvssMetricV30' in metrics and metrics['cvssMetricV30']:
                        cvss_data = metrics['cvssMetricV30'][0].get('cvssData', {})
                        cvss_score = cvss_data.get('baseScore', 0.0)
                        severity = cvss_data.get('baseSeverity', 'UNKNOWN')
                    elif 'cvssMetricV2' in metrics and metrics['cvssMetricV2']:
                        cvss_data = metrics['cvssMetricV2'][0].get('cvssData', {})
                        cvss_score = cvss_data.get('baseScore', 0.0)
                        if cvss_score >= 7.0:
                            severity = 'HIGH'
                        elif cvss_score >= 4.0:
                            severity = 'MEDIUM'
                        else:
                            severity = 'LOW'
                    
                    affected_packages = []
                    configurations = cve_data.get('configurations', [])
                    for config in configurations:
                        nodes = config.get('nodes', [])
                        for node in nodes:
                            cpe_matches = node.get('cpeMatch', [])
                            for cpe in cpe_matches:
                                cpe_uri = cpe.get('criteria', '')
                                if cpe_uri and cpe_uri.startswith('cpe:2.3:'):
                                    parts = cpe_uri.split(':')
                                    if len(parts) >= 5:
                                        vendor = parts[3] if parts[3] != '*' else 'unknown'
                                        product = parts[4] if parts[4] != '*' else 'unknown'
                                        version = parts[5] if len(parts) > 5 and parts[5] != '*' else '*'
                                        affected_packages.append({
                                            'vendor': vendor,
                                            'product': product,
                                            'version': version
                                        })
                    
                    references = cve_data.get('references', [])
                    exploit_available = any('Exploit' in ref.get('tags', []) for ref in references)
                    
                    vulnerability = {
                        'cveId': cve_id,
                        'description': description[:1000],
                        'cvssScore': cvss_score,
                        'severity': severity,
                        'affectedPackages': affected_packages[:50],
                        'exploitAvailable': exploit_available,
                        'publishedDate': cve_data.get('published'),
                        'lastModifiedDate': cve_data.get('lastModified'),
                        'references': [ref.get('url') for ref in references][:10],
                        'metadata': {'source': 'NVD', 'year': year, 'month': month}
                    }
                    
                    vulnerabilities.append(vulnerability)
                except:
                    continue
            
            start_index += results_per_page
            if start_index >= total_results:
                break
            
            time.sleep(7)  # Rate limiting
        except Exception as e:
            print(f"✗ Error: {e}")
            break
    
    print(f"✓ {len(vulnerabilities)} CVEs")
    return vulnerabilities

def update_database(db, vulnerabilities):
    collection = db.vulnerabilities
    
    collection.create_index([('cveId', ASCENDING)], unique=True)
    collection.create_index([('severity', ASCENDING)])
    collection.create_index([('affectedPackages.product', ASCENDING)])
    
    inserted = 0
    updated = 0
    
    for vuln in vulnerabilities:
        try:
            result = collection.update_one(
                {'cveId': vuln['cveId']},
                {'$set': vuln},
                upsert=True
            )
            if result.upserted_id:
                inserted += 1
            else:
                updated += 1
        except:
            pass
    
    return inserted, updated

def main():
    print("=" * 60)
    print("NVD Full Database Updater")
    print("=" * 60)
    
    db = connect_to_mongodb()
    
    # Fetch last 2 years month by month (2023-2024)
    total_vulns = []
    
    for year in [2023, 2024]:
        print(f"\nFetching year {year}:")
        for month in range(1, 13):
            vulns = fetch_cves_by_month(year, month)
            total_vulns.extend(vulns)
            
            # Update database every 3 months to save progress
            if month % 3 == 0:
                print(f"  Saving progress... ", end='', flush=True)
                inserted, updated = update_database(db, total_vulns)
                print(f"✓ {inserted} new, {updated} updated")
                total_vulns = []
    
    # Final update
    if total_vulns:
        print("\nFinal save... ", end='', flush=True)
        inserted, updated = update_database(db, total_vulns)
        print(f"✓ {inserted} new, {updated} updated")
    
    # Stats
    collection = db.vulnerabilities
    stats = {
        'total': collection.count_documents({}),
        'critical': collection.count_documents({'severity': 'CRITICAL'}),
        'high': collection.count_documents({'severity': 'HIGH'}),
        'medium': collection.count_documents({'severity': 'MEDIUM'}),
        'low': collection.count_documents({'severity': 'LOW'})
    }
    
    print("\n" + "=" * 60)
    print("Database Statistics:")
    print(f"  Total CVEs: {stats['total']}")
    print(f"  Critical: {stats['critical']}")
    print(f"  High: {stats['high']}")
    print(f"  Medium: {stats['medium']}")
    print(f"  Low: {stats['low']}")
    print("=" * 60)

if __name__ == '__main__':
    main()
