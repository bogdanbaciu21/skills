# Public Table Migration Writeup Fixture

A content site had a mixture of canonical content tables, legacy admin grids,
and unwrapped HTML tables. The reusable writeup describes the migration in
generic terms only:

- canonical table class
- canonical wrapper class
- legacy admin allowlist
- no-new-debt baseline
- browser geometry checks for wide tables and admin grids

It deliberately omits customer names, local paths, production domains, emails,
hostnames, tokens, analytics IDs, exact defect counts, and commit hashes.
