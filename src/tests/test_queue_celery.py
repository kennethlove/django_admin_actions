from unittest import mock

import pytest
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME

from admin_actions.actions.queue_celery import QueueCeleryAction
from tests._app.models import AdminActionsTestModel


@pytest.fixture(scope="session")
def celery_enable_logging():
    return True


@pytest.fixture(scope="session")
def celery_config():
    return {
        "broker_url": "memory://",
        "result_backend": "rpc://",
        "task_always_eager": True,
    }


@pytest.fixture
def celery_task(celery_session_app):
    @celery_session_app.task
    def sample_task(_):  # Must take a single argument
        ...

    return sample_task


@pytest.fixture
def mock_task(celery_task):
    with mock.patch.object(celery_task, "delay", wraps=celery_task.delay) as mock_delay:
        yield mock_delay


@pytest.mark.django_db
def test_task_is_delayed_appropriately(
    admin,
    model_instance,
    celery_task,
    mock_task,
    _request,
):
    """Using the action in the Admin should delay the provided task."""
    instance = model_instance()
    model_instance()
    r = _request("post", data={ACTION_CHECKBOX_NAME: [instance.pk]})

    def _filter(obj: AdminActionsTestModel) -> bool:
        return obj.pk == instance.pk

    queue_action = QueueCeleryAction(celery_task, condition=_filter)
    queue_action(admin, r, AdminActionsTestModel.objects.all())

    mock_task.assert_called_once_with(instance.pk)


def test_non_celery_task_raises():
    """Providing a non-celery task should raise an error."""

    def not_a_celery_task(_):
        return 0

    with pytest.raises(TypeError):
        QueueCeleryAction(task=not_a_celery_task)  # pyright: ignore[reportArgumentType]


@mock.patch("admin_actions.actions.find_spec", return_value=None)
def test_celery_not_available_raises(_mock_find_spec):
    """Celery not being installed should raise an ImportError."""

    with pytest.raises(ImportError):
        from admin_actions.actions import QueueCeleryAction  # noqa: F401
