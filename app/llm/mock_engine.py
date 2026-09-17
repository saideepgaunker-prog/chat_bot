import asyncio
import re
from typing import AsyncGenerator, Dict, Any, List, Optional
from app.llm.base import BaseLLMClient

class MockContextualEngine(BaseLLMClient):
    async def generate_stream(
        self,
        prompt: str,
        system_instruction: str = "",
        context_data: Dict[str, Any] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        ctx = context_data or {}
        intent = ctx.get("intent", "general")
        recalled_memories = ctx.get("recalled_memories", [])
        
        if intent == "feature_locator":
            feat = ctx.get("matched_feature")
            if feat:
                name = feat.get("name", "Feature")
                desc = feat.get("description", "")
                perm = feat.get("permission_required", "developer")
                crumbs = " > ".join(feat.get("breadcrumbs", []))
                response_text = f"""You can find **{name}** at `{crumbs}`.

**Summary:** {desc}

*Required Permission:* `{perm}`

Click the action card below to jump directly to this view."""
            else:
                response_text = "I searched the Developer Control Tower catalog but could not find an exact feature match."

        elif intent == "feature_explainer":
            doc = ctx.get("matched_doc")
            feat = ctx.get("matched_feature")
            if doc:
                title = doc.get("title", "Documentation")
                body = doc.get("text", "")
                response_text = f"""### {title}

{body}"""
            elif feat:
                crumbs = " > ".join(feat.get("breadcrumbs", []))
                name = feat.get("name", "")
                desc = feat.get("description", "")
                response_text = f"""### {name}

{desc}

**Path:** `{crumbs}`"""
            else:
                response_text = "This feature provides configuration toggles and automated monitoring for your codebase within the Developer Control Tower."

        elif intent == "project_telemetry":
            telemetry = ctx.get("telemetry")
            if telemetry:
                repo_id = str(telemetry.get("repo_id", "repo"))
                health = str(telemetry.get("health_score", "100"))
                branch = str(telemetry.get("active_branch", "main"))
                agents = telemetry.get("agents_summary", {})
                events = telemetry.get("recent_events", [])
                
                cr_stat = agents.get("code_reviewer", {}).get("status", "idle").upper()
                ci_stat = agents.get("ci_cd_orchestrator", {}).get("status", "idle").upper()
                ci_build = str(agents.get("ci_cd_orchestrator", {}).get("last_build", "N/A"))
                sec_stat = agents.get("security_scanner", {}).get("status", "idle").upper()
                sec_cve = str(agents.get("security_scanner", {}).get("cve_count", 0))

                events_md = ""
                for ev in events[:3]:
                    agent_name = ev.get("agent_type", "").replace("_", " ").title()
                    status_emoji = "✅" if ev.get("status") == "success" else ("⚠️" if ev.get("status") == "warning" else "❌")
                    summary = ev.get("summary", "")
                    events_md += f"- **{status_emoji} {agent_name}**: {summary}\n"

                response_text = f"""### 📡 Project Status for `{repo_id}`

- **Health Score:** `{health}/100`
- **Active Branch:** `{branch}`
- **Code Reviewer:** `{cr_stat}`
- **CI/CD Pipeline:** `{ci_stat}` (Build {ci_build})
- **Security Scanner:** `{sec_stat}` ({sec_cve} CVEs)

#### 🔍 Recent Multi-Agent Events:
{events_md}"""
            else:
                response_text = "I could not find real-time telemetry records for the specified repository."

        elif intent == "cross_session_memory":
            pref_facts = [m.get("fact_text", "") for m in recalled_memories if m.get("memory_type") == "preference"]
            pref_str = "\n".join(["- " + f for f in pref_facts if f]) if pref_facts else "- Preferred language: TypeScript, Preferred repo: repo-analytics"
            response_text = f"""I remember your preferences from our previous sessions:
{pref_str}

Here is the tailored TypeScript hook for your repository:

```typescript
// Custom Control Tower Agent Hook for repo-analytics
export async function onAgentEvent(event: AgentTriggerEvent): Promise<void> {{
  console.log('[Agent Hook] Event triggered:', event.type);
  if (event.status === 'failed') {{
    await notifySlack('#dev-alerts', event.summary);
  }}
}}
```"""
        else:
            response_text = """Hello! I am your **Developer Control Tower AI Assistant**.

1. **Locate Features & Settings**: Ask *'Where do I configure Slack webhooks?'* or *'Where are branch rules?'*
2. **Explain Views & Features**: Ask *'What does Auto-Rollback Threshold do?'*
3. **Synthesize Project Telemetry**: Ask *'What happened in repo-payments today?'*
4. **Remember Preferences**: I automatically retain your working repositories and tech preferences across sessions!"""

        words = re.split(r"(\s+)", response_text)
        for w in words:
            yield {"type": "token", "delta": w}
            await asyncio.sleep(0.01)
