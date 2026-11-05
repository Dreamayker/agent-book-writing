# Order Review Lab

“星河优选”优惠券叠加与退款案例的可运行教学工程。业务契约见 [ADR-001](docs/ADR-001-business-contract.md)，总体迁移方案见 [规划](../docs/order-case-migration-plan.md)。

## 运行

需要 JDK 17、Docker 和可访问 Maven Central/Docker 镜像仓库的网络。Maven Wrapper 固定 Maven 3.9.14；MySQL Testcontainers 集成测试缺少 Docker 时直接失败，不静默跳过。

```bash
cd order-review-lab
./mvnw -B -ntp verify
docker compose up -d --wait
java -jar order-api/target/order-api-1.0.0-SNAPSHOT-exec.jar
```

macOS 若尚未配置 Java，可用已安装 JDK 的实际路径设置 `JAVA_HOME`。非默认 Docker socket 需设置 `DOCKER_HOST`，例如 OrbStack 的 `unix://$HOME/.orbstack/run/docker.sock`。Testcontainers 使用 Docker API 1.44。

服务只监听 `127.0.0.1:8081`，数据库只映射 `127.0.0.1:3307`。Compose 内密码是本地虚构数据的固定开发口令。

```bash
curl -s http://127.0.0.1:8081/orders \
  -H 'Content-Type: application/json' -H 'X-User-Id: alice' -H 'Idempotency-Key: checkout-1' \
  -d '{"items":[{"itemId":"A","quantity":1},{"itemId":"B","quantity":1},{"itemId":"C","quantity":1}],"couponIds":["order5000","new2000"]}'
```

返回订单 ID、33000 分实付及快照哈希；使用返回的 ID 调用 `POST /orders/{id}/refunds`，请求 `{"unitIds":["C#001"]}`，正确退款为 6600 分。接口还包括试算 `/orders/quote`、查询 `/orders/{id}` 和拆单 `/orders/{id}/splits`。所有写操作使用 `Idempotency-Key`；身份头仅供教学。

## 目录与复现

- `order-core/`：无框架依赖的计价、分摊与快照退款计算。
- `order-infra/`：MyBatis、MySQL 事务、固定业务适配器及快照序列化。
- `order-api/`：Spring Boot 启动与 HTTP 接口。
- `order-test/`：真实 MySQL 的集成、并发和 API 测试。
- `fixtures/`：固定业务数据。
- `book-assets/`：独立缺陷补丁与运行证据。
- `evaluation/`、`policies/`：案例清单与订单风险规则，由已有 Python 评审系统读取。

本工程是基于案例说明构建的教学系统，遗留版本和故障均为构造样本。正确基线不调用真实支付、退款或外部会员系统。
