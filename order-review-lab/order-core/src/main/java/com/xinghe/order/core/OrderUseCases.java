package com.xinghe.order.core;

import static com.xinghe.order.core.Models.*;

public interface OrderUseCases {
  PricingResult quote(String owner, CheckoutRequest request);

  OrderResult checkout(String owner, String key, CheckoutRequest request);

  OrderDetail read(String owner, String orderId);

  RefundResult refund(String owner, String orderId, String key, RefundRequest request);

  SplitResult split(String owner, String orderId, String key, SplitRequest request);
}
