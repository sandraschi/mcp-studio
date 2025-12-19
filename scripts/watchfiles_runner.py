#!/usr/bin/env python3
"""
MCP Studio Watchfiles Crashproof Runner

This script provides crashproofing for MCP Studio using watchfiles.
It automatically detects crashes and restarts the application with exponential backoff.

Usage:
    python watchfiles_runner.py

Environment Variables:
    MCP_STUDIO_HOST: Host to bind to (default: 0.0.0.0)
    MCP_STUDIO_PORT: Port to bind to (default: 7787)
    MCP_STUDIO_DEBUG: Enable debug mode (default: True)
    MCP_STUDIO_WORKERS: Number of workers (default: 1)
    MCP_STUDIO_LOG_LEVEL: Log level (default: INFO)
    WATCHFILES_MAX_RESTARTS: Max restart attempts (default: 10)
    WATCHFILES_RESTART_DELAY: Base restart delay in seconds (default: 1.0)
    WATCHFILES_BACKOFF_MULTIPLIER: Exponential backoff multiplier (default: 1.5)
    WATCHFILES_HEALTH_CHECK_INTERVAL: Health check interval in seconds (default: 30)
    WATCHFILES_NOTIFY_ON_CRASH: Enable crash notifications (default: True)

Author: Sandra Schipal
Created: 2025-12-17
"""

import asyncio
import aiohttp
import json
import logging
import os
import signal
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/mcp-studio-watchfiles.log', mode='a')
    ]
)
logger = logging.getLogger('mcp-studio-watchfiles')

