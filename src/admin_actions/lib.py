import abc
from collections.abc import Callable
from types import FunctionType
from typing import Any, TypeAlias

from django.contrib import messages
from django.contrib.admin import ModelAdmin
from django.db.models import QuerySet
from django.http import HttpRequest

Condition: TypeAlias = Callable[[Any], bool]  # Condition to enable the action


class AdminActionBaseClass(abc.ABC):
    """Generates an admin action for calling a function for a chosen set of records.

    Yes, it's basically an abstracted `map`.

    Example usage:
        conditional_action = MyAdminAction(
            function=my_function,
            condition=lambda record: record.should_process(),
            name="process_records",
        )

        def my_function(record_id):
            record = MyModel.objects.get(pk=record_id)
            ...

        class MyModelAdmin(admin.ModelAdmin):
            actions = [conditional_action]
            model = MyModel

    The `function` parameter is required and should be a callable that takes a
    single model instance's primary key as an argument.

    The `condition` parameter is optional. If provided, it should be a callable
    that takes a model instance and returns a boolean indicating whether to queue
    the task for that record.

    The `name` parameter is also optional. If provided, it will be used as the
    action's name in the admin interface. If it is omitted, the name of the
    function will be used instead.
    """

    @abc.abstractmethod
    def handle_item(self, item):
        """Handles a single item from the queryset."""

    def __call__(
        self, modeladmin: ModelAdmin, request: HttpRequest, queryset: QuerySet
    ) -> None:
        """Admin action to queue task for selected records."""
        _count: int = 0

        for record in queryset:
            if not self.condition(record):
                continue
            self.handle_item(record)
            _count += 1

        if _count:
            model_name = queryset.model._meta.verbose_name_plural.title()
            if _count == 1:
                model_name = queryset.model._meta.verbose_name.title()

            modeladmin.message_user(
                request,
                f"Called {self.__name__} for {_count} {model_name}.",
                messages.SUCCESS,
            )

    def __init__(
        self,
        function: FunctionType,
        *,
        condition: Condition | None = None,
        name: str | None = None,
    ) -> None:
        """Initializes the action with a function and optional condition."""

        if condition is not None:
            if isinstance(condition, Callable):  # Cannot call a non-callable condition
                self.condition = condition
            else:
                raise TypeError("The condition must be a callable.")
        else:
            self.condition = lambda _: True  # Default condition always returns True

        if not callable(function):  # Cannot call a non-callable task
            raise TypeError("The function must be a callable.")

        self.name = name
        self.function = function
        self.__name__ = name if name else function.__name__

