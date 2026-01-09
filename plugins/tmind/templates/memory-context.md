---
name: Memory Context Template
description: Template for injecting TuringMind cloud memory into reviews
---

# Memory Context Injection

When TuringMind cloud is connected, inject this context into review agents.

## Template

```markdown
## 🧠 TuringMind Memory Context

{{#if has_memory}}

### Known False Positives (Skip These)
{{#each false_positives}}
- **Pattern:** `{{pattern}}` — dismissed {{count}} times
  Reason: {{reason}}
{{/each}}

### 🔥 Hotspot Files (Extra Scrutiny)
{{#each hotspots}}
- `{{path}}` — {{issue_count}} issues in last 30 days
{{/each}}

### 📋 Open Issues in These Files
{{#each open_issues}}
- `{{file}}:{{line}}` — {{title}} ({{status}})
  Check if this commit addresses it
{{/each}}

### 📏 Team Conventions
{{#each conventions}}
- {{this}}
{{/each}}

{{else}}

*No memory context available. Running in local mode.*

{{/if}}
```

## Usage in Review

### Step 1: Fetch Context

```bash
# Only if TURINGMIND_API_KEY is set
if [ -n "$TURINGMIND_API_KEY" ]; then
  REPO=$(git remote get-url origin 2>/dev/null | sed 's/.*github.com[:/]//' | sed 's/.git$//' || echo "local")
  API_URL="${TURINGMIND_API_URL:-https://api-dev.turingmind.ai}"
  MEMORY=$(curl -s -H "Authorization: Bearer $TURINGMIND_API_KEY" \
    "$API_URL/api/v1/code-review/context/$REPO")
fi
```

### Step 2: Inject Into Agent Prompts

Add to the beginning of each agent's context:

```
## Memory Context from TuringMind

Known false positives to SKIP:
- [list from API]

Files that are hotspots (be extra careful):
- [list from API]

Team conventions to enforce:
- [list from API]
```

### Step 3: Use in Filtering

When scoring issues, apply memory:

| Memory Signal | Score Adjustment |
|---------------|------------------|
| Matches known false positive pattern | -50 |
| File is a hotspot | +10 (flag more) |
| Violates team convention | +15 |
| Issue already open for this location | Skip (don't duplicate) |

## Example Injected Context

```markdown
## 🧠 TuringMind Memory Context

### Known False Positives (Skip These)
- **Pattern:** `config?.optional` — dismissed 12 times
  Reason: Config object is always defined in this codebase
- **Pattern:** `process.env.NODE_ENV` — dismissed 8 times
  Reason: Always set in deployment

### 🔥 Hotspot Files (Extra Scrutiny)
- `src/api/auth.ts` — 15 issues in last 30 days
- `src/db/queries.ts` — 8 issues in last 30 days

### 📋 Open Issues in These Files
- `src/api/auth.ts:45` — SQL Injection vulnerability (open)
  Check if this commit addresses it

### 📏 Team Conventions
- Always use parameterized queries for database access
- Prefer optional chaining (?.) over explicit null checks
- All API routes must validate input with zod
- Error messages must not expose stack traces
```

## No Memory Fallback

If cloud is not connected:

```markdown
## 🧠 Memory Context

*Running in local mode — no cloud memory available.*

To enable memory features:
1. Sign up at https://turingmind.ai
2. Get your API key
3. Run: `/config set TURINGMIND_API_KEY your_key`
```

## Privacy Note

Memory context is fetched from YOUR data:
- Only patterns YOU dismissed are returned
- Only YOUR repo's hotspots are shown
- Only YOUR team's conventions apply

No cross-organization data is ever shared.

