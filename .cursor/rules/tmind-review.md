---
description: TuringMind code review workflow for Cursor IDE
globs: "**/*"
alwaysApply: false
---

# TuringMind Code Review Workflow

When the user asks for a code review, TuringMind review, or when invoked via `cursor-agent`, follow this workflow.

## Trigger Phrases

Activate this workflow when user says:
- "review my code"
- "turingmind review"
- "tmind review"
- "check for bugs"
- "security review"
- "code quality check"

## Step 1: Detect Mode & Load Config

```bash
# Check for TuringMind API key (enables cloud features)
[ -f ~/.turingmind/config ] && source ~/.turingmind/config

if [ -n "$TURINGMIND_API_KEY" ]; then
  MODE=cloud
else
  MODE=local
fi
```

**Announce mode:**
- Cloud: "☁️ Cloud Mode - Memory and analytics enabled"
- Local: "💻 Local Mode - Run `/tmind:login` to enable cloud features"

## Step 2: Gather Context

Run these commands to understand what to review:

```bash
# Check for changes
git status --porcelain
git diff --stat
git diff --cached --stat  # staged changes
```

**Extract:**
- Files changed (list paths)
- Languages (from file extensions)
- Line counts (additions/deletions)
- Whether CLAUDE.md or .cursor/rules exist

**If no changes:** Report "No changes to review" and stop.

## Step 3: Select Agents

Based on detected context, apply these agent checks from `tmind-agents.md`:

| Always Apply | Conditional |
|--------------|-------------|
| Bugs Agent | TypeScript Agent (if .ts/.tsx/.js/.jsx) |
| Security Agent | Python Agent (if .py) |
| | Compliance Agent (if CLAUDE.md exists) |
| | Architecture Agent (if deep review requested) |

## Step 4: Fetch Memory Context (Cloud Only)

If `MODE=cloud`, call the MCP tool to get memory context:

```
turingmind_get_context({
  repo: "<owner>/<repo>"  // from: git remote get-url origin
})
```

**Use memory for:**
- Skip known false positive patterns
- Extra scrutiny on hotspot files  
- Enforce team conventions
- Check if commit fixes known issues

If fetch fails, continue without memory.

## Step 5: Run Review

For each applicable agent, analyze the changed code:

1. **Read the diff** - Focus on new/modified lines only
2. **Apply agent checks** - From `tmind-agents.md`
3. **Score each issue 0-100:**

| Factor | Points |
|--------|--------|
| In the diff (new code) | +20 |
| Would cause runtime failure | +30 |
| Violates CLAUDE.md rules | +20 |
| Senior engineer would flag | +20 |
| Has ignore comment | -50 |
| Memory says false positive | -40 |
| Hotspot file | +10 |

4. **Filter issues < 80 score**

## Step 6: Format Output

Present results in this format:

```markdown
## 🧠 TuringMind Code Review

**Mode:** [Local/Cloud]
**Files:** X files, Y lines changed
**Agents:** Bugs, Security, [others]

### Summary
| Found | Reported | Filtered |
|-------|----------|----------|
| N     | M (≥80)  | K (<80)  |

---

### 🔴 Critical (95-100)
Must fix before committing:

#### Issue Title
**Location:** `file.ts:42`
**Confidence:** 97/100
**Agent:** Security

**Problem:** Description of the issue

**Fix:**
```diff
- vulnerable code
+ safe code
```

---

### 🟠 Warning (80-94)
Should fix:

[Same format as Critical]

---

### 🔇 Filtered (X issues)
<details>
<summary>Show filtered issues</summary>

- file.ts:10 - Minor style issue (score: 65)
- file.ts:25 - Pre-existing code (score: 40)
</details>
```

## Step 7: Upload to Cloud (Cloud Only)

If `MODE=cloud` and issues were found, upload results:

```
turingmind_upload_review({
  repo: "owner/repo",
  branch: "feature/x",
  commit: "abc123",
  review_type: "quick",
  issues: [...],
  summary: { critical: 0, high: 1, medium: 2, low: 0 }
})
```

**Benefits:**
- Builds memory for future reviews
- Tracks metrics over time
- Syncs with team dashboards

## MCP Tools Available

When connected to TuringMind cloud via MCP:

| Tool | Purpose |
|------|---------|
| `turingmind_get_context` | Fetch memory (false positives, hotspots, conventions) |
| `turingmind_upload_review` | Store review results |
| `turingmind_submit_feedback` | Mark issues as false positive |
| `turingmind_validate_auth` | Check if API key is valid |

## Example Invocation

**In Cursor chat:**
```
Review my staged changes for bugs and security issues
```

**Via cursor-agent CLI:**
```bash
cursor-agent -p "Run TuringMind code review on my staged changes" --output-format text
```

**Via git hook:**
```bash
# Automatically runs on git commit/push
git commit -m "fix: update auth logic"
```
