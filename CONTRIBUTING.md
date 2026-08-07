# Contributing

Codemium follows the same principle it asks of coding agents: make the smallest justified change.

Before submitting a change:

1. explain the current behavior or limitation;
2. keep unrelated cleanup out of the diff;
3. add or update tests for changed behavior;
4. run `sh plugins/codemium/scripts/verify.sh`;
5. avoid new dependencies unless the existing standard library/project stack cannot reasonably solve the problem;
6. do not claim token savings without measured benchmark evidence.
