package com.xinghe.order.core;

import static com.xinghe.order.core.DomainException.require;
import static com.xinghe.order.core.Models.*;

import java.math.BigInteger;
import java.time.Instant;
import java.util.*;

public final class PricingService {
  private final DiscountAllocator allocator = new DiscountAllocator();

  public PricingResult price(PricingRequest request, Instant now) {
    require(
        !request.items().isEmpty() && request.items().size() <= 100, "INVALID", "Invalid lines");
    require(
        request.items().stream().map(Item::itemId).distinct().count() == request.items().size(),
        "INVALID",
        "Duplicate item");
    require(
        request.items().stream().mapToInt(Item::quantity).sum() <= 1000,
        "INVALID",
        "Too many units");
    Map<CouponType, Coupon> coupons = new EnumMap<>(CouponType.class);
    List<String> decisions = new ArrayList<>();
    for (Coupon coupon : request.coupons()) {
      require(
          coupon.owner().equals(request.owner()), "FORBIDDEN", "Coupon belongs to another user");
      require(coupon.expiresAt().isAfter(now), "INVALID", "Coupon expired");
      require(coupons.putIfAbsent(coupon.type(), coupon) == null, "INVALID", "One coupon per type");
    }
    if (!request.newcomer() && coupons.remove(CouponType.NEWCOMER) != null)
      decisions.add("newcomer:ineligible");
    List<Unit> units = new ArrayList<>();
    for (Item item : request.items().stream().sorted(Comparator.comparing(Item::itemId)).toList()) {
      for (int i = 1; i <= item.quantity(); i++)
        units.add(
            new Unit(
                item.itemId() + "#" + String.format(Locale.ROOT, "%03d", i),
                item.itemId(),
                i,
                item.category(),
                item.activityCents(),
                Map.of(),
                item.activityCents()));
    }
    money(units.stream().mapToLong(Unit::grossCents).reduce(0, Math::addExact));
    PricingResult initial = result(units, List.of(), decisions);
    PricingResult category = apply(initial, coupons.get(CouponType.CATEGORY));
    Coupon order = coupons.get(CouponType.ORDER), newcomer = coupons.get(CouponType.NEWCOMER);
    if (order != null && newcomer != null && !newcomer.stackableWithOrder()) {
      PricingResult orderPath = apply(category, order), newcomerPath = apply(category, newcomer);
      PricingResult chosen =
          orderPath.payableCents() <= newcomerPath.payableCents() ? orderPath : newcomerPath;
      var reasons = new ArrayList<>(chosen.decisions());
      reasons.add(
          "exclusive:order="
              + orderPath.payableCents()
              + ",newcomer="
              + newcomerPath.payableCents());
      return result(chosen.units(), chosen.stages(), reasons);
    }
    return apply(apply(category, order), newcomer);
  }

  private PricingResult apply(PricingResult before, Coupon coupon) {
    if (coupon == null) return before;
    Map<String, Long> weights = new TreeMap<>();
    before.units().stream()
        .filter(
            u -> coupon.type() != CouponType.CATEGORY || coupon.categories().contains(u.category()))
        .forEach(u -> weights.put(u.unitId(), u.payableCents()));
    long base = coupon.type() == CouponType.ORDER ? before.grossCents() : weights.values().stream().mapToLong(Long::longValue).sum();
    long requested =
        base < coupon.thresholdCents()
            ? 0
            : coupon.discountBps() > 0
                ? BigInteger.valueOf(base)
                    .multiply(BigInteger.valueOf(coupon.discountBps()))
                    .divide(BigInteger.valueOf(10000))
                    .longValueExact()
                : coupon.discountCents();
    long actual = Math.min(base, requested);
    var allocated = allocator.allocate(weights, actual);
    var next =
        before.units().stream()
            .map(
                u -> {
                  long share = allocated.getOrDefault(u.unitId(), 0L);
                  var shares = new TreeMap<>(u.discountShares());
                  shares.put(coupon.id(), share);
                  return new Unit(
                      u.unitId(),
                      u.itemId(),
                      u.unitIndex(),
                      u.category(),
                      u.grossCents(),
                      shares,
                      u.payableCents() - share);
                })
            .toList();
    var stages = new ArrayList<>(before.stages());
    stages.add(
        new Stage(
            coupon.id(), coupon.type(), coupon.ruleVersion(), base, actual, actual < requested));
    var decisions = new ArrayList<>(before.decisions());
    decisions.add(
        coupon.id()
            + (base < coupon.thresholdCents()
                ? ":threshold-not-met"
                : actual < requested ? ":discount-capped" : ":applied"));
    return result(next, stages, decisions);
  }

  private PricingResult result(List<Unit> units, List<Stage> stages, List<String> decisions) {
    long gross = units.stream().mapToLong(Unit::grossCents).sum(),
        payable = units.stream().mapToLong(Unit::payableCents).sum();
    return new PricingResult(gross, gross - payable, payable, units, stages, decisions);
  }
}
