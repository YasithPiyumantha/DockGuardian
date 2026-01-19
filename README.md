# Dock-Guardian - Docker Security Scanner

This repository contains **dataset files** and **Jupyter notebooks** for the Dock-Guardian project.  
It is intended for exploring, analyzing, and experimenting with Docker container vulnerabilities and security assessments.

---

## Additional Contents

- `datasets/` – Folder containing dataset files used for analysis.  
- `notebooks/` – Jupyter notebooks demonstrating data analysis, experiments, and insights.  


## 🌟 Features

- 🔍 **Vulnerability Scanning**: Automated CVE detection using Syft
- 🛡️ **CIS Benchmark Compliance**: Docker CIS benchmark automated checking  
- 🔧 **Auto-Healer**: Automatic remediation of security issues with rollback support
- 📊 **Security Dashboard**: Real-time threat monitoring and analytics
- 🤖 **Agent-Based Architecture**: Distributed scanning with task polling
- 📱 **Web Interface**: Modern React-based frontend with Material-UI
- 💻 **CLI Agent Interface**: Standalone terminal-based agent management
- ⚡ **Task-Based Polling**: Efficient agent communication without direct connectivity
- 📦 **Backup & Restore**: Automatic container backups before remediation

## 🏗️ Architecture
```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   Frontend  │ ◄─────► │   Backend   │ ◄─────► │   MongoDB   │
│  (React.js) │         │  (Node.js)  │         │  (Database) │
└─────────────┘         └─────────────┘         └─────────────┘
                               ▲
                               │ (Task Polling)
                               ▼
                        ┌─────────────┐
                        │    Agent    │
                        │  (Python)   │
                        │   Scanner   │
                        └─────────────┘
                               │
                               ▼
                        ┌─────────────┐
                        │   Docker    │
                        │ Containers  │
                        └─────────────┘
```

- **Frontend**: React.js with Material-UI
- **Backend**: Node.js with Express
- **Agent**: Python-based scanning engine
- **Database**: MongoDB Atlas
- **Deployment**: Google Cloud Run

## 📁 Project Structure
```
DockGuardian/
├── agent/              # Python scanning agent
│   ├── scanner.py      # Container vulnerability scanner
│   ├── healer.py       # Auto-remediation engine
│   ├── task_poller.py  # Task polling service
│   ├── agent_cli.py    # CLI management interface
│   ├── cis_checks.py   # CIS benchmark checker
│   └── backups/        # Container backups
├── backend/            # Node.js API server
│   ├── controllers/    # API controllers
│   ├── models/         # MongoDB models
│   ├── routes/         # API routes
│   └── middleware/     # Authentication & validation
├── frontend/           # React web interface
│   ├── src/
│   │   ├── components/ # React components
│   │   ├── pages/      # Page components
│   │   └── services/   # API services
│   └── public/         # Static assets
└── database/           # Database utilities
    ├── nvd_updater.py  # NVD vulnerability updater
    └── comprehensive_seed.py  # Database seeding
```

## 🚀 Installation

### Prerequisites
- Docker & Docker Compose
- Node.js 16+
- Python 3.8+
- MongoDB (local or Atlas)
- Syft (for vulnerability scanning)

### 1. Install Syft
```bash
curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin
```

### 2. Clone Repository
```bash
git clone https://github.com/YOUR_USERNAME/DockGuardian.git
cd DockGuardian
```

### 3. Backend Setup
```bash
cd backend
npm install
cp .env.example .env
# Edit .env with your MongoDB URI and secrets
npm start
```

### 4. Frontend Setup
```bash
cd frontend
npm install
cp .env.example .env
# Edit .env with your backend URL
npm start
```

### 5. Agent Setup
```bash
cd agent
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt --break-system-packages
cp .env.example .env
# Edit .env with backend URL and API key

# Start task poller
python3 task_poller.py &
```

## 💻 Agent CLI Interface

DockGuardian includes a standalone terminal-based interface for managing the agent:

### Launch CLI Interface
```bash
cd agent
source venv/bin/activate
python3 agent_cli.py
```

### Features
- ✅ Real-time agent status monitoring
- ✅ Start/Stop task poller with one click
- ✅ Trigger full container scans
- ✅ View running containers
- ✅ Live log streaming
- ✅ Color-coded status indicators
- ✅ Keyboard-driven navigation

### Keyboard Controls
- `↑/↓` - Navigate menu
- `ENTER` - Select action
- `r` - Refresh status
- `q` - Quit

![CLI Interface Screenshot]

## 📖 Usage

