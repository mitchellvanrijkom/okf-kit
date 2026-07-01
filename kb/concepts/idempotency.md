---
type: Concept
title: Idempotency
description: An operation that can be applied many times without changing the result beyond the first.
tags: [reliability, retries, data]
---

# Idempotency
An operation is idempotent when running it repeatedly yields the same result as running it once. It is essential for safe [retries](/concepts/retries.md): a retried request must not create duplicates or corrupt state. A common technique is an idempotency key that de-duplicates repeated requests.

## Related
* [Retries](/concepts/retries.md)
* [Rate Limiting](/concepts/rate-limiting.md)
