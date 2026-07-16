"""
Celery Application Configuration
Distributed task queue for scalable database operations.
"""
from celery import Celery
import os
from kombu import Exchange, Queue

# Load environment
from dotenv import load_dotenv
load_dotenv()

# Create Celery app
app = Celery('m-dn_dba')

# Redis configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = os.getenv('REDIS_PORT', '7379')
REDIS_DB = os.getenv('REDIS_DB', '0')
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', 'pippopippo_1234')

BROKER_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
RESULT_BACKEND = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{int(REDIS_DB)+1}"

# Celery configuration
app.conf.update(
    # Broker settings
    broker_url=BROKER_URL,
    result_backend=RESULT_BACKEND,
    
    # Serialization
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    
    # Timezone
    timezone='Europe/Rome',
    enable_utc=True,
    
    # Performance
    worker_prefetch_multiplier=4,  # Tasks per worker
    task_acks_late=True,  # Ack after completion
    task_reject_on_worker_lost=True,
    
    # Retries
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,
    
    # Results
    result_expires=3600,  # 1 hour
    
    # Task routes
    task_routes={
        'orchestrator.tasks.collect_metrics': {'queue': 'metrics'},
        'orchestrator.tasks.validate_alert': {'queue': 'alerts'},
        'orchestrator.tasks.discover_databases': {'queue': 'discovery'},
    },
    
    # Queues
    task_queues=(
        Queue('default', Exchange('default'), routing_key='default'),
        Queue('metrics', Exchange('metrics'), routing_key='metrics'),
        Queue('alerts', Exchange('alerts'), routing_key='alerts', priority=10),
        Queue('discovery', Exchange('discovery'), routing_key='discovery'),
    ),
)

# Auto-discover tasks
app.autodiscover_tasks(['orchestrator.tasks'])

if __name__ == '__main__':
    app.start()
