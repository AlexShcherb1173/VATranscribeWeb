# Activation commit point and release cleanup

`activate-release.sh` runs `deploy.sh` as a foreground command under
`set -Eeuo pipefail`. Migration, stateless replacement, API readiness, public
smoke and monitoring smoke must all return successfully before the activator
sets `RELEASE_COMMITTED=true`, clears `ROTATED`, and logs `RELEASE_COMMIT_POINT`.
The shell call is deliberately not wrapped in an `if`/`||` that would disable
errexit within the activation transaction.

Before commit, an error after rotation still collects bounded failure evidence,
preserves the failed candidate, restores the prior release and propagates the
original status. Database downgrades are not automatic.

After commit, cleanup failure returns nonzero and logs
`POST_COMMIT_PRUNE_FAILED` with the affected path/category and
`RELEASE_POST_COMMIT_FAILURE ... candidate_active=true rollback_performed=false`.
The active healthy candidate stays active. A failed workflow alone therefore
does not imply rollback: operators must distinguish these markers from a
pre-commit failure. `POST_COMMIT_PRUNE_COMPLETE` is emitted only if all selected
previous-release cleanup succeeds. No automatic retry is implied.

## Runtime and evidence boundaries

Certbot state belongs in the validated persistent sibling `CERTBOT_ROOT`
(default `/opt/vatranscribe/certbot`). Activation installs `infra/certbot` as a
symlink to that location before rotating the candidate. Compose's relative
Certbot bind mounts consequently resolve to persistent state. Removing an old
release unlinks its symlink; it does not traverse the external target.

Historical real `infra/certbot` directories are preserved for separate review,
and cleanup reports `legacy_certbot_state`. F21 encountered root-owned mutable
state in such a historical release after both smoke checks had passed. This
guard avoids treating legacy certificate material as disposable release data;
it does not migrate or change that material's ownership or permissions.

Previous releases are enumerated one level beneath the canonical project
parent and sorted by descending mtime, preserving the configured retention
count (default 3, accepted range 1–20). Deletion rechecks the immediate parent,
restricted basename, directory type and canonical identity; top-level symlinks
are excluded and nested symlinks are not followed. Inspection rejects mount
points within the target (including bind mounts on the same filesystem),
without descending through them. Each non-symlink entry is probed explicitly;
a directory is enumerated one level at a time only after its probe returns
util-linux status **32** (authoritatively not a mountpoint). Status **0** rejects
the mount boundary. Status **1**, execution failures (including unavailable
tooling), and every other unexpected status report `MOUNT_PROBE_ERROR` with
the affected path and `probe_status`, and return nonzero. Probe status is not
inferred from a `find -exec` predicate. Enumeration errors also fail closed.
Recursive deletion is never attempted for a release whose inspection is
indeterminate; post-commit failure leaves the candidate active without rollback.
GNU rm is additionally restricted to one filesystem and
refuses a target on a different filesystem from its parent.
The activation lock coordinates deployment writers; these checks are not a
security boundary against a privileged actor concurrently replacing mounts or
mutating the release filesystem.

`app.broken.*` and `release-evidence` are retained without automatic pruning.
This intentionally requires separate capacity management and an explicitly
reviewed forensic-retention policy. Existing backup creation and backup
retention scripts are unchanged. Post-commit failures preserve remaining
filesystem evidence and their path/status diagnostics in the workflow log;
they do not create a misleading activation-failure snapshot of the healthy
candidate. Partial deletion of an ordinary previous release remains possible
when an unanticipated filesystem error occurs.

## Local regression coverage

`tests/security/test_release_commit_boundary.py` executes the real activator,
deployment readiness gate and smoke scripts on temporary Linux release trees.
Docker and HTTP are faked. Run as an unprivileged user so the protected-directory
case exercises actual kernel permission denial. The Backend CI filesystem test
step includes this suite. No production access is required.
