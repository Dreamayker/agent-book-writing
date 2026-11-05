package com.xinghe.order.core;

import static com.xinghe.order.core.DomainException.require;
import static com.xinghe.order.core.Models.*;

import java.util.*;

public final class RefundAmountCalculator {
  public long calculate(PricingResult pricing, List<String> unitIds) {
    Set<String> selected = new HashSet<>(new RefundRequest(unitIds).unitIds());
    var units = pricing.units().stream().filter(u -> selected.contains(u.unitId())).toList();
    require(units.size() == selected.size(), "INVALID", "Unknown unit");
    return units.stream().mapToLong(Unit::payableCents).reduce(0, Math::addExact);
  }
}
