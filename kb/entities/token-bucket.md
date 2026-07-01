---
type: Reference
title: Token Bucket
description: A rate-limiting algorithm that grants requests while tokens are available.
tags: [throughput, algorithm]
---

# Token Bucket
The token bucket algorithm adds tokens at a fixed rate up to a capacity; each request consumes a token. It allows short bursts while enforcing an average rate. It is a standard implementation of [rate limiting](/concepts/rate-limiting.md).

## Related
* [Backpressure](/concepts/backpressure.md)
* [Caching](/concepts/caching.md)
* [Rate Limiting](/concepts/rate-limiting.md)
