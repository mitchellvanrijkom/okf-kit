---
type: Concept
title: Rate Limiting
description: Bounding how many requests a client may make in a time window.
tags: [reliability, throughput]
---

# Rate Limiting
Rate limiting protects a service from overload by capping request frequency. Common algorithms are token bucket and leaky bucket. It pairs with [retries](/concepts/retries.md) and [backpressure](/concepts/backpressure.md) to keep a system stable under load.

## Related
* [Backpressure](/concepts/backpressure.md)
* [Caching](/concepts/caching.md)
* [Idempotency](/concepts/idempotency.md)
* [Retries](/concepts/retries.md)
* [Token Bucket](/entities/token-bucket.md)
