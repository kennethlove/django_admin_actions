from calendar import c
from unittest import mock

import pytest
from django.contrib.admin import AdminSite

from ._app.admin import AdminActionsTestModelAdmin
from ._app.models import AdminActionsTestModel


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
def admin_site():
    return AdminSite()


@pytest.fixture
def admin(admin_site):
    return AdminActionsTestModelAdmin(AdminActionsTestModel, admin_site)


@pytest.fixture
def model_instance(db, faker):
    def _create_instance():
        return AdminActionsTestModel.objects.create(name=faker.word())

    return _create_instance


@pytest.fixture
def celery_task(celery_session_app):
    @celery_session_app.task
    def sample_task(_):  # Must take a single argument
        ...

    return sample_task


@pytest.fixture
def mocked_task(celery_task):
    with mock.patch.object(celery_task, "delay", wraps=celery_task.delay) as mock_delay:
        yield mock_delay


@pytest.fixture(name="_request")
def request_with_messages(rf, admin_user):
    """Create a session- and messages-enabled request."""

    def _request(method="get", path="/", data=None):
        match method.lower():
            case "get":
                request = rf.get(path, data=data or {})
            case "post":
                request = rf.post(path, data or {})
            case _:
                raise ValueError(f"Unsupported method: {method}")

        request.user = admin_user
        setattr(request, "session", "session")
        setattr(request, "_messages", mock.MagicMock())

        return request

    return _request
