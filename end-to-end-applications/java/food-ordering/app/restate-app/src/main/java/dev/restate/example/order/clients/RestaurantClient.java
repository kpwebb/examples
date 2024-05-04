/*
 * Copyright (c) 2024 - Restate Software, Inc., Restate GmbH
 *
 * This file is part of the Restate examples,
 * which is released under the MIT license.
 *
 * You can find a copy of the license in the file LICENSE
 * in the root directory of this repository or package or at
 * https://github.com/restatedev/examples/
 */

package dev.restate.example.order.clients;

import dev.restate.sdk.common.TerminalException;
import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

public class RestaurantClient {
  private final Logger logger = LogManager.getLogger(RestaurantClient.class);

  public static final String RESTAURANT_ENDPOINT =
      System.getenv("RESTAURANT_ENDPOINT") != null
          ? System.getenv("RESTAURANT_ENDPOINT")
          : "http://localhost:5050";

  private final HttpClient httpClient;

  private RestaurantClient() {
    httpClient = HttpClient.newBuilder().build();
  }

  public static RestaurantClient get() {
    return new RestaurantClient();
  }

  public void prepare(String orderId, String callbackId) throws IOException, InterruptedException {
    this.call(orderId, callbackId, "/prepare");
  }

  private void call(String orderId, String callbackId, String method)
      throws IOException, InterruptedException {
    logger.info(
        String.format(
            "Calling restaurant service with orderId %s and callbackId %s", orderId, callbackId));
    URI uri = URI.create(RESTAURANT_ENDPOINT + method);
    String requestBody = String.format("{\"cb\":\"%s\",\"orderId\":\"%s\"}", callbackId, orderId);
    HttpRequest request =
        HttpRequest.newBuilder()
            .uri(uri)
            .header("Content-Type", "application/json")
            .POST(HttpRequest.BodyPublishers.ofString(requestBody))
            .build();
    HttpResponse<?> response = httpClient.send(request, HttpResponse.BodyHandlers.discarding());
    if (response.statusCode() != 200) {
      throw new TerminalException(
          "Prepare request to restaurant failed with status code: " + response.statusCode());
    } else {
      logger.info("Restaurant service responded with " + response.statusCode());
    }
  }
}
