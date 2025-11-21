from types import FunctionType

from admin_actions.lib import AdminActionBaseClass, Condition


class BroadcastPubSubAction(AdminActionBaseClass):
    """
    Generates an admin action for broadcasting a pubsub message for a chosen
    set of records.

    Usage:
        conditional_action = BroadcastPubSubAction(
            publish_item,
            condition=lambda record: record.is_complete(),
        )

        def publish_item(record_id):
            record = MyModel.objects.get(pk=record_id)
            record.publish_to_pubsub()

        class MyModelAdmin(admin.ModelAdmin):
            actions = [conditional_action]
            model = MyModel
    """

    def handle_item(self, item):
        """Handles a single item from the queryset."""
        self.function(item.pk)

    def __init__(
        self,
        function: FunctionType,
        *,
        condition: Condition | None = None,
        name: str | None = None,
    ) -> None:
        """Initializes the action with function and optional condition."""

        # TODO: Check to make sure `function` is correct outside of being callable.
        super().__init__(function=function, condition=condition, name=name)
