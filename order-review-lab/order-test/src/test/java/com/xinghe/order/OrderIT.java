package com.xinghe.order;

import static com.xinghe.order.core.Models.*;
import static org.junit.jupiter.api.Assertions.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

import com.xinghe.order.core.*;
import com.xinghe.order.infra.*;
import java.util.*;
import java.util.concurrent.*;
import org.junit.jupiter.api.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.test.web.servlet.MockMvc;
import org.testcontainers.containers.MySQLContainer;
import org.testcontainers.junit.jupiter.*;

@Testcontainers
@SpringBootTest(classes = OrderApplication.class)
@AutoConfigureMockMvc
class OrderIT {
  @Container static final MySQLContainer<?> MYSQL = new MySQLContainer<>("mysql:8.4.7");

  @DynamicPropertySource
  static void database(DynamicPropertyRegistry properties) {
    properties.add("spring.datasource.url", MYSQL::getJdbcUrl);
    properties.add("spring.datasource.username", MYSQL::getUsername);
    properties.add("spring.datasource.password", MYSQL::getPassword);
  }

  @Autowired OrderUseCases orders;
  @Autowired FixedCommerceGateway gateway;
  @Autowired JdbcTemplate sql;
  @Autowired MockMvc http;

  @BeforeEach
  void reset() {
    for (String table :
        List.of(
            "refund_requests",
            "idempotency_records",
            "coupon_uses",
            "order_memberships",
            "order_units",
            "orders",
            "principal_locks")) sql.update("DELETE FROM " + table);
    gateway.reset();
  }

  CheckoutRequest basket() {
    return new CheckoutRequest(
        List.of(new RequestedLine("A", 1), new RequestedLine("B", 1), new RequestedLine("C", 1)),
        List.of("order5000", "new2000"));
  }

  OrderResult checkout() {
    return orders.checkout("alice", "checkout", basket());
  }

  @Test
  void refundUsesImmutableSnapshotAfterRuleChange() {
    var order = checkout();
    assertEquals(33000, order.payableCents());
    gateway.register(
        FixedCommerceGateway.coupon("order5000", CouponType.ORDER, Set.of(), 30000, 6000, true));
    int before = gateway.pricingReads();
    var refund =
        orders.refund("alice", order.orderId(), "refund", new RefundRequest(List.of("C#001")));
    assertEquals(6600, refund.amountCents());
    assertEquals(before, gateway.pricingReads());
    assertEquals(6600, sql.queryForObject("SELECT amount_cents FROM refund_requests", Long.class));
    assertEquals(order.snapshotHash(), refund.snapshotHash());
    System.out.println(
        "ORD-09 snapshot refund expected=6600 actual="
            + refund.amountCents()
            + " livePricingReadsDuringRefund="
            + (gateway.pricingReads() - before));
  }

  @Test
  void idempotentRefundAndChangedPayloadConflict() {
    var order = checkout();
    var request = new RefundRequest(List.of("C#001"));
    var first = orders.refund("alice", order.orderId(), "retry", request);
    assertEquals(first, orders.refund("alice", order.orderId(), "retry", request));
    assertCode(
        "CONFLICT",
        () ->
            orders.refund("alice", order.orderId(), "retry", new RefundRequest(List.of("A#001"))));
    assertEquals(1, sql.queryForObject("SELECT COUNT(*) FROM refund_requests", Integer.class));
    assertEquals(6600, orders.read("alice", order.orderId()).rootRefundedCents());
  }

  @Test
  void checkoutRetryDoesNotConsumeCouponsTwice() {
    var first = checkout();
    assertEquals(first, orders.checkout("alice", "checkout", basket()));
    assertCode("CONFLICT", () -> orders.checkout("alice", "other", basket()));
    assertEquals(1, sql.queryForObject("SELECT COUNT(*) FROM orders", Integer.class));
  }

  @Test
  void parallelRefundsCannotRefundOneUnitTwice() throws Exception {
    var order = checkout();
    var results =
        race(
            () ->
                orders.refund(
                    "alice",
                    order.orderId(),
                    UUID.randomUUID().toString(),
                    new RefundRequest(List.of("C#001"))));
    assertEquals(1, results.stream().filter(RefundResult.class::isInstance).count());
    assertEquals(
        1,
        results.stream()
            .filter(x -> x instanceof DomainException e && e.code().equals("CONFLICT"))
            .count());
    assertEquals(6600, orders.read("alice", order.orderId()).rootRefundedCents());
    assertEquals(1, sql.queryForObject("SELECT COUNT(*) FROM refund_requests", Integer.class));
  }

