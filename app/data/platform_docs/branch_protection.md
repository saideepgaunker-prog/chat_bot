# Branch Protection Rules & Merge Policies

## Overview
Branch protection rules safeguard critical code branches (such as `main`, `production`, and `release/*`) against unauthorized direct commits, unreviewed changes, or broken builds.

## Location & Route
Navigate to: **Repositories > [Your Repo] > Settings > Branch Rules** (`/repos/:repoId/settings/branches`).
*Required Permission:* `maintainer` or `admin`.

## Key Capabilities
1. **Required Approvals**: Enforce a minimum number of peer code reviews (e.g. 1 or 2 approvals) before a pull request can be merged.
2. **AI Agent Verification Gate**: Require automated agents (Code Reviewer Agent and Security Scanner Agent) to emit a `PASS` status check prior to merge.
3. **Linear History & Squash Merges**: Disallow non-fast-forward merge commits to maintain a clean git history.
4. **Force Push Restriction**: Completely disallow `git push --force` on protected branches.

## Safe Defaults
For production microservices, enable:
- Minimum 1 Senior Approval
- Mandatory CI/CD Pipeline Pass (`Build & Test Matrix`)
- Mandatory Security Scan Gate (0 Critical/High CVEs)
