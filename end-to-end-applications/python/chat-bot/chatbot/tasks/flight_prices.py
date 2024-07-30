from datetime import timedelta

from restate import Workflow, WorkflowContext, WorkflowSharedContext

from chatbot.utils.flight_price_api import FlightPriceOpts, get_best_quote

POLL_INTERVAL = 10000

flight_watcher = Workflow("flight_price_watcher")


@flight_watcher.handlers()
async def run(ctx: WorkflowContext, opts: FlightPriceOpts):
    cancelled = ctx.promise("cancelled")
    attempt = 0

    while not await cancelled.peek():
        best_offer_so_far = await ctx.run("Probing prices #" + str(attempt + 1),
                                          lambda: get_best_quote(opts["trip"], opts["price_threshold_usd"]))

        if best_offer_so_far["price"] <= opts["price_threshold_usd"]:
            return "Found an offer matching the price for" + opts["name"] + " " + str(best_offer_so_far)

        ctx.set("last_quote", best_offer_so_far)

        await ctx.sleep(timedelta(milliseconds=POLL_INTERVAL))

    return "(cancelled)"


@flight_watcher.handler()
async def cancel(ctx: WorkflowSharedContext):
    await ctx.promise("cancelled").resolve(True)


@flight_watcher.handler()
async def current_status(ctx: WorkflowSharedContext):
    return await ctx.get("last_quote")
