# Performance Model

Performance requirements are architectural bounds first and wall-clock
measurements second. Timing varies by machine; complexity, allocation, queue,
and concurrency behavior must remain deterministically testable.

## Required Bounds

- Snapshot evolution shallow-copies only changed aggregate tuples. Existing
  immutable messages, parts, context, catalog, and metric values retain object
  identity.
- A durable change with no history append or replacement reuses the exact
  history tuple and its private history proof. An append validates and extends
  only the appended messages, while retaining exact cross-history tool-call id
  evidence and a rolling 32-byte content digest. Tuple growth still copies
  `O(h + a)` immutable references; it does not revisit message content.
- Public `RunSnapshot` construction, wire decoding, and explicit history
  replacement are trust boundaries: each validates and digests the complete
  resulting history in `O(h)`. Internal proven evolution has no public bypass
  flag or caller-supplied proof.
- Trusted immutable values are passed directly. Runtime does not serialize and
  reconstruct them as a copying mechanism.
- Wire validation happens once at each trust boundary. Commit never re-freezes
  or reconstructs domain values. The default ephemeral repository reuses the
  snapshot's 32-byte history digest and explicitly hashes only the remaining
  checkpoint fields. It retains one 32-byte fingerprint per id and never
  retains historical snapshots.
- Result-only invocation uses a null observation sink and constructs no
  `RunEvent` values.
- The observation queue is created only when `events()` selects event mode and
  is released when that invocation's sole event iterator finishes.
- An invocation closes and drains its live control channel at termination; it
  retains no uncommitted controls, releases its execution driver, and discards
  later submissions.
- An event-stream invocation retains at most the configured bounded number of
  lossy model delta and tool progress events, defaulting to 1024. Lifecycle and
  checkpoint events remain lossless.
- Tool registration compiles input/output schemas once. Registration is average
  `O(1)` after compilation; catalog opening is `O(n)` and yields one immutable
  invocation snapshot.
- Binding reuses the immutable call, spec, and implementation reference.
- A selected tool batch creates at most one task per member and gates active
  invocations with `max_tool_concurrency`.
- Model streaming has one accumulator in the provider adapter. Kernel forwards
  deltas and consumes one complete response; it does not rebuild another.
- The default ephemeral repository retains current authoritative state and the
  information required for idempotent commit, not every historical checkpoint.
- A diagnostic trace stores one entry per event, including one compact entry per
  committed checkpoint, and grows `O(e)`, not with repeated history snapshots
  or derived summaries.
- Kernel creates no worker thread pool. All potentially blocking ports are
  async and cancellation-safe.
- Every source function has McCabe complexity at most 10.

These bounds require identity, allocation, queue-capacity, cancellation, and
complexity tests in addition to behavior tests.

The ephemeral repository's new-id fingerprint cost is `O(c)`, where `c` is the
non-history checkpoint content; incorporating history is `O(1)` through the
already-proven digest. The digest is domain-separated and length-prefixed, and
its JSON mapping keys are sorted with null, boolean, integer, float, string,
array, and object encoded as distinct types. This preserves content-exact
retries without repeated `O(history)` hashing or the `O(sum(history))` retained
memory of a checkpoint ledger. Durable adapters may reuse an equivalent backend
content checksum.

## Runtime Smoke Benchmark

Run from the repository root with the uv-selected interpreter:

```bash
uv run python benchmarks/runtime_smoke.py
```

The benchmark compares identical asynchronous tools under serial and
bounded-parallel scheduling. It verifies:

- the configured active-concurrency ceiling;
- durable output ordered by model call position;
- one atomic checkpoint for a parallel batch;
- at least a 2x parallel speedup for the controlled workload;
- no detached tool tasks after completion or cancellation.

It reports timings for the current machine. The speedup ratio is a regression
signal, not a production latency promise.

## Additional Regression Cases

Deterministic tests cover:

- result-only execution allocates no event queue;
- terminated invocations retain no queued controls and discard new ones;
- a stalled event consumer cannot grow lossy buffers past their bound;
- a large history update preserves identity for unchanged messages;
- large tool schemas are compiled once per registration;
- repeated checkpoint retries do not grow ephemeral repository history;
- trace size increases linearly across long runs;
- deadline cleanup settles all model/tool tasks within fixed grace.

## Non-Goals

Kernel does not hide network latency with unbounded queues, background threads,
speculative side effects, or retries. Provider transports and durable
repositories own connection pooling, batching, and backend-specific tuning.
