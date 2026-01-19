#!/usr/bin/env python3
"""Fix agent registration with correct values"""
from pymongo import MongoClient
import socket
import os
from dotenv import load_dotenv

load_dotenv()

# Get correct values
hostname = socket.gethostname()
agent_id = os.getenv('AGENT_ID', f'agent-{hostname}')
api_key = os.getenv('API_KEY')

# Get local IP
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip_address = s.getsockname()[0]
    s.close()
except:
    ip_address = "192.168.5.128"  # Default from your system

print(f"Agent ID: {agent_id}")
print(f"IP Address: {ip_address}")
print(f"API Key: {api_key[:20]}...")

# Update MongoDB
client = MongoClient('mmongodb+srv://user:pass@cluster.mongodb.net/dockguardian')
db = client['dockguardian']

# Delete old agent with wrong ID
db.agents.delete_many({'agentId': {'$regex': '^\$'}})

# Upsert correct agent
db.agents.update_one(
    {'agentId': agent_id},
    {'$set': {
        'agentId': agent_id,
        'hostname': hostname,
        'ipAddress': ip_address,
        'apiKey': api_key,
        'status': 'active',
        'lastHeartbeat': None,
        'metadata': {
            'osType': 'Linux',
            'agentVersion': '1.0.0'
        }
    }},
    upsert=True
)

print("\n✅ Agent registered successfully!")
print(f"Backend will connect to: http://{ip_address}:5000")
