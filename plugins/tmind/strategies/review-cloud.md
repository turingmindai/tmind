---
allowed-tools: Bash(git diff:*), Bash(git status:*), Bash(git log:*), Bash(git blame:*), Bash(git show:*), Bash(curl:*), Bash(~/.turingmind/upload_review.sh:*), turingmind_validate_auth, turingmind_upload_review, turingmind_get_context
description: Quick code review for uncommitted local changes (Cloud Mode)
---

Quick code review for uncommitted changes. Fast, focused on critical issues.
Running in **Cloud Mode** (API key detected).

## Step 0: Initialize TuringMind Cloud

Fetch memory context from TuringMind cloud.

### Option A: MCP Tool (Preferred)

```
turingmind_get_context({
  repo: "owner/repo"  // from git remote
})
```

Returns: open issues, hotspot files, team conventions, false positive patterns.

### Option B: Curl Fallback

```bash
REPO=$(git remote get-url origin 2>/dev/null | sed 's/.*github.com[:/]//' | sed 's/.git$//' || echo "local")
curl -s -H "Authorization: Bearer $TURINGMIND_API_KEY" \
  "${TURINGMIND_API_URL:-http://localhost:3000}/api/v1/code-review/context/$REPO"
```

- **API details:** See `@agents/cloud-sync.md`
- **What gets injected:** See `@templates/memory-context.md`

Memory improves reviews by skipping known false positives, flagging hotspot files, and enforcing team conventions.

## Step 1: Gather Context (Haiku Agent)

Detect what needs to be reviewed:

```
1. Run `git status` and `git diff` / `git diff --staged`
2. If no changes → inform user and stop
3. Extract:
   - Files changed (list)
   - Languages detected (from extensions)
   - Line counts (additions/deletions)
   - Has CLAUDE.md? (root or in changed directories)
```

## Step 2: Load Agents (Progressive)

Only load agents relevant to detected context:

| Condition | Load Agent |
|-----------|------------|
| Always | `@agents/bugs.md` |
| Always | `@agents/security.md` |
| CLAUDE.md exists | `@agents/compliance.md` |
| `.ts/.tsx/.js/.jsx` files | `@agents/language-typescript.md` |
| `.py` files | `@agents/language-python.md` |

See `@agents/index.md` for full routing logic.

## Step 3: Run Review (Parallel Sonnet Agents)

Launch loaded agents in parallel. Each agent:
1. Reads full file context for changed files
2. Analyzes only the diff (not pre-existing code)
3. Returns structured issues with **diff-style fixes**

Output format per agent (see `@agents/bugs.md` for example):
```markdown
### 🐛 {{issue_title}}
**Location:** `{{file}}:{{line}}`
**Confidence:** {{score}}/100

**Problem:** {{reason}}

**Suggested Fix:**
```diff
- {{old_code}}
+ {{new_code}}
```
```

## Step 4: Score & Filter (Haiku Agents)

Score each issue 0-100 using criteria from `@templates/false-positive-rules.md`:

| Factor | Points |
|--------|--------|
| In the diff (new code) | +20 |
| Would cause failure | +30 |
| In CLAUDE.md rules | +20 |
| Senior engineer would flag | +20 |
| Has ignore comment | -50 |

If cloud connected, apply memory-based adjustments (see `@templates/false-positive-rules.md#memory-based-scoring`).

**Filtering:**
- Filter issues with score < 80
- Track filtered count by reason

## Step 5: Present Results

Format output using `@templates/output-format.md`:

```
## Code Review

**Summary:** Reviewed X files, Y lines changed

| Found | Reported | Filtered |
|-------|----------|----------|
| total | ≥80 score | <80 score |

### Critical (95-100) 🔴
[Issues with diff-style fixes]

### Warning (80-94) 🟠  
[Issues with diff-style fixes]

### Filtered Issues 🔇
[Count by reason, expandable details]
```

## Step 6: Upload to Cloud

Upload review results to TuringMind cloud for analytics and memory.

### Option A: MCP Tool (Preferred)

If TuringMind MCP server is configured, use the type-safe `turingmind_upload_review` tool:

```
turingmind_upload_review({
  repo: "owner/repo",           // from git remote
  branch: "feature/branch",     // from git branch
  commit: "abc123",             // from git rev-parse
  review_type: "quick",
  issues: [
    {
      title: "Issue title from Steps 3-4",
      severity: "critical|high|medium|low",
      category: "security|bug|compliance",
      file: "path/to/file.ts",
      line: 42,
      description: "Detailed explanation",
      confidence: 95
    }
  ],
  summary: {
    critical: 0,    // count from your analysis
    high: 1,
    medium: 2,
    low: 0
  }
})
```

### Option B: Curl Fallback

If MCP is not available, use curl directly:

```bash
# Get repo info
REPO=$(git remote get-url origin 2>/dev/null | sed 's/.*github.com[:/]//' | sed 's/.git$//' || basename "$(pwd)")
BRANCH=$(git branch --show-current 2>/dev/null || echo "main")
COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")

# Upload (field aliases supported: findings→issues, results→issues)
source ~/.turingmind/config 2>/dev/null
curl -s -X POST "${TURINGMIND_API_URL:-http://localhost:3000}/api/v1/code-review/reviews" \
  -H "Authorization: Bearer $TURINGMIND_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"context\": {\"repo\": \"$REPO\", \"branch\": \"$BRANCH\", \"commit\": \"$COMMIT\", \"review_type\": \"quick\"},
    \"issues\": [...],
    \"summary\": {\"critical\": 0, \"high\": 1, \"medium\": 2, \"low\": 0}
  }"
```

### Notes

- MCP provides type-safe schema validation before sending
- Curl fallback works everywhere but is more error-prone
- If upload fails, the review is still valid locally
- Cloud sync is optional but enables memory features
