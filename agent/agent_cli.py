#!/usr/bin/env python3
"""
DockGuardian Agent CLI Interface
Standalone terminal-based interface for managing the scanning agent
"""
import curses
import subprocess
import os
import time
import docker
from datetime import datetime
from dotenv import load_dotenv
import psutil

load_dotenv()

class AgentCLI:
    def __init__(self):
        self.backend_url = os.getenv('BACKEND_URL', 'http://localhost:5000')
        self.agent_id = os.getenv('AGENT_ID', 'unknown')
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Docker client
        try:
            self.docker_client = docker.from_env()
        except Exception as e:
            self.docker_client = None
            
        self.logs = []
        self.max_logs = 50
        self.selected_menu = 0
        self.menu_items = [
            "Start Task Poller",
            "Stop Task Poller",
            "Run Full Scan",
            "Refresh Status",
            "View Logs",
            "Exit"
        ]
        
    def log(self, message):
        """Add log message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.logs.append(f"[{timestamp}] {message}")
        if len(self.logs) > self.max_logs:
            self.logs.pop(0)
    
    def is_poller_running(self):
        """Check if task poller is running"""
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if 'task_poller.py' in cmdline and 'python' in cmdline.lower():
                    return True, proc.info['pid']
            except:
                continue
        return False, None
    
    def get_containers(self):
        """Get list of containers"""
        if not self.docker_client:
            return []
        
        try:
            containers = self.docker_client.containers.list(all=True)
            return [{
                'id': c.id[:12],
                'name': c.name,
                'image': c.image.tags[0] if c.image.tags else c.image.id[:12],
                'status': c.status
            } for c in containers]
        except Exception as e:
            self.log(f"Error getting containers: {e}")
            return []
    
    def start_poller(self):
        """Start task poller"""
        is_running, _ = self.is_poller_running()
        
        if is_running:
            self.log("⚠️  Task poller is already running")
            return
        
        try:
            subprocess.Popen(
                ['nohup', 'python3', 'task_poller.py'],
                cwd=self.script_dir,
                stdout=open('task_poller.log', 'a'),
                stderr=subprocess.STDOUT,
                start_new_session=True
            )
            time.sleep(2)
            self.log("✓ Task poller started")
        except Exception as e:
            self.log(f"✗ Error starting poller: {e}")
    
    def stop_poller(self):
        """Stop task poller"""
        try:
            subprocess.run(['pkill', '-f', 'task_poller.py'], check=False)
            time.sleep(1)
            self.log("✓ Task poller stopped")
        except Exception as e:
            self.log(f"✗ Error stopping poller: {e}")
    
    def run_scan(self):
        """Run full scan"""
        self.log("Starting full scan...")
        try:
            result = subprocess.run(
                ['python3', 'scanner.py', '--once'],
                cwd=self.script_dir,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                self.log("✓ Scan completed successfully")
                # Count scanned containers
                for line in result.stdout.split('\n'):
                    if 'containers scanned' in line.lower():
                        self.log(f"  {line.strip()}")
            else:
                self.log(f"✗ Scan failed")
        except subprocess.TimeoutExpired:
            self.log("✗ Scan timeout (>5 minutes)")
        except Exception as e:
            self.log(f"✗ Scan error: {e}")
    
    def draw_header(self, stdscr):
        """Draw header section"""
        height, width = stdscr.getmaxyx()
        
        # Title
        title = "═══ DockGuardian Agent Interface ═══"
        stdscr.addstr(0, (width - len(title)) // 2, title, curses.A_BOLD | curses.color_pair(1))
        
        # Agent info
        stdscr.addstr(2, 2, f"Agent ID: {self.agent_id}", curses.A_DIM)
        stdscr.addstr(3, 2, f"Backend:  {self.backend_url}", curses.A_DIM)
        
        # Status
        is_running, pid = self.is_poller_running()
        status_text = f"Poller Status: "
        stdscr.addstr(4, 2, status_text)
        
        if is_running:
            stdscr.addstr(4, 2 + len(status_text), f"RUNNING ✓ (PID: {pid})", 
                         curses.color_pair(2) | curses.A_BOLD)
        else:
            stdscr.addstr(4, 2 + len(status_text), "STOPPED", 
                         curses.color_pair(3) | curses.A_BOLD)
        
        # Draw separator
        stdscr.addstr(5, 0, "─" * width, curses.A_DIM)
    
    def draw_menu(self, stdscr, start_y):
        """Draw menu section"""
        stdscr.addstr(start_y, 2, "MENU (↑/↓ to navigate, ENTER to select):", curses.A_BOLD)
        
        for idx, item in enumerate(self.menu_items):
            y = start_y + 2 + idx
            if idx == self.selected_menu:
                stdscr.addstr(y, 4, f"► {item}", curses.A_REVERSE | curses.A_BOLD)
            else:
                stdscr.addstr(y, 4, f"  {item}")
    
    def draw_containers(self, stdscr, start_y):
        """Draw containers section"""
        height, width = stdscr.getmaxyx()
        containers = self.get_containers()
        
        stdscr.addstr(start_y, 2, f"RUNNING CONTAINERS ({len(containers)}):", curses.A_BOLD)
        
        if not containers:
            stdscr.addstr(start_y + 2, 4, "No containers found", curses.A_DIM)
            return start_y + 3
        
        # Table header
        header_y = start_y + 2
        stdscr.addstr(header_y, 4, "ID", curses.A_BOLD)
        stdscr.addstr(header_y, 18, "NAME", curses.A_BOLD)
        stdscr.addstr(header_y, 38, "IMAGE", curses.A_BOLD)
        stdscr.addstr(header_y, 65, "STATUS", curses.A_BOLD)
        
        # Table rows
        for idx, container in enumerate(containers[:8]):  # Show max 8
            y = header_y + 1 + idx
            if y >= height - 10:  # Leave space for logs
                break
                
            stdscr.addstr(y, 4, container['id'][:12])
            stdscr.addstr(y, 18, container['name'][:18])
            stdscr.addstr(y, 38, container['image'][:25])
            
            status = container['status']
            color = curses.color_pair(2) if status == 'running' else curses.color_pair(3)
            stdscr.addstr(y, 65, status, color)
        
        return header_y + len(containers[:8]) + 2
    
    def draw_logs(self, stdscr, start_y):
        """Draw logs section"""
        height, width = stdscr.getmaxyx()
        
        stdscr.addstr(start_y, 2, "RECENT LOGS:", curses.A_BOLD)
        
        # Show last logs that fit
        available_lines = height - start_y - 3
        recent_logs = self.logs[-available_lines:] if len(self.logs) > available_lines else self.logs
        
        for idx, log in enumerate(recent_logs):
            y = start_y + 2 + idx
            if y >= height - 1:
                break
            log_text = log[:width - 4] if len(log) > width - 4 else log
            stdscr.addstr(y, 4, log_text, curses.A_DIM)
    
    def draw_footer(self, stdscr):
        """Draw footer"""
        height, width = stdscr.getmaxyx()
        footer = "Press 'q' to quit | 'r' to refresh | Updated: " + datetime.now().strftime("%H:%M:%S")
        stdscr.addstr(height - 1, 0, footer[:width-1], curses.A_REVERSE)
    
    def handle_menu_action(self):
        """Handle selected menu action"""
        action = self.menu_items[self.selected_menu]
        
        if action == "Start Task Poller":
            self.start_poller()
        elif action == "Stop Task Poller":
            self.stop_poller()
        elif action == "Run Full Scan":
            self.run_scan()
        elif action == "Refresh Status":
            self.log("Refreshing status...")
        elif action == "View Logs":
            self.log("Showing logs...")
        elif action == "Exit":
            return False
        
        return True
    
    def run(self, stdscr):
        """Main run loop"""
        # Setup colors
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)
        
        # Setup screen
        curses.curs_set(0)  # Hide cursor
        stdscr.timeout(1000)  # Refresh every second
        
        self.log("Agent CLI started")
        
        running = True
        while running:
            stdscr.clear()
            height, width = stdscr.getmaxyx()
            
            # Draw sections
            self.draw_header(stdscr)
            
            menu_y = 7
            self.draw_menu(stdscr, menu_y)
            
            containers_y = menu_y + len(self.menu_items) + 4
            logs_y = self.draw_containers(stdscr, containers_y)
            
            self.draw_logs(stdscr, logs_y + 1)
            self.draw_footer(stdscr)
            
            stdscr.refresh()
            
            # Handle input
            key = stdscr.getch()
            
            if key == ord('q') or key == ord('Q'):
                running = False
            elif key == ord('r') or key == ord('R'):
                self.log("Refreshing...")
            elif key == curses.KEY_UP:
                self.selected_menu = (self.selected_menu - 1) % len(self.menu_items)
            elif key == curses.KEY_DOWN:
                self.selected_menu = (self.selected_menu + 1) % len(self.menu_items)
            elif key == ord('\n') or key == curses.KEY_ENTER or key == 10:
                running = self.handle_menu_action()

def main():
    app = AgentCLI()
    curses.wrapper(app.run)

if __name__ == '__main__':
    main()
