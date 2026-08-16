# Known Failure Modes

- If the Render service is completely unavailable, incoming webhook events cannot be received until the service comes back online. The mock API may retry delivery, but there is no external durable queue in front of the application.

- If MongoDB Atlas is unavailable while a webhook is being received, the event cannot be persisted and the webhook request may fail. This means durable event processing depends on MongoDB availability.

- If the process is restarted while an in-memory worker operation is actively executing, that operation may be interrupted. Jobs already persisted in MongoDB remain available for processing, but the currently executing operation may need to be retried.

- The worker deliberately spaces outbound DM requests to remain below the mock API's rolling rate limit. During a large burst such as 500 comments in 10 seconds, matching jobs are persisted and queued, but delivery can take substantially longer because of the rate limit.

- If a webhook is forged with an invalid X-PseudoGram-Signature, the request is rejected with HTTP 401. This is intentional, but it means a correctly formatted event with an incorrect signature will not be processed.

- Duplicate protection relies on MongoDB unique indexes. If the database is unavailable, duplicate protection cannot be evaluated until the database becomes available again.