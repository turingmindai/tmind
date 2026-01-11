---
allowed-tools: Bash(git diff:*), Bash(git status:*), Bash(git log:*), Bash(git blame:*), Bash(git show:*), Bash(curl:*), Bash(~/.turingmind/upload_review.sh:*), Read, turingmind_validate_auth, turingmind_upload_review, turingmind_get_context, turingmind_submit_feedback
description: Quick code review for uncommitted local changes (Cloud Mode)
---

Quick code review for uncommitted changes. Fast, focused on critical issues.
Running in **Cloud Mode** (API key detected).

## Step 0: Fetch Memory Context

Get memory context from TuringMind cloud to improve review quality.

### If MCP tools available:

```
turingmind_get_context({
  repo: "owner/repo"  // extract from: git remote get-url origin
})
```

### Fallback (curl):

```bash
source ~/.turingmind/config 2>/dev/null
REPO=$(git remote get-url origin 2>/dev/null | sed 's/.*github.com[:/]//' | sed 's/.git$//' || echo "local")
curl -s -H "Authorization: Bearer $TURINGMIND_API_KEY" \
  "${TURINGMIND_API_URL:-https://api.turingmind.ai}/api/v1/code-review/context/$REPO"
```

**What this returns:**
- Known false positive patterns (skip these)
- Hotspot files (give extra scrutiny)
- Team conventions (enforce these)
- Recent open issues (check if this commit fixes any)

Use this context in Steps 3-4 to improve review accuracy. If fetch fails, continue without memory context.

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
| In memory's false positive patterns | -40 |
| In hotspot file | +10 |

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

### If MCP tools available:

```
turingmind_upload_review({
  repo: "owner/repo",
  branch: "feature/branch",
  commit: "abc123",
  review_type: "quick",
  issues: [
    {
      title: "Issue title",
      severity: "critical",
      category: "security",
      file: "path/to/file.ts",
      line: 42,
      description: "Detailed explanation",
      confidence: 95
    }
  ],
  summary: { critical: 0, high: 1, medium: 2, low: 0 }
})
```

### Fallback (curl):

```bash
source ~/.turingmind/config 2>/dev/null
REPO=$(git remote get-url origin 2>/dev/null | sed 's/.*github.com[:/]//' | sed 's/.git$//' || basename "$(pwd)")
BRANCH=$(git branch --show-current 2>/dev/null || echo "main")
COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")

curl -s -X POST "${TURINGMIND_API_URL:-https://api.turingmind.ai}/api/v1/code-review/reviews" \
  -H "Authorization: Bearer $TURINGMIND_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"context\": {\"repo\": \"$REPO\", \"branch\": \"$BRANCH\", \"commit\": \"$COMMIT\", \"review_type\": \"quick\"},
    \"issues\": [...],
    \"summary\": {\"critical\": 0, \"high\": 1, \"medium\": 2, \"low\": 0}
  }"
```

Or use the helper script:
```bash
~/.turingmind/upload_review.sh "$REVIEW_JSON"
```

**Benefits of uploading:**
- Builds memory for future reviews
- Tracks metrics over time
- Enables dashboard analytics
- Syncs false positives across team

If upload fails, the review is still valid locally.
