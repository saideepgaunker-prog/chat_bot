# Auto-Rollback Thresholds & Reliability Policies

## Overview
Auto-Rollback protects production environments by automatically reverting a deployment if newly released code causes anomaly spikes in error rate, latency, or unhandled exceptions.

## Location & Route
Navigate to: **Pipelines > Reliability > Auto-Rollback Policies** (`/pipelines/rollback-policies`).
*Required Permission:* `maintainer`.

## Configurable Thresholds
1. **HTTP 5xx Error Rate Threshold**: Default `> 1.5%` over a 3-minute sliding window. If breached, the orchestrator initiates an immediate traffic shift back to the prior stable release replica.
2. **p99 Latency Breach**: Default `> 450ms` (or 200% above baseline).
3. **Health Check Failure**: Default `3 consecutive failed probes` within 30 seconds.
4. **Canary Step Evaluation**: Evaluates 10% canary traffic for 5 minutes before progressing to 100%.

## What Does 'Auto-Rollback Threshold' Do?
When you adjust the Auto-Rollback Threshold, you define the sensitivity of the automated safety trigger. Setting it too tight (<0.5%) may cause false rollbacks during brief network blips, while setting it too loose (>5%) risks exposing users to prolonged outages.
