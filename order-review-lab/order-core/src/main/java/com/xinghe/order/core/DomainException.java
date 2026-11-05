package com.xinghe.order.core;

public final class DomainException extends RuntimeException {
  private final String code;

  public DomainException(String code, String message) {
    super(message);
    this.code = code;
  }

  public String code() {
    return code;
  }

  public static void require(boolean condition, String code, String message) {
    if (!condition) throw new DomainException(code, message);
  }
}