  @Test
  void concurrentSameKeyReturnsSameRefund() throws Exception {
    var order = checkout();
    var results =
        race(
            () ->
                orders.refund(
                    "alice", order.orderId(), "same", new RefundRequest(List.of("C#001"))));
    assertInstanceOf(RefundResult.class, results.get(0));
    assertEquals(results.get(0), results.get(1));
    assertEquals(1, sql.queryForObject("SELECT COUNT(*) FROM refund_requests", Integer.class));
  }

  @Test
  void concurrentCheckoutCannotConsumeCouponTwice() throws Exception {
    var results = race(() -> orders.checkout("alice", UUID.randomUUID().toString(), basket()));
    assertEquals(1, results.stream().filter(OrderResult.class::isInstance).count());
    assertEquals(1, sql.queryForObject("SELECT COUNT(*) FROM orders", Integer.class));
  }

  @Test
  void splitKeepsOriginalSharesAndSharedRefundLedger() {
    var order = checkout();
    var request = new SplitRequest(List.of(List.of("A#001", "B#001"), List.of("C#001")));
    var split = orders.split("alice", order.orderId(), "split", request);
    assertEquals(split, orders.split("alice", order.orderId(), "split", request));
    var first = orders.read("alice", split.orderIds().get(0));
    var second = orders.read("alice", split.orderIds().get(1));
    assertEquals(33000, first.payableCents() + second.payableCents());
    assertEquals(6600, second.payableCents());
    assertEquals(
        6600,
        orders
            .refund("alice", second.orderId(), "child", new RefundRequest(List.of("C#001")))
            .amountCents());
    assertCode(
        "CONFLICT",
        () ->
            orders.refund("alice", order.orderId(), "parent", new RefundRequest(List.of("C#001"))));
  }

  @Test
  void invalidSplitAndUnknownUnitRollBack() {
    var order = checkout();
    assertCode(
        "INVALID",
        () ->
            orders.split(
                "alice",
                order.orderId(),
                "bad",
                new SplitRequest(List.of(List.of("A#001"), List.of("C#001")))));
    assertCode(
        "INVALID",
        () ->
            orders.refund("alice", order.orderId(), "bad", new RefundRequest(List.of("unknown"))));
    assertEquals(0, orders.read("alice", order.orderId()).rootRefundedCents());
  }

  @Test
  void oldOrdersAndSnapshotCorruptionRequireManualReview() {
    var order = checkout();
    sql.update(
        "UPDATE orders SET snapshot_hash=? WHERE order_id=?", "0".repeat(64), order.orderId());
    assertCode(
        "MANUAL_REVIEW",
        () -> orders.refund("alice", order.orderId(), "bad", new RefundRequest(List.of("C#001"))));
    sql.update("UPDATE orders SET snapshot_json=NULL WHERE order_id=?", order.orderId());
    assertCode("MANUAL_REVIEW", () -> orders.read("alice", order.orderId()));
    assertEquals(0, sql.queryForObject("SELECT COUNT(*) FROM refund_requests", Integer.class));
  }

  @Test
  void apiAuthorizationAndUnknownAmountsAreRejected() throws Exception {
    var order = checkout();
    http.perform(get("/orders/" + order.orderId()).header("X-User-Id", "bob"))
        .andExpect(status().isForbidden());
    http.perform(
            post("/orders/" + order.orderId() + "/refunds")
                .header("X-User-Id", "bob")
                .header("Idempotency-Key", "refund")
                .contentType("application/json")
                .content("{\"unitIds\":[\"C#001\"]}"))
        .andExpect(status().isForbidden());
    http.perform(
            post("/orders")
                .header("X-User-Id", "alice")
                .header("Idempotency-Key", "api")
                .contentType("application/json")
                .content(
                    "{\"items\":[{\"itemId\":\"A\",\"quantity\":1}],\"couponIds\":[],\"price\":1}"))
        .andExpect(status().isBadRequest());
    http.perform(
            post("/orders")
                .header("X-User-Id", "alice")
                .header("Idempotency-Key", "api")
                .contentType("application/json")
                .content("{\"items\":[{\"itemId\":\"A\",\"quantity\":1.5}],\"couponIds\":[]}"))
        .andExpect(status().isBadRequest());
  }

  static void assertCode(String code, Runnable action) {
    assertEquals(code, assertThrows(DomainException.class, action::run).code());
  }

  static List<Object> race(Callable<?> action) throws Exception {
    var executor = Executors.newFixedThreadPool(2);
    var barrier = new CyclicBarrier(2);
    Callable<Object> contender =
        () -> {
          barrier.await(10, TimeUnit.SECONDS);
          try {
            return action.call();
          } catch (DomainException e) {
            return e;
          }
        };
    try {
      var first = executor.submit(contender);
      var second = executor.submit(contender);
      return List.of(first.get(30, TimeUnit.SECONDS), second.get(30, TimeUnit.SECONDS));
    } finally {
      executor.shutdownNow();
    }
  }
}
