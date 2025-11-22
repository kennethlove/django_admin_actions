from importlib.util import find_spec

from .broadcast_pubsub import BroadcastPubSubAction

__all__ = [
    "BroadcastPubSubAction",
]

# Guard import for Celery integration
if find_spec("celery") is not None:
    from .queue_celery import QueueCeleryAction

    __all__ += ["QueueCeleryAction"]
else:
    raise ImportError(
        "Celery integration requires celery to be installed. "
        "Install it with: pip install admin-actions[celery]"
    )
