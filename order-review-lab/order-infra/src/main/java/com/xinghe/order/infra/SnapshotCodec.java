package com.xinghe.order.infra;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.nio.charset.StandardCharsets;
import java.security.*;
import java.util.HexFormat;
import org.springframework.stereotype.Component;

@Component
public final class SnapshotCodec {
  private final ObjectMapper mapper;

  public SnapshotCodec(ObjectMapper mapper) {
    this.mapper = mapper;
  }

  public String encode(Object value) {
    try {
      return mapper.writeValueAsString(value);
    } catch (JsonProcessingException e) {
      throw new IllegalStateException("Cannot encode snapshot", e);
    }
  }

  public <T> T decode(String json, Class<T> type) {
    try {
      return mapper.readValue(json, type);
    } catch (JsonProcessingException e) {
      throw new IllegalStateException("Cannot decode snapshot", e);
    }
  }

  public String hash(Object value) {
    return hashText(encode(value));
  }

  public String hashText(String value) {
    try {
      return HexFormat.of()
          .formatHex(
              MessageDigest.getInstance("SHA-256").digest(value.getBytes(StandardCharsets.UTF_8)));
    } catch (NoSuchAlgorithmException e) {
      throw new IllegalStateException(e);
    }
  }
}
