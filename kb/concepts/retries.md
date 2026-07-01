---
type: Concept
title: Retries
description: Re-attempting a failed operation, usually with backoff, to handle transient errors.
tags: [reliability, retries]
---

# Retries
Retries recover from transient failures. They only work safely when the target is idempotent (see [idempotency](/concepts/idempotency.md)). Use exponential backoff with jitter to avoid overwhelming a struggling service, and cap the number of attempts. See also [rate limiting](/concepts/rate-limiting.md).

## Related
* [Idempotency](/concepts/idempotency.md)
* [Rate Limiting](/concepts/rate-limiting.md)
