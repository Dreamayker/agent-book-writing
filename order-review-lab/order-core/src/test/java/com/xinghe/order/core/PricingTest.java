package com.xinghe.order.core;

import static com.xinghe.order.core.Models.*;
import static org.junit.jupiter.api.Assertions.*;

import java.time.Instant;
import java.util.*;
import org.junit.jupiter.api.Test;

class PricingTest {
  static final Instant NOW = Instant.parse("2026-11-05T00:00:00Z");

  static Coupon coupon(
      String id,
      CouponType type,
      Set<String> categories,
      long threshold,
      long discount,
      boolean stack) {
    return new Coupon(
        id, "alice", type, categories, threshold, discount, 0, stack, "v1", NOW.plusSeconds(86400));
  }

  static List<Item> basket() {
    return List.of(
        new Item("A", "books", 12000, 1),
        new Item("B", "books", 20000, 1),
        new Item("C", "home", 8000, 1));
  }

  static PricingResult price(List<Item> items, Coupon... coupons) {
    return new PricingService()
        .price(new PricingRequest("alice", items, List.of(coupons), true), NOW);
  }

  @Test
  void fullStackingAndRefundAreConserved() {
    var result =
        price(
            basket(),
            coupon("order", CouponType.ORDER, Set.of(), 30000, 5000, true),
            coupon("new", CouponType.NEWCOMER, Set.of(), 0, 2000, true));
    assertEquals(33000, result.payableCents());
    assertEquals(
        List.of(9900L, 16500L, 6600L), result.units().stream().map(Unit::payableCents).toList());
    assertEquals(6600, new RefundAmountCalculator().calculate(result, List.of("C#001")));
    for (Unit unit : result.units())
      assertEquals(
          unit.grossCents(),
          unit.payableCents()
              + unit.discountShares().values().stream().mapToLong(Long::longValue).sum());
  }

  @Test
  void largestRemainderNeverLosesCents() {
    var allocator = new DiscountAllocator();
    assertEquals(
        Map.of("A", 1L, "B", 0L, "C", 0L),
        allocator.allocate(Map.of("C", 1L, "B", 1L, "A", 1L), 1));
    var random = new Random(42);
    for (int trial = 0; trial < 1000; trial++) {
      var weights = new TreeMap<String, Long>();
      for (int i = 0; i < 10; i++) weights.put("item" + i, (long) random.nextInt(10000));
      long total = weights.values().stream().mapToLong(Long::longValue).sum();
      long discount = random.nextLong(total + 1);
      var result = allocator.allocate(weights, discount);
      assertEquals(discount, result.values().stream().mapToLong(Long::longValue).sum());
      weights.forEach((id, value) -> assertTrue(result.get(id) >= 0 && result.get(id) <= value));
    }
    assertEquals(Map.of("A", 0L), allocator.allocate(Map.of("A", 0L), 0));
    assertThrows(DomainException.class, () -> allocator.allocate(Map.of("A", 1L), 2));
  }

  @Test
  void orderThresholdUsesPostCategoryAmount() {
    var category = coupon("category", CouponType.CATEGORY, Set.of("books"), 0, 1000, true);
    var order = coupon("order", CouponType.ORDER, Set.of(), 30000, 5000, true);
    assertEquals(
        25000, price(List.of(new Item("A", "books", 31000, 1)), category, order).payableCents());
    assertEquals(
        29999, price(List.of(new Item("A", "books", 30999, 1)), category, order).payableCents());
  }

  @Test
  void categoryEligibilityControlsThresholdAndAllocation() {
    var category = coupon("category", CouponType.CATEGORY, Set.of("books"), 10000, 1000, true);
    var result =
        price(List.of(new Item("A", "books", 9999, 1), new Item("B", "home", 20000, 1)), category);
    assertEquals(29999, result.payableCents());
    var eligible = price(basket(), category);
    assertEquals(8000, eligible.units().get(2).payableCents());
    assertEquals(0, eligible.units().get(2).discountShares().get("category"));
  }

  @Test
  void exclusiveChoiceComparesLegalFinalAmounts() {
    var order = coupon("order", CouponType.ORDER, Set.of(), 50000, 5000, true);
    var newcomer = coupon("new", CouponType.NEWCOMER, Set.of(), 0, 2000, false);
    assertEquals(38000, price(basket(), order, newcomer).payableCents());
    assertEquals(
        35000,
        price(basket(), coupon("order", CouponType.ORDER, Set.of(), 0, 5000, true), newcomer)
            .payableCents());
  }

  @Test
  void capIsRecordedAndQuantityRefundUsesFrozenUnitShares() {
    var result =
        price(
            List.of(new Item("A", "books", 1, 3)),
            coupon("order", CouponType.ORDER, Set.of(), 0, 10, true));
    assertEquals(0, result.payableCents());
    assertTrue(result.stages().get(0).capped());
    var shares =
        price(
            List.of(new Item("A", "books", 1, 3)),
            coupon("order", CouponType.ORDER, Set.of(), 0, 1, true));
    assertEquals(List.of(0L, 1L, 1L), shares.units().stream().map(Unit::payableCents).toList());
    assertEquals(1, new RefundAmountCalculator().calculate(shares, List.of("A#002")));
  }

  @Test
  void invalidCouponMoneyAndInputAreRejected() {
    assertThrows(DomainException.class, () -> new Item("A", "books", -1, 1));
    assertThrows(
        DomainException.class,
        () ->
            new CheckoutRequest(
                List.of(new RequestedLine("A", 1), new RequestedLine("A", 2)), List.of()));
    var order = coupon("order", CouponType.ORDER, Set.of(), 0, 1, true);
    assertThrows(DomainException.class, () -> price(basket(), order, order));
    var foreign =
        new Coupon(
            "foreign", "bob", CouponType.ORDER, Set.of(), 0, 1, 0, true, "v1", NOW.plusSeconds(1));
    assertThrows(DomainException.class, () -> price(basket(), foreign));
    var expired =
        new Coupon("expired", "alice", CouponType.ORDER, Set.of(), 0, 1, 0, true, "v1", NOW);
    assertThrows(DomainException.class, () -> price(basket(), expired));
    assertThrows(
        DomainException.class,
        () -> new RefundAmountCalculator().calculate(price(basket()), List.of("missing")));
    assertThrows(DomainException.class, () -> new RefundRequest(List.of("A#001", "A#001")));
  }

  @Test
  void basisPointDiscountRoundsDownOncePerStage() {
    var rate =
        new Coupon(
            "rate",
            "alice",
            CouponType.CATEGORY,
            Set.of("books"),
            0,
            0,
            1000,
            true,
            "v1",
            NOW.plusSeconds(1));
    assertEquals(9, price(List.of(new Item("A", "books", 10, 1)), rate).payableCents());
    assertEquals(10, price(List.of(new Item("A", "books", 11, 1)), rate).payableCents());
  }
}
