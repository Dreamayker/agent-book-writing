package com.xinghe.order.infra;

import java.util.List;
import org.apache.ibatis.annotations.*;

@Mapper
public interface OrderMapper {
  record OrderRow(
      String orderId,
      String rootOrderId,
      String ownerId,
      String snapshotJson,
      String snapshotHash,
      long payableCents,
      long refundedCents,
      boolean splitDone) {}

  record UnitRow(String unitId, long payableCents, boolean refunded) {}

  record IdempotencyRow(String fingerprint, String responseJson) {}

  @Insert(
      "INSERT INTO principal_locks(owner_id) VALUES(#{owner}) ON DUPLICATE KEY UPDATE owner_id=VALUES(owner_id)")
  void ensurePrincipal(String owner);

  @Select("SELECT owner_id FROM principal_locks WHERE owner_id=#{owner} FOR UPDATE")
  String lockPrincipal(String owner);

  @Select("SELECT * FROM orders WHERE order_id=#{id}")
  OrderRow find(String id);

  @Select("SELECT * FROM orders WHERE order_id=#{id} FOR UPDATE")
  OrderRow lock(String id);

  @Insert(
      "INSERT INTO orders(order_id,root_order_id,owner_id,snapshot_json,snapshot_hash,payable_cents) VALUES(#{orderId},#{rootOrderId},#{ownerId},#{snapshotJson},#{snapshotHash},#{payableCents})")
  void insert(OrderRow order);

  @Insert(
      "INSERT INTO order_units(root_order_id,unit_id,payable_cents) VALUES(#{root},#{unit},#{amount})")
  void insertUnit(String root, String unit, long amount);

  @Insert("INSERT INTO order_memberships(order_id,unit_id) VALUES(#{order},#{unit})")
  void membership(String order, String unit);

  @Select(
      "SELECT u.unit_id,u.payable_cents,u.refunded FROM order_units u JOIN order_memberships m ON m.unit_id=u.unit_id WHERE m.order_id=#{order} AND u.root_order_id=#{root} ORDER BY u.unit_id")
  List<UnitRow> units(String root, String order);

  @Update(
      "UPDATE order_units SET refunded=TRUE WHERE root_order_id=#{root} AND unit_id=#{unit} AND refunded=FALSE")
  int markRefunded(String root, String unit);

  @Update(
      "UPDATE orders SET refunded_cents=refunded_cents+#{amount} WHERE order_id=#{root} AND refunded_cents+#{amount}<=payable_cents")
  int increaseRefund(String root, long amount);

  @Update("UPDATE orders SET split_done=TRUE WHERE order_id=#{id} AND split_done=FALSE")
  int markSplit(String id);

  @Insert("INSERT INTO coupon_uses(coupon_id,order_id) VALUES(#{coupon},#{order})")
  void consumeCoupon(String coupon, String order);

  @Select("SELECT COUNT(*) FROM coupon_uses WHERE coupon_id=#{coupon}")
  int couponConsumed(String coupon);

  @Select(
      "SELECT fingerprint,response_json FROM idempotency_records WHERE owner_id=#{owner} AND operation_id=#{operation} AND request_key=#{key}")
  IdempotencyRow idempotency(String owner, String operation, String key);

  @Insert(
      "INSERT INTO idempotency_records(owner_id,operation_id,request_key,fingerprint,response_json) VALUES(#{owner},#{operation},#{key},#{fingerprint},#{response})")
  void saveIdempotency(
      String owner, String operation, String key, String fingerprint, String response);

  @Insert(
      "INSERT INTO refund_requests(refund_id,order_id,root_order_id,amount_cents,unit_ids,snapshot_hash) VALUES(#{id},#{order},#{root},#{amount},#{units},#{hash})")
  void saveRefund(String id, String order, String root, long amount, String units, String hash);
}
