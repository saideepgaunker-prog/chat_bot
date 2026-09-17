# Slack & Webhook Integrations

## Overview
Receive real-time notifications for repository events, build completions, security scan findings, and agent actions directly in your team's Slack channels.

## Location & Route
Navigate to: **Settings > Integrations > Webhooks > Slack** (`/settings/integrations/webhooks/slack`).
*Required Permission:* `admin`.

## Setup Instructions
1. Navigate to `/settings/integrations/webhooks/slack`.
2. Click **Add Slack Webhook**.
3. Select your target Slack workspace and channel (e.g. `#dev-alerts-payments`).
4. Select event subscriptions:
   - `Build Failures`
   - `Critical Security Alerts`
   - `Agent PR Reviews`
   - `Deployment State Changes`
5. Test the connection with the **Send Test Ping** button.
