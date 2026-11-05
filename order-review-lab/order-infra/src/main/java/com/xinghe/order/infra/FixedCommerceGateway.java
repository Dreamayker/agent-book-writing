package com.xinghe.order.infra;

import static com.xinghe.order.core.DomainException.require;
import static com.xinghe.order.core.Models.*;

import java.time.Instant;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;
import org.springframework.stereotype.Component;

/** Server-controlled teaching fixtures; checkout never accepts a client price or owner. */
@Component
public final class FixedCommerceGateway {
  private final Map<String, Coupon> rules = new ConcurrentHashMap<>();
  private final AtomicInteger reads = new AtomicInteger();

  public FixedCommerceGateway() {
    reset();
  }

  public void reset() {
    rules.clear();
    reads.set(0);
    register(coupon("order5000", CouponType.ORDER, Set.of(), 30000, 5000, true));
    register(coupon("new2000", CouponType.NEWCOMER, Set.of(), 0, 2000, true));
    register(coupon("category1000", CouponType.CATEGORY, Set.of("books"), 10000, 1000, true));
  }

  public static Coupon coupon(
      String id,
      CouponType type,
      Set<String> categories,
      long threshold,
      long amount,
      boolean stackable) {
    return new Coupon(
        id,
        "alice",
        type,
        categories,
        threshold,
        amount,
        0,
        stackable,
        "v1",
        Instant.parse("2099-01-01T00:00:00Z"));
  }

  public void register(Coupon coupon) {
    rules.put(coupon.id(), coupon);
  }

  public int pricingReads() {
    return reads.get();
  }

  public PricingRequest resolve(String owner, CheckoutRequest request) {
    reads.incrementAndGet();
    var items =
        request.items().stream()
            .map(
                line -> {
                  long price =
                      switch (line.itemId()) {
                        case "A" -> 12000;
                        case "B" -> 20000;
                        case "C" -> 8000;
                        default -> -1;
                      };
                  require(price >= 0, "INVALID", "Unknown product");
                  return new Item(
                      line.itemId(),
                      line.itemId().equals("C") ? "home" : "books",
                      price,
                      line.quantity());
                })
            .toList();
    var coupons =
        request.couponIds().stream()
            .map(
                id -> {
                  Coupon coupon = rules.get(id);
                  require(coupon != null, "INVALID", "Unknown coupon");
                  return coupon;
                })
            .toList();
    return new PricingRequest(owner, items, coupons, owner.equals("alice"));
  }
}
