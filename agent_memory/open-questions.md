# open-questions

Threads raised in prior sessions that were never fully resolved.

## NAS ↔ GitHub divergence

The user described the authoritative git repo as living on a NAS as a
bare repo, with the NAS "ahead" of this local clone. However, this
local clone's `HEAD` matches `origin/main` on GitHub exactly. So either:

1. The NAS is also ahead of GitHub (needs pull-down + push), or
2. The NAS claim was mistaken and everything is already in sync.

Not verified. To resolve: add the NAS mount path as a git remote,
`git fetch`, and compare refs.

## GitHub origin ownership

`origin` is configured and SSH auth succeeds. User expressed uncertainty
early on about whether they actually had a GitHub account. If the question
resurfaces, `ssh -T git@github.com` prints the authenticated username.
