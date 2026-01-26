"""
Redis Client - Shared client for Async Messaging and Caching.

Handles connection to Redis and provides wrapper methods for:
- Message Queues (LPUSH/BRPOP)
- Pub/Sub
- Key-Value caching
"""
import os
import redis
import json
import logging
from typing import Optional, Any, Dict, List, Callable
from threading import Thread

# Configure logger
logger = logging.getLogger("RedisClient")


class RedisClient:
    _instance = None
    
    def __init__(self, host: str = None, port: int = None, db: int = 0, password: str = None):
        """
        Initialize Redis connection.
        If host/port not provided, attempts to load from environment.
        """
        self.host = host or os.getenv("REDIS_HOST", "localhost")
        self.port = int(port or os.getenv("REDIS_PORT", 7379))
        self.db = db
        self.password = password or os.getenv("REDIS_PASSWORD", None)
        
        self.client = None
        self.pubsub = None
        self._connect()
        
    def _connect(self):
        """Establish connection to Redis"""
        try:
            self.client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True,  # Automatically decode bytes to strings
                socket_connect_timeout=5
            )
            # Test connection
            self.client.ping()
            logger.info(f"✅ Connected to Redis at {self.host}:{self.port}")
        except redis.ConnectionError as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            self.client = None
    
    @classmethod
    def get_instance(cls):
        """Singleton accessor"""
        if cls._instance is None:
            cls._instance = RedisClient()
        return cls._instance
    
    # =========================================================================
    # Queue Operations (Producer/Consumer)
    # =========================================================================
    
    def push_to_queue(self, queue_name: str, payload: Dict[str, Any]) -> bool:
        """
        Push a dictionary message to the tail of a queue.
        """
        if not self.client:
            logger.warning("Redis client not connected, dropping message")
            return False
        
        try:
            message = json.dumps(payload, default=str)
            self.client.lpush(queue_name, message)
            return True
        except Exception as e:
            logger.error(f"Failed to push to queue {queue_name}: {e}")
            return False

    def pop_from_queue(self, queue_name: str, timeout: int = 0) -> Optional[Dict[str, Any]]:
        """
        Blocking pop from the head of a queue.
        Returns None on timeout (if timeout > 0).
        """
        if not self.client:
            return None
        
        try:
            # brpop returns tuple (queue_name, value)
            result = self.client.brpop(queue_name, timeout=timeout)
            if result:
                _, message = result
                return json.loads(message)
        except Exception as e:
            logger.error(f"Failed to pop from queue {queue_name}: {e}")
        
        return None
    
    # =========================================================================
    # Pub/Sub Operations (Real-time broadcasting)
    # =========================================================================
    
    def publish(self, channel: str, message: Dict[str, Any]) -> int:
        """Publish a message to a channel"""
        if not self.client:
            return 0
        try:
            return self.client.publish(channel, json.dumps(message, default=str))
        except Exception as e:
            logger.error(f"Failed to publish to {channel}: {e}")
            return 0
            
    def subscribe(self, channel: str, callback: Callable[[Dict], None]):
        """
        Subscribe to a channel in a background thread.
        Callback receives the parsed dict message.
        """
        if not self.client:
            return
            
        def _listener():
            pubsub = self.client.pubsub()
            pubsub.subscribe(channel)
            for message in pubsub.listen():
                if message['type'] == 'message':
                    try:
                        data = json.loads(message['data'])
                        callback(data)
                    except Exception as e:
                        logger.error(f"Error processing pubsub message: {e}")
                        
        thread = Thread(target=_listener, daemon=True)
        thread.start()
        logger.info(f"🎧 Subscribed to channel: {channel}")

    # =========================================================================
    # Caching Operations
    # =========================================================================
    
    def set_cache(self, key: str, value: Any, ttl_seconds: int = 300) -> bool:
        """Set a value with TTL"""
        if not self.client:
            return False
        try:
            val_str = json.dumps(value, default=str)
            return self.client.setex(key, ttl_seconds, val_str)
        except Exception as e:
            logger.error(f"Failed to set cache {key}: {e}")
            return False
            
    def get_cache(self, key: str) -> Optional[Any]:
        """Get a value from cache"""
        if not self.client:
            return None
        try:
            val_str = self.client.get(key)
            if val_str:
                return json.loads(val_str)
        except Exception as e:
            logger.error(f"Failed to get cache {key}: {e}")
        return None
