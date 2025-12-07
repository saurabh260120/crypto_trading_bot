"""
Main worker process for executing trading algorithms.
"""
import asyncio
import logging
import signal
import sys
from typing import Dict, Set
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.config import settings
from app.models.profile import Profile
from app.workers.profile_executor import ProfileExecutor
import redis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WorkerManager:
    """Manages multiple profile executors."""
    
    def __init__(self):
        self.executors: Dict[int, ProfileExecutor] = {}
        self.running = False
        self.redis_client = redis.from_url(settings.REDIS_URL)
        self.lock_timeout = 60  # Lock timeout in seconds
    
    async def start(self):
        """Start the worker manager."""
        self.running = True
        logger.info("Worker manager started")
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Start monitoring loop
        await self._monitor_profiles()
    
    async def _monitor_profiles(self):
        """Monitor profiles and start/stop executors as needed."""
        while self.running:
            try:
                db = SessionLocal()
                try:
                    # Get all enabled profiles
                    profiles = db.query(Profile).filter(
                        Profile.enabled == True,
                        Profile.paused == False
                    ).all()
                    
                    active_profile_ids = {p.id for p in profiles}
                    executor_profile_ids = set(self.executors.keys())
                    
                    # Start new executors
                    for profile in profiles:
                        if profile.id not in executor_profile_ids:
                            # Try to acquire lock
                            lock_key = f"profile_executor:{profile.id}"
                            if self._acquire_lock(lock_key):
                                logger.info(f"Starting executor for profile {profile.id}")
                                executor = ProfileExecutor(profile.id, db)
                                self.executors[profile.id] = executor
                                asyncio.create_task(executor.run())
                    
                    # Stop removed executors
                    for profile_id in executor_profile_ids - active_profile_ids:
                        if profile_id in self.executors:
                            logger.info(f"Stopping executor for profile {profile_id}")
                            await self.executors[profile_id].stop()
                            del self.executors[profile_id]
                            self._release_lock(f"profile_executor:{profile_id}")
                
                finally:
                    db.close()
                
                await asyncio.sleep(5)  # Check every 5 seconds
            
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}", exc_info=True)
                await asyncio.sleep(5)
    
    def _acquire_lock(self, lock_key: str) -> bool:
        """Acquire a distributed lock."""
        try:
            return self.redis_client.set(
                lock_key,
                "locked",
                nx=True,
                ex=self.lock_timeout
            )
        except Exception as e:
            logger.error(f"Failed to acquire lock {lock_key}: {e}")
            return False
    
    def _release_lock(self, lock_key: str):
        """Release a distributed lock."""
        try:
            self.redis_client.delete(lock_key)
        except Exception as e:
            logger.error(f"Failed to release lock {lock_key}: {e}")
    
    async def stop(self):
        """Stop all executors."""
        logger.info("Stopping worker manager...")
        self.running = False
        
        # Stop all executors
        for profile_id, executor in list(self.executors.items()):
            logger.info(f"Stopping executor for profile {profile_id}")
            await executor.stop()
            self._release_lock(f"profile_executor:{profile_id}")
        
        self.executors.clear()
        logger.info("Worker manager stopped")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        asyncio.create_task(self.stop())


async def main():
    """Main entry point for worker."""
    manager = WorkerManager()
    try:
        await manager.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    finally:
        await manager.stop()


if __name__ == "__main__":
    asyncio.run(main())

