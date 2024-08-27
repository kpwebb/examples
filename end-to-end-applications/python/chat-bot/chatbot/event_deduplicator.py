"""
Simple VirtualObject that deduplicates Slack messages based on their event id.
"""

from datetime import timedelta

from restate import VirtualObject, ObjectContext

event_deduplicator = VirtualObject("SlackMessageDeduplicator")

@event_deduplicator.handler()
async def is_new_message(ctx: ObjectContext, event_id: str):
    """
    Remember the event id and return True if it is new, otherwise return False.
    We store the event id for 24 hours.
    """
    known = await ctx.get(event_id)
    if known is not None:
        return False

    # Remember the event id
    ctx.set(event_id, True)

    # Expire the event id after 24 hours
    ctx.object_send(expire_message_id, key=ctx.key(), arg=event_id, send_delay=timedelta(hours=24))
    return True


@event_deduplicator.handler()
async def expire_message_id(ctx: ObjectContext, event_id: str):
    """
    Expire an event from state.
    """
    ctx.clear(event_id)