### Running Scans

**Full Scan (All Containers)**
```bash
cd agent
source venv/bin/activate
python3 scanner.py --once
```

**Scan Specific Container**
```bash
python3 scanner.py --container <container_id>
```

### Auto-Healing

The auto-healer automatically fixes security issues:

1. Navigate to the **Auto-Healer** tab in the web interface
2. Select a container with failed CIS checks
3. Choose the issue to fix (e.g., "Running as root")
4. Click **Fix Container**
5. Agent creates a backup and applies the fix
6. View backup history and rollback if needed

**Supported Fixes:**
- ✅ Running as root (CIS-4.1)
- ✅ Privileged mode (CIS-5.4)
- ✅ Read-only filesystem (CIS-5.12)

### Task Poller

The task poller enables the agent to work behind firewalls:
```bash
cd agent
source venv/bin/activate
python3 task_poller.py
```

It polls the backend every 5 seconds for:
- Pending scan tasks
- Healing tasks
- Rollback requests

### Accessing the Dashboard

**Local Development**
```
http://localhost:3000
```

**Production**
```
https://your-frontend-url.run.app
```

## ⚙️ Configuration

### Environment Variables

**Backend (`backend/.env`)**
```env
PORT=5000
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/dockguardian
JWT_SECRET=your-super-secret-jwt-key
NODE_ENV=production
AGENT_API_KEY=your-agent-api-key
```

**Frontend (`frontend/.env`)**
```env
REACT_APP_API_URL=https://your-backend-url.run.app
```

**Agent (`agent/.env`)**
```env
BACKEND_URL=https://your-backend-url.run.app
API_KEY=your-agent-api-key
AGENT_ID=agent-hostname-timestamp
SCAN_INTERVAL=3600
AGENT_PORT=5000
```

**Database (`database/.env`)**
```env
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/dockguardian
```

## 🌐 Deployment

### Google Cloud Run Deployment

**Backend**
```bash
cd backend
gcloud run deploy dockguardian-backend --source .
```

**Frontend**
```bash
cd frontend
npm run build
gcloud run deploy dockguardian-frontend --source .
```

**Agent** runs on your local infrastructure and polls the cloud backend.

## 🔒 Security Features

- ✅ Container vulnerability detection (CVE scanning via Syft)
- ✅ CIS Docker Benchmark compliance checking
- ✅ Automated security remediation with backups
- ✅ Real-time threat scoring algorithm
- ✅ Task-based polling architecture (agent-initiated)
- ✅ Secure agent authentication with API keys
- ✅ JWT-based user authentication
- ✅ Rollback capability for all healing operations

## 🎯 Workflow

1. **Scan**: Agent scans Docker containers using Syft
2. **Analyze**: Backend calculates threat scores and identifies issues
3. **Visualize**: Dashboard displays security status
4. **Remediate**: Auto-healer fixes CIS benchmark violations
5. **Verify**: Re-scan to confirm fixes applied successfully

## 🛠️ Development

### Running Tests
```bash
# Backend tests
cd backend
npm test

# Frontend tests
cd frontend
npm test

# Agent tests
cd agent
pytest
```

### Adding New CIS Checks

Edit `agent/cis_checks.py` and add your check to the `CISChecker` class.

### Adding New Healing Rules

Edit `agent/healer.py` and implement the remediation logic.

## 📊 Dashboard Features

- **Security Overview**: Total containers, critical risks, threat scores
- **Recent Scans**: Latest scan results with threat levels
- **Vulnerabilities**: CVE database with severity ratings
- **CIS Benchmarks**: Compliance status for each container
- **Auto-Healer**: One-click remediation with backup/rollback
- **Scan Trigger**: Manually trigger scans for selected containers

## 🐛 Troubleshooting

### Agent Can't Connect to Backend
- Verify `BACKEND_URL` in `agent/.env`
- Check API key matches backend configuration
- Ensure backend is deployed and accessible

### Scans Not Appearing in Dashboard
- Check agent logs: `tail -f agent/task_poller.log`
- Verify MongoDB connection
- Clear old scans and run fresh scan

### Auto-Healer Not Working
- Ensure task poller is running: `ps aux | grep task_poller`
- Check agent has Docker permissions
- Review healing logs in task_poller.log

## 📝 License

MIT License - see LICENSE file for details

## 👥 Contributors

- Yasith Piyumantha - Initial development

## 🙏 Acknowledgments

- Syft by Anchore for vulnerability scanning
- CIS Docker Benchmark for security standards
- Material-UI for frontend components