class CrashproofRunner:
    """Crashproof runner for MCP Studio using watchfiles monitoring."""

    def __init__(
        self,
        command: List[str],
        cwd: str = None,
        max_restarts: int = 10,
        restart_delay: float = 1.0,
        backoff_multiplier: float = 1.5,
        health_check_url: str = None,
        health_check_interval: int = 30,
        notify_on_crash: bool = True
    ):
        self.command = command
        self.cwd = cwd or os.getcwd()
        self.max_restarts = max_restarts
        self.restart_delay = restart_delay
        self.backoff_multiplier = backoff_multiplier
        self.health_check_url = health_check_url
        self.health_check_interval = health_check_interval
        self.notify_on_crash = notify_on_crash

        self.process = None
        self.restart_count = 0
        self.start_time = datetime.now()
        self.last_health_check = 0
        self.uptime_total = 0
        self.crash_log = []

    async def start_process(self) -> bool:
        """Start the MCP Studio process."""
        try:
            # Set environment variables for MCP Studio
            env = os.environ.copy()
            env.update({
                'PYTHONPATH': str(Path(self.cwd) / 'src'),
                'MCP_STUDIO_DEBUG': 'true',
                'MCP_STUDIO_LOG_LEVEL': 'INFO'
            })

            self.process = await asyncio.create_subprocess_exec(
                *self.command,
                cwd=self.cwd,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                preexec_fn=None if os.name == 'nt' else os.setsid
            )

            logger.info(f"✓ Started MCP Studio process: {' '.join(self.command)} (PID: {self.process.pid})")
            return True

        except Exception as e:
            logger.error(f"✗ Failed to start MCP Studio process: {e}")
            return False

    async def check_health(self) -> bool:
        """Check MCP Studio health via HTTP endpoint."""
        if not self.health_check_url:
            return True  # Assume healthy if no health check configured

        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(self.health_check_url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get('status') == 'healthy'
                    return False
        except Exception as e:
            logger.debug(f"Health check failed: {e}")
            return False

    async def monitor_process(self):
        """Monitor process health and restart on crash."""
        while True:
            current_time = time.time()

            try:
                # Periodic health check
                if current_time - self.last_health_check > self.health_check_interval:
                    if not await self.check_health():
                        logger.warning("⚠️  Health check failed - initiating restart")
                        await self.restart_process()
                    self.last_health_check = current_time

                # Check if process is still running
                if self.process:
                    if self.process.returncode is not None:
                        # Process has exited
                        crash_time = datetime.now()
                        self.uptime_total += (crash_time - self.start_time).total_seconds()

                        # Log crash details
                        crash_info = {
                            'timestamp': crash_time.isoformat(),
                            'exit_code': self.process.returncode,
                            'uptime_before_crash': self.uptime_total,
                            'restart_attempt': self.restart_count + 1,
                            'pid': self.process.pid
                        }
                        self.crash_log.append(crash_info)

                        # Read stderr for error details
                        if self.process.stderr:
                            try:
                                stderr_data = await self.process.stderr.read()
                                if stderr_data:
                                    crash_info['stderr'] = stderr_data.decode('utf-8', errors='ignore').strip()
                            except:
                                pass

                        logger.warning(f"⚠️  MCP Studio crashed with exit code {self.process.returncode}")
                        logger.info(f"📊 Uptime before crash: {self.uptime_total:.1f}s")
                        logger.info(f"🔄 Restart attempt {self.restart_count + 1}/{self.max_restarts}")

                        if self.notify_on_crash:
                            await self.notify_crash(crash_info)

                        await self.restart_process()
                    else:
                        # Process is healthy, update uptime
                        self.uptime_total = (datetime.now() - self.start_time).total_seconds()
                else:
                    # No process running, start one
                    await self.start_process()

            except Exception as e:
                logger.error(f"Error in process monitoring: {e}")

            await asyncio.sleep(1)

    async def restart_process(self):
        """Restart crashed process with exponential backoff."""
        if self.restart_count >= self.max_restarts:
            logger.error(f"✗ Maximum restarts ({self.max_restarts}) exceeded. Giving up.")
            logger.error("💡 Consider checking application logs and fixing underlying issues")
            await self.save_crash_report()
            return

        self.restart_count += 1
        delay = self.restart_delay * (self.backoff_multiplier ** (self.restart_count - 1))

        logger.info(f"🔄 Restarting MCP Studio in {delay:.1f}s... (attempt {self.restart_count}/{self.max_restarts})")

        # Clean up old process
        if self.process:
            try:
                if os.name == 'nt':
                    self.process.terminate()
                else:
                    os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                await asyncio.wait_for(self.process.wait(), timeout=5.0)
                logger.debug(f"Cleaned up old process (PID: {self.process.pid})")
            except Exception as e:
                logger.warning(f"Error cleaning up old process: {e}")
                try:
                    self.process.kill()
                except:
                    pass

        await asyncio.sleep(delay)

        # Reset start time for new process
        self.start_time = datetime.now()

        # Start new process
        if not await self.start_process():
            logger.error("Failed to restart MCP Studio - will retry on next monitoring cycle")

    async def notify_crash(self, crash_info: Dict[str, Any]):
        """Send crash notification (extend this for email/SMS/etc)."""
        try:
            # For now, just log the crash details
            logger.error("🚨 MCP STUDIO CRASH DETECTED")
            logger.error(f"   Exit Code: {crash_info['exit_code']}")
            logger.error(f"   Uptime: {crash_info['uptime_before_crash']:.1f}s")
            logger.error(f"   PID: {crash_info['pid']}")
            logger.error(f"   Timestamp: {crash_info['timestamp']}")

            if 'stderr' in crash_info and crash_info['stderr']:
                logger.error(f"   Error Output: {crash_info['stderr'][:200]}...")

            # TODO: Add email/SMS notifications here
            # await self.send_notification_email(crash_info)
            # await self.send_sms_alert(crash_info)

        except Exception as e:
            logger.error(f"Error sending crash notification: {e}")

    async def save_crash_report(self):
        """Save detailed crash report to file."""
        try:
            report_path = Path('logs') / f"mcp-studio-crash-report-{int(time.time())}.json"

            report = {
                'generated_at': datetime.now().isoformat(),
                'total_crashes': len(self.crash_log),
                'total_restarts': self.restart_count,
                'total_uptime': self.uptime_total,
                'max_restarts_allowed': self.max_restarts,
                'crash_events': self.crash_log[-10:],  # Last 10 crashes
                'system_info': {
                    'platform': sys.platform,
                    'python_version': sys.version,
                    'cwd': self.cwd,
                    'command': self.command
                }
            }

            report_path.parent.mkdir(exist_ok=True)
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)

            logger.info(f"💾 Crash report saved to: {report_path}")

        except Exception as e:
            logger.error(f"Error saving crash report: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get current runner statistics."""
        return {
            'process_running': self.process is not None and self.process.returncode is None,
            'process_pid': self.process.pid if self.process else None,
            'restart_count': self.restart_count,
            'max_restarts': self.max_restarts,
            'total_uptime': self.uptime_total,
            'crash_count': len(self.crash_log),
            'start_time': self.start_time.isoformat(),
            'command': self.command
        }

    async def run(self):
        """Main runner loop."""
        logger.info("🚀 Starting MCP Studio Crashproof Runner")
        logger.info(f"📍 Working directory: {self.cwd}")
        logger.info(f"⚙️  Command: {' '.join(self.command)}")
        logger.info(f"🔄 Max restarts: {self.max_restarts}")
        logger.info(f"🏥 Health check: {self.health_check_url or 'Disabled'}")

        # Set up signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            logger.info(f"🛑 Received signal {signum} - shutting down...")
            if self.process:
                try:
                    if os.name == 'nt':
                        self.process.terminate()
                    else:
                        os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                except Exception as e:
                    logger.error(f"Error terminating process: {e}")

            # Save final crash report
            asyncio.create_task(self.save_crash_report())
            sys.exit(0)

        # Register signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        try:
            # Start initial process
            if not await self.start_process():
                logger.error("Failed to start initial MCP Studio process")
                return

            # Monitor and restart loop
            await self.monitor_process()

        except KeyboardInterrupt:
            logger.info("🛑 Shutting down gracefully...")
        except Exception as e:
            logger.error(f"Fatal error in runner: {e}")
        finally:
            # Save final crash report
            await self.save_crash_report()
            logger.info("👋 MCP Studio Crashproof Runner stopped")


def load_config() -> Dict[str, Any]:
    """Load configuration from environment variables."""
    return {
        'host': os.getenv('MCP_STUDIO_HOST', '0.0.0.0'),
        'port': int(os.getenv('MCP_STUDIO_PORT', '7787')),
        'debug': os.getenv('MCP_STUDIO_DEBUG', 'true').lower() == 'true',
        'workers': int(os.getenv('MCP_STUDIO_WORKERS', '1')),
        'log_level': os.getenv('MCP_STUDIO_LOG_LEVEL', 'INFO'),
        'max_restarts': int(os.getenv('WATCHFILES_MAX_RESTARTS', '10')),
        'restart_delay': float(os.getenv('WATCHFILES_RESTART_DELAY', '1.0')),
        'backoff_multiplier': float(os.getenv('WATCHFILES_BACKOFF_MULTIPLIER', '1.5')),
        'health_check_interval': int(os.getenv('WATCHFILES_HEALTH_CHECK_INTERVAL', '30')),
        'notify_on_crash': os.getenv('WATCHFILES_NOTIFY_ON_CRASH', 'true').lower() == 'true'
    }


async def main():
    """Main entry point."""
    config = load_config()

    # Build uvicorn command for MCP Studio
    command = [
        sys.executable, "-m", "uvicorn",
        "mcp_studio.main:app",
        "--host", config['host'],
        "--port", str(config['port']),
        "--reload" if config['debug'] else "--no-reload",
        "--log-level", config['log_level'].lower(),
        "--workers", str(config['workers'])
    ]

    # Health check URL
    health_url = f"http://{config['host']}:{config['port']}/api/health"

    # Create and run crashproof runner
    runner = CrashproofRunner(
        command=command,
        cwd=Path(__file__).parent,
        max_restarts=config['max_restarts'],
        restart_delay=config['restart_delay'],
        backoff_multiplier=config['backoff_multiplier'],
        health_check_url=health_url,
        health_check_interval=config['health_check_interval'],
        notify_on_crash=config['notify_on_crash']
    )

    await runner.run()


if __name__ == "__main__":
    # Ensure we're in the right directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    # Run the crashproof runner
    asyncio.run(main())
