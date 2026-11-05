package com.xinghe.order.core;

import static com.xinghe.order.core.DomainException.require;

import java.time.Instant;
import java.util.*;

public final class Models {
  private Models() {}

  public static String identifier(String value) {
    require(value != null && value.matches("[A-Za-z0-9_-]{1,64}"), "INVALID", "Invalid identifier");
    return value;
  }

  public static long money(long value) {
    require(
        value >= 0 && value <= 1_000_000_000_000L,
        "INVALID",
        "Amount outside supported cents range");
    return value;
  }

  public enum CouponType {
    CATEGORY,
    ORDER,
    NEWCOMER
  }

  public record RequestedLine(String itemId, int quantity) {
    public RequestedLine {
      identifier(itemId);
      require(quantity > 0 && quantity <= 100, "INVALID", "Quantity must be 1..100");
    }
  }

  public record CheckoutRequest(List<RequestedLine> items, List<String> couponIds) {
    public CheckoutRequest {
      require(
          items != null && !items.isEmpty() && items.size() <= 100,
          "INVALID",
          "Require 1..100 lines");
      items = List.copyOf(items);
      couponIds = List.copyOf(Objects.requireNonNull(couponIds));
      require(
          items.stream().map(RequestedLine::itemId).distinct().count() == items.size(),
          "INVALID",
          "Duplicate item");
      require(
          items.stream().mapToInt(RequestedLine::quantity).sum() <= 1000,
          "INVALID",
          "At most 1000 units");
      require(
          couponIds.size() <= 3 && new HashSet<>(couponIds).size() == couponIds.size(),
          "INVALID",
          "Duplicate/excess coupons");
      couponIds.forEach(Models::identifier);
    }
  }

  public record Item(String itemId, String category, long activityCents, int quantity) {
    public Item {
      identifier(itemId);
      identifier(category);
      money(activityCents);
      new RequestedLine(itemId, quantity);
    }
  }

  public record Coupon(
      String id,
      String owner,
      CouponType type,
      Set<String> categories,
      long thresholdCents,
      long discountCents,
      int discountBps,
      boolean stackableWithOrder,
      String ruleVersion,
      Instant expiresAt) {
    public Coupon {
      identifier(id);
      identifier(owner);
      Objects.requireNonNull(type);
      categories = Set.copyOf(categories);
      money(thresholdCents);
      money(discountCents);
      identifier(ruleVersion);
      Objects.requireNonNull(expiresAt);
      require(
          discountBps >= 0 && discountBps <= 10000,
          "INVALID",
          "Rate must be 0..10000 basis points");
      require((discountCents > 0) != (discountBps > 0), "INVALID", "Specify one discount kind");
      require(
          type != CouponType.CATEGORY || !categories.isEmpty(),
          "INVALID",
          "Category coupon needs eligible categories");
    }
  }

  public record PricingRequest(
      String owner, List<Item> items, List<Coupon> coupons, boolean newcomer) {
    public PricingRequest {
      identifier(owner);
      items = List.copyOf(items);
      coupons = List.copyOf(coupons);
    }
  }

  public record Unit(
      String unitId,
      String itemId,
      int unitIndex,
      String category,
      long grossCents,
      Map<String, Long> discountShares,
      long payableCents) {
    public Unit {
      discountShares = Collections.unmodifiableMap(new TreeMap<>(discountShares));
    }
  }

  public record Stage(
      String couponId,
      CouponType type,
      String ruleVersion,
      long baseCents,
      long actualDiscountCents,
      boolean capped) {}

  public record PricingResult(
      long grossCents,
      long discountCents,
      long payableCents,
      List<Unit> units,
      List<Stage> stages,
      List<String> decisions) {
    public PricingResult {
      units = List.copyOf(units);
      stages = List.copyOf(stages);
      decisions = List.copyOf(decisions);
    }
  }

  public record OrderSnapshot(
      int version,
      String orderId,
      String owner,
      Instant createdAt,
      CheckoutRequest request,
      PricingResult pricing) {}

  public record OrderResult(String orderId, long payableCents, String snapshotHash) {}

  public record RefundRequest(List<String> unitIds) {
    public RefundRequest {
      require(
          unitIds != null && !unitIds.isEmpty() && unitIds.size() <= 1000,
          "INVALID",
          "Select 1..1000 units");
      unitIds = unitIds.stream().sorted().toList();
      require(new HashSet<>(unitIds).size() == unitIds.size(), "INVALID", "Duplicate unit");
    }
  }

  public record RefundResult(
      String refundId,
      String orderId,
      List<String> unitIds,
      long amountCents,
      String snapshotHash) {}

  public record SplitRequest(List<List<String>> groups) {
    public SplitRequest {
      require(
          groups != null && groups.size() >= 2 && groups.size() <= 100,
          "INVALID",
          "Require 2..100 child groups");
      groups = groups.stream().map(g -> new RefundRequest(g).unitIds()).toList();
    }
  }

  public record SplitResult(List<String> orderIds) {
    public SplitResult {
      orderIds = List.copyOf(orderIds);
    }
  }

  public record OrderDetail(
      String orderId,
      String rootOrderId,
      String owner,
      List<Unit> units,
      long payableCents,
      long rootRefundedCents,
      String snapshotHash) {}
}
