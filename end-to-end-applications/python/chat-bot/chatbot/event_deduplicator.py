from datetime import timedelta

from restate import VirtualObject, ObjectContext

event_deduplicator = VirtualObject("SlackMessageDeduplicator")


@event_deduplicator.handler()
async def is_new_message(ctx: ObjectContext, event_id: str):
    known = await ctx.get(event_id)

    if not known:
        ctx.set(event_id, True)
        ctx.object_send(expire_message_id, key=ctx.key(), arg=event_id, send_delay=timedelta(hours=24))

    return not known


@event_deduplicator.handler()
async def expire_message_id(ctx: ObjectContext, event_id: str):
    ctx.clear(event_id)
