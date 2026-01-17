"""
Base Worker Class
Standard interface for all background agents/workers.
"""
import logging
import asyncio
from abc import ABC, abstractmethod

class BaseWorker(ABC):
    def __init__(self, name: str, interval: int = 60):
        self.name = name
        self.interval = interval
        self.logger = logging.getLogger(name)
        self.running = False
    
    @abstractmethod
    async def run(self):
        """Main execution loop"""
        pass
    
    async def start(self):
        """Start the worker"""
        self.running = True
        self.logger.info(f"Started {self.name} (Interval: {self.interval}s)")
        await self.run()
    
    async def stop(self):
        """Stop the worker"""
        self.running = False
        self.logger.info(f"Stopped {self.name}")
