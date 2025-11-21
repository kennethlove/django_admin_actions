import pytest
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME

from admin_actions.lib import AdminActionBaseClass
from tests._app.models import AdminActionsTestModel


class _AdminAction(AdminActionBaseClass):
    """A concrete implementation of AdminActionBaseClass for testing."""

    def handle_item(self, item):
        """Calls the provided function with the item's primary key."""
        self.function(item.pk)


def test_generated_action_is_registrable(admin, rf, admin_user, mock_function):
    """The Admin should have an action that includes `empty_function`."""

    r = rf.get("/")
    r.user = admin_user

    queue_action = _AdminAction(mock_function)
    admin.actions += (queue_action,)

    actions = admin.get_actions(r)
    expected = "empty_function"
    assert expected in actions.keys(), (
        f"Expected action '{expected}' not found in admin actions."
    )
    assert actions[expected][0] is queue_action


def test_generated_action_is_nameable(admin, rf, admin_user):
    """AdminActionBaseClass should accept a custom name."""
    r = rf.get("/")
    r.user = admin_user

    queue_action = _AdminAction(lambda _: ..., name="custom_action_name")
    admin.actions += (queue_action,)

    actions = admin.get_actions(r)
    expected = "custom_action_name"
    assert expected in actions.keys(), (
        f"Expected action '{expected}' not found in admin actions."
    )
    assert actions[expected][0] is queue_action


@pytest.mark.django_db
def test_generated_action_is_callable(
    admin,
    model_instance,
    mock_function,
    _request,
):
    """Using the action in the Admin should call the provided function."""
    instance = model_instance()
    r = _request("post", data={ACTION_CHECKBOX_NAME: [instance.pk]})

    queue_action = _AdminAction(mock_function)
    queue_action(admin, r, AdminActionsTestModel.objects.all())

    mock_function.assert_called_once_with(instance.pk)


@pytest.mark.django_db
def test_condition_failure_excludes_records(
    admin,
    model_instance,
    mock_function,
    _request,
):
    """The condition should exclude all failing records."""
    instance = model_instance()
    r = _request("post", data={ACTION_CHECKBOX_NAME: [instance.pk]})

    queue_action = _AdminAction(mock_function, condition=lambda _: False)
    queue_action(admin, r, AdminActionsTestModel.objects.all())

    # Every record was rejected, task should never be delayed
    mock_function.assert_not_called()


@pytest.mark.django_db
def test_condition_result_determines_record_inclusion(
    admin,
    model_instance,
    mock_function,
    _request,
):
    """The condition should include and exclude appropriately."""
    instance = model_instance()
    r = _request("post", data={ACTION_CHECKBOX_NAME: [instance.pk]})
    model_instance()  # A second instance that should be excluded

    def condition(record):
        return record.pk == instance.pk

    queue_action = _AdminAction(mock_function, condition=condition)
    queue_action(admin, r, AdminActionsTestModel.objects.all())

    # The record met the condition, task should be delayed
    mock_function.assert_called_once_with(instance.pk)


def test_noncallable_condition_raises():
    """Providing a non-callable condition should raise an error."""
    with pytest.raises(TypeError):
        _AdminAction(lambda _: ..., condition="not_a_function")  # pyright: ignore[reportArgumentType]


def test_noncallable_function_raises():
    """Providing a non-callable function should raise an error."""
    with pytest.raises(TypeError):
        _AdminAction("not_a_function")  # pyright: ignore[reportArgumentType]
