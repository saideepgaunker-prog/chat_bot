# Preview Environments & Ephemeral Staging

## Overview
Preview Environments are isolated, short-lived deployments created automatically for every active Pull Request. They allow developers, designers, and product leads to test live features before merging into main.

## Location & Route
Navigate to: **Repositories > [Your Repo] > Deployments > Preview Environments** (`/repos/:repoId/deployments/previews`).
*Required Permission:* `developer`.

## Key Features
1. **Automatic Lifecycle**: Spun up when a PR opens or receives new commits; automatically decommissioned 30 minutes after PR merge or closure.
2. **Dynamic URL Allocation**: Each PR receives an isolated subdomain (e.g. `https://preview-pr142.devtower.internal`).
3. **Ephemeral Seed Data**: Pre-loaded with sanitized staging fixtures to enable realistic end-to-end testing.
4. **Environment Variables Override**: Custom mock variables can be injected per preview environment without affecting production.
