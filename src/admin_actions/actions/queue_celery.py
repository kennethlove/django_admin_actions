from types import FunctionType
from typing import TypeAlias

import celery

from admin_actions.lib import AdminActionBaseClass, Condition


class QueueCeleryAction(AdminActionBaseClass):
    """Generates an admin action for queuing a Celery task for a chosen set of records.

    Usage:
        conditional_action = QueueCeleryAction(
            task=my_celery_task,
            condition=lambda record: record.should_process(),
        )
        another_action = QueueCeleryAction(...)

        @celery.task
        def my_celery_task(record_id):
            record = MyModel.objects.get(pk=record_id)
            ...

        class MyModelAdmin(admin.ModelAdmin):
            actions = [conditional_action, QueueCeleryAction(...), another_action]
            model = MyModel

    The `task` parameter is required and should be a Celery task callable that
    takes a single model instance's primary key as an argument.

    The `condition` parameter is optional. If provided, it should be a callable
    that takes a model instance and returns a boolean indicating whether to queue
    the task for that record.
    """

    Task: TypeAlias = FunctionType  # Celery task to be called

    def handle_item(self, item):
        """Queues the Celery task for the given item."""
        self.task.delay(item.pk)

    def __init__(
        self, task: Task, *, condition: Condition | None = None, name: str | None = None
    ) -> None:
        """Initializes the action with task and optional condition."""

        if not isinstance(task, (celery.Task,)):
            raise TypeError(f"The task must be a Celery task. Got {type(task)}")

        self.task = task
        super().__init__(function=task, condition=condition, name=name or task.name)
