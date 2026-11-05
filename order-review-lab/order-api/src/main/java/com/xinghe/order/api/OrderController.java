package com.xinghe.order.api;

import static com.xinghe.order.core.Models.*;

import com.xinghe.order.core.*;
import java.util.Map;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

/** X-User-Id is a sandbox identity adapter, never a production authentication mechanism. */
@RestController
@RequestMapping("/orders")
public class OrderController {
  private final OrderUseCases orders;

  public OrderController(OrderUseCases orders) {
    this.orders = orders;
  }

  @PostMapping("/quote")
  public PricingResult quote(
      @RequestHeader("X-User-Id") String owner, @RequestBody CheckoutRequest request) {
    return orders.quote(owner, request);
  }

  @PostMapping
  public OrderResult checkout(
      @RequestHeader("X-User-Id") String owner,
      @RequestHeader("Idempotency-Key") String key,
      @RequestBody CheckoutRequest request) {
    return orders.checkout(owner, key, request);
  }

  @GetMapping("/{id}")
  public OrderDetail read(@RequestHeader("X-User-Id") String owner, @PathVariable String id) {
    return orders.read(owner, id);
  }

  @PostMapping("/{id}/refunds")
  public RefundResult refund(
      @RequestHeader("X-User-Id") String owner,
      @PathVariable String id,
      @RequestHeader("Idempotency-Key") String key,
      @RequestBody RefundRequest request) {
    return orders.refund(owner, id, key, request);
  }

  @PostMapping("/{id}/splits")
  public SplitResult split(
      @RequestHeader("X-User-Id") String owner,
      @PathVariable String id,
      @RequestHeader("Idempotency-Key") String key,
      @RequestBody SplitRequest request) {
    return orders.split(owner, id, key, request);
  }

  @ExceptionHandler(DomainException.class)
  public ResponseEntity<Map<String, String>> failure(DomainException error) {
    int status =
        switch (error.code()) {
          case "FORBIDDEN" -> 403;
          case "NOT_FOUND" -> 404;
          case "CONFLICT", "MANUAL_REVIEW" -> 409;
          default -> 400;
        };
    return ResponseEntity.status(status)
        .body(Map.of("code", error.code(), "message", error.getMessage()));
  }
}
