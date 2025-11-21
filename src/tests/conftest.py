from unittest import mock

import pytest
from django.contrib.admin import AdminSite

from ._app.admin import AdminActionsTestModelAdmin
from ._app.models import AdminActionsTestModel


@pytest.fixture
def mock_function():
    def _empty_function(*args, **kwargs):
        """A no-op function for testing purposes."""
        pass

    with mock.patch.object(
        _empty_function,
        "__call__",
        wraps=_empty_function.__call__,
        __name__="empty_function",
    ) as mock_fn:
        yield mock_fn


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
