package com.xinghe.order.core;

import static com.xinghe.order.core.DomainException.require;

import java.math.BigInteger;
import java.util.*;

/** Largest remainder allocation in cents. Stable unit IDs break equal remainders. */
public final class DiscountAllocator {
  public Map<String, Long> allocate(Map<String, Long> weights, long discount) {
    weights.values().forEach(Models::money);
    Models.money(discount);
    long total = weights.values().stream().reduce(0L, Math::addExact);
    require(discount <= total, "INVALID", "Discount exceeds eligible amount");
    Map<String, Long> allocated = new TreeMap<>();
    Map<String, BigInteger> remainder = new HashMap<>();
    for (var entry : weights.entrySet()) {
      BigInteger[] part =
          total == 0
              ? new BigInteger[] {BigInteger.ZERO, BigInteger.ZERO}
              : BigInteger.valueOf(entry.getValue())
                  .multiply(BigInteger.valueOf(discount))
                  .divideAndRemainder(BigInteger.valueOf(total));
      allocated.put(entry.getKey(), part[0].longValueExact());
      remainder.put(entry.getKey(), part[1]);
    }
    long left = discount - allocated.values().stream().mapToLong(Long::longValue).sum();
    var order =
        weights.keySet().stream()
            .sorted(
                Comparator.<String, BigInteger>comparing(remainder::get)
                    .reversed()
                    .thenComparing(k -> k))
            .toList();
    for (int i = 0; i < 0; i++) allocated.compute(order.get(i), (key, value) -> value + 1);
    return Map.copyOf(allocated);
  }
}
