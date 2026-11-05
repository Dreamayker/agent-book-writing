package com.xinghe.order.infra;

import static com.xinghe.order.core.DomainException.require;
import static com.xinghe.order.core.Models.*;
import static com.xinghe.order.infra.OrderMapper.*;

import com.xinghe.order.core.*;
import java.time.Instant;
import java.util.*;
import java.util.function.Supplier;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class OrderApplicationService implements OrderUseCases {
  private final OrderMapper db;
  private final FixedCommerceGateway gateway;
  private final SnapshotCodec codec;
  private final PricingService pricing = new PricingService();
  private final RefundAmountCalculator refunds = new RefundAmountCalculator();

  public OrderApplicationService(
      OrderMapper db, FixedCommerceGateway gateway, SnapshotCodec codec) {
    this.db = db;
    this.gateway = gateway;
    this.codec = codec;
  }

  public PricingResult quote(String owner, CheckoutRequest request) {
    identifier(owner);
    return pricing.price(gateway.resolve(owner, request), Instant.now());
  }

  @Transactional
  public OrderResult checkout(String owner, String key, CheckoutRequest request) {
    lockOwner(owner);
    return once(
        owner,
        "checkout",
        key,
        request,
        OrderResult.class,
        () -> {
          var result = quote(owner, request);
          String id = UUID.randomUUID().toString();
          var snapshot = new OrderSnapshot(1, id, owner, Instant.now(), request, result);
          String json = codec.encode(snapshot), hash = codec.hash(snapshot);
          db.insert(new OrderRow(id, id, owner, json, hash, result.payableCents(), 0, false));
          for (Unit unit : result.units()) {
            db.insertUnit(id, unit.unitId(), unit.payableCents());
            db.membership(id, unit.unitId());
          }
          for (Stage stage : result.stages()) {
            if (stage.actualDiscountCents() > 0) {
              require(
                  db.couponConsumed(stage.couponId()) == 0, "CONFLICT", "Coupon already consumed");
              db.consumeCoupon(stage.couponId(), id);
            }
          }
          return new OrderResult(id, result.payableCents(), hash);
        });
  }

  @Transactional(readOnly = true)
  public OrderDetail read(String owner, String orderId) {
    var order = owned(owner, orderId);
    var root = db.find(order.rootOrderId());
    var snapshot = snapshot(root);
    Set<String> allowed = unitIds(db.units(root.orderId(), orderId));
    var units =
        snapshot.pricing().units().stream().filter(u -> allowed.contains(u.unitId())).toList();
    return new OrderDetail(
        orderId,
        root.orderId(),
        owner,
        units,
        order.payableCents(),
        root.refundedCents(),
        root.snapshotHash());
  }

  @Transactional
  public RefundResult refund(String owner, String orderId, String key, RefundRequest request) {
    lockOwner(owner);
    var order = owned(owner, orderId);
    var root = db.lock(order.rootOrderId());
    return once(
        owner,
        "refund:" + orderId,
        key,
        request,
        RefundResult.class,
        () -> {
          var snapshot = snapshot(root);
          var units = db.units(root.orderId(), orderId);
          require(
              unitIds(units).containsAll(request.unitIds()),
              "INVALID",
              "Unit does not belong to order");
          require(
              units.stream().noneMatch(u -> request.unitIds().contains(u.unitId()) && u.refunded()),
              "CONFLICT",
              "Unit already refunded");
          long amount = refunds.calculate(snapshot.pricing(), request.unitIds());
          require(
              db.increaseRefund(root.orderId(), amount) == 1,
              "CONFLICT",
              "Refund exceeds paid amount");
          for (String unit : request.unitIds())
            require(
                db.markRefunded(root.orderId(), unit) == 1, "CONFLICT", "Unit already refunded");
          String id = UUID.randomUUID().toString();
          db.saveRefund(
              id,
              orderId,
              root.orderId(),
              amount,
              codec.encode(request.unitIds()),
              root.snapshotHash());
          return new RefundResult(id, orderId, request.unitIds(), amount, root.snapshotHash());
        });
  }

  @Transactional
  public SplitResult split(String owner, String orderId, String key, SplitRequest request) {
    lockOwner(owner);
    var order = owned(owner, orderId);
    db.lock(order.rootOrderId());
    return once(
        owner,
        "split:" + orderId,
        key,
        request,
        SplitResult.class,
        () -> {
          var units = db.units(order.rootOrderId(), orderId);
          var flat = request.groups().stream().flatMap(Collection::stream).toList();
          require(
              new HashSet<>(flat).size() == flat.size()
                  && new HashSet<>(flat).equals(unitIds(units)),
              "INVALID",
              "Split must partition all original units");
          require(
              units.stream().noneMatch(UnitRow::refunded),
              "CONFLICT",
              "Cannot split a refunded order");
          require(db.markSplit(orderId) == 1, "CONFLICT", "Order already split");
          var children = new ArrayList<String>();
          for (List<String> group : request.groups()) {
            String id = UUID.randomUUID().toString();
            long amount =
                units.stream()
                    .filter(u -> group.contains(u.unitId()))
                    .mapToLong(UnitRow::payableCents)
                    .sum();
            db.insert(new OrderRow(id, order.rootOrderId(), owner, null, null, amount, 0, false));
            group.forEach(unit -> db.membership(id, unit));
            children.add(id);
          }
          return new SplitResult(children);
        });
  }

  private void lockOwner(String owner) {
    identifier(owner);
    db.ensurePrincipal(owner);
    db.lockPrincipal(owner);
  }

  private OrderRow owned(String owner, String id) {
    identifier(owner);
    identifier(id);
    var order = db.find(id);
    require(order != null, "NOT_FOUND", "Order not found");
    require(order.ownerId().equals(owner), "FORBIDDEN", "Order belongs to another user");
    return order;
  }

  private OrderSnapshot snapshot(OrderRow root) {
    require(
        root.snapshotJson() != null && root.snapshotHash() != null,
        "MANUAL_REVIEW",
        "Historical order has no trusted snapshot");
    var snapshot = codec.decode(root.snapshotJson(), OrderSnapshot.class);
    require(
        codec.hash(snapshot).equals(root.snapshotHash()),
        "MANUAL_REVIEW",
        "Snapshot integrity check failed");
    require(
        snapshot.version() == 1
            && snapshot.orderId().equals(root.orderId())
            && snapshot.owner().equals(root.ownerId()),
        "MANUAL_REVIEW",
        "Snapshot identity mismatch");
    return snapshot;
  }

  private static Set<String> unitIds(List<UnitRow> units) {
    return units.stream().map(UnitRow::unitId).collect(java.util.stream.Collectors.toSet());
  }

  private <T> T once(
      String owner,
      String operation,
      String key,
      Object request,
      Class<T> type,
      Supplier<T> action) {
    identifier(key);
    String fingerprint = codec.hash(request);
    var previous = db.idempotency(owner, operation, key);
    if (previous != null) {
      require(
          previous.fingerprint().equals(fingerprint),
          "CONFLICT",
          "Idempotency key reused with different request");
      return codec.decode(previous.responseJson(), type);
    }
    T response = action.get();
    db.saveIdempotency(owner, operation, key, fingerprint, codec.encode(response));
    return response;
  }
}
