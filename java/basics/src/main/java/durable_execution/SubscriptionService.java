package durable_execution;

import dev.restate.sdk.JsonSerdes;
import dev.restate.sdk.ObjectContext;
import dev.restate.sdk.annotation.Handler;
import dev.restate.sdk.annotation.VirtualObject;
import dev.restate.sdk.http.vertx.RestateHttpEndpointBuilder;
import utils.SubscriptionRequest;
import utils.SubscriptionResult;
import workflows.SignupWorkflow;

import static utils.ExampleStubs.createRecurringPayment;
import static utils.ExampleStubs.createSubscription;


@VirtualObject
public class SubscriptionService {

    @Handler
    public SubscriptionResult add(ObjectContext ctx, SubscriptionRequest req) {

        var paymentId = ctx.random().nextUUID().toString();
        var payRef = ctx.run("recurring payment", JsonSerdes.STRING, () ->
                createRecurringPayment(req.creditCard(), paymentId));

        for (String subscription : req.subscriptions()) {
            ctx.run("Creating subscription " + subscription,
                    () -> {
//                        if (subscription.equals("Disney")) {
//                            throw new IllegalStateException("Can't create subscription: Disney is not allowed");
//                        }
                        createSubscription(ctx.key(), subscription, payRef);
                    }
            );
        }

        return new SubscriptionResult(true, payRef);
    }

    public static void main(String[] args) {
        // Create an HTTP endpoint to serve your services
        RestateHttpEndpointBuilder.builder()
                .bind(new SubscriptionService())
                .bind(new SignupWorkflow())
                .buildAndListen();
    }
}

/*
Check the README to learn how to run Restate.
Then invoke this function and see in the log how it recovers.
Each action (e.g. "created recurring payment") is only logged once across all retries.
Retries did not re-execute the successful operations.

curl localhost:8080/SubscriptionService/add -H 'content-type: application/json' -d \
'{
    "userId": "Sam Beckett",
    "creditCard": "1234-5678-9012-3456",
    "subscriptions" : ["Netflix", "Disney+", "HBO Max"]
}'
*/
