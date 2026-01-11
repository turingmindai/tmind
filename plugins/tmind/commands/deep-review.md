---
allowed-tools: Bash(git diff:*), Bash(git status:*), Bash(git log:*), Bash(git blame:*), Bash(git show:*), Bash(curl:*), Bash(~/.turingmind/upload_review.sh:*), Read, Grep, Glob, LS, turingmind_validate_auth, turingmind_upload_review, turingmind_get_context, turingmind_submit_feedback
description: Deep comprehensive code review with full context analysis
---

Comprehensive code review with full context analysis. Includes architecture review, test coverage, and impact analysis.

## Phase 0: Detect Mode & Fetch Context

```bash
# Load API key from config file
[ -f ~/.turingmind/config ] && source ~/.turingmind/config

if [ -n "$TURINGMIND_API_KEY" ] && [ "$TURINGMIND_API_KEY" != "" ]; then
  echo "☁️  Cloud Mode (API key detected)"
  echo "MODE=cloud"
else
  echo "💻 Local Mode (no API key)"
  echo "MODE=local"
  echo "Run /tmind:login to enable cloud features."
fi
```

### Cloud Mode Only: Fetch Memory Context

If `MODE=cloud`, get memory context from TuringMind cloud to improve review quality.

**If MCP tools available:**

```
turingmind_get_context({
  repo: "owner/repo"  // extract from: git remote get-url origin
})
```

**Fallback (curl):**

```bash
source ~/.turingmind/config 2>/dev/null
REPO=$(git remote get-url origin 2>/dev/null | sed 's/.*github.com[:/]//' | sed 's/.git$//' || echo "local")
curl -s -H "Authorization: Bearer $TURINGMIND_API_KEY" \
  "${TURINGMIND_API_URL:-https://api.turingmind.ai}/api/v1/code-review/context/$REPO"
```

**What memory context provides:**
- Known false positive patterns (skip these)
- Hotspot files (give extra scrutiny)
- Team conventions (enforce these)
- Recent open issues (check if this commit fixes any)

Use this context in Phases 3-5 to improve review accuracy. If fetch fails, continue without memory context.

---

## Phase 1: Gather Context (3 Parallel Haiku Agents)

**Agent 1A - Change Summary:**
```
1. Run `git status`, `git diff`, `git diff --staged`
2. If no changes → inform user and stop
3. Extract:
   - Files changed (list)
   - Languages detected (from extensions)
   - Line counts (additions/deletions)
```

**Agent 1B - Project Context:**
```
1. Find CLAUDE.md (root + directories with changes)
2. Read dependency files:
   - package.json / requirements.txt / go.mod / Cargo.toml
3. Identify project type and framework
```

**Agent 1C - Related Files:**
```
For each modified file, find:
- Files that import the modified file
- Files that the modified file imports
- Test files (foo.ts → foo.test.ts)
```

## Phase 2: Load Agents (Progressive)

Only load agents relevant to detected context:

| Condition | Load Agent |
|-----------|------------|
| Always | `@agents/bugs.md` |
| Always | `@agents/security.md` |
| Always (deep) | `@agents/architecture.md` |
| CLAUDE.md exists | `@agents/compliance.md` |
| `.ts/.tsx/.js/.jsx` files | `@agents/language-typescript.md` |
| `.py` files | `@agents/language-python.md` |

See `@agents/index.md` for full routing logic.

## Phase 3: Deep Analysis (Parallel Sonnet Agents)

Launch loaded agents in parallel. Each agent:
1. Reads full file context + related files from Phase 1C
2. Analyzes only the diff (not pre-existing code)
3. Returns structured issues with **diff-style fixes**

**Core Agents (always):**
- `@agents/bugs.md` - Logic errors, null access, race conditions
- `@agents/security.md` - OWASP Top 10, injection, XSS, secrets
- `@agents/architecture.md` - Patterns, coupling, dependencies

**Conditional Agents:**
- `@agents/compliance.md` - If CLAUDE.md exists
- `@agents/language-typescript.md` - If TS/JS files
- `@agents/language-python.md` - If Python files

**Additional Deep Analysis:**
- **Tests & Documentation Agent:**
  - Do test files exist for modified code?
  - Do tests need updating for this change?
  - Are new public APIs missing tests?
  - Do README/docs need updates?

## Phase 4: Impact Analysis (Sonnet Agent)

Using Phase 1C results, analyze:
- What other parts of codebase could be affected?
- Are there breaking changes to public APIs?
- Could this affect performance at scale?
- Are there database/schema implications?
- What's the blast radius if this has a bug?

## Phase 5: Score & Filter (Haiku Agents)

Score each issue 0-100 using criteria from `@templates/false-positive-rules.md`:

| Factor | Points |
|--------|--------|
| In the diff (new code) | +20 |
| Would cause failure | +30 |
| In CLAUDE.md rules | +20 |
| Senior engineer would flag | +20 |
| Has ignore comment | -50 |
| In memory's false positive patterns (cloud only) | -40 |
| In hotspot file (cloud only) | +10 |

**Filtering (lower threshold for deep review):**
- Filter issues with score < 70
- Track filtered count by reason

## Phase 6: Present Results

Format output using `@templates/output-format.md`:

```
## Deep Code Review

**Summary:** Reviewed X files, Y lines changed

| Found | Reported | Filtered |
|-------|----------|----------|
| total | ≥70 score | <70 score |

### Critical (95-100) 🔴
[Issues with diff-style fixes]

### Warning (80-94) 🟠  
[Issues with diff-style fixes]

### Medium (70-79) 🟡
[Issues with diff-style fixes]

### Filtered Issues 🔇
[Count by reason, expandable details]

### Architectural Notes 📐
- Pattern consistency: ✅/⚠️/❌
- Test coverage: ✅/⚠️/❌
- Documentation: ✅/⚠️/❌
- Dependencies: ✅/⚠️/❌

### Impact Analysis 💥
- Affected files: [list]
- Blast radius: [scope]
- Breaking changes: [yes/no]
```

---

## Phase 7: Upload to Cloud (Cloud Mode Only)

If `MODE=cloud`, upload review results to TuringMind cloud for analytics and memory.

**If MCP tools available:**

```
turingmind_upload_review({
  repo: "owner/repo",
  branch: "feature/branch",
  commit: "abc123",
  review_type: "deep",
  issues: [
    {
      title: "Issue title",
      severity: "critical",
      category: "security",
      file: "path/to/file.ts",
      line: 42,
      description: "Detailed explanation with impact analysis",
      cwe: "CWE-79",
      confidence: 95
    }
  ],
  summary: { critical: 0, high: 1, medium: 3, low: 2 },
  raw_content: "Full review markdown including architectural notes"
})
```

**Fallback (curl):**

```bash
source ~/.turingmind/config 2>/dev/null
REPO=$(git remote get-url origin 2>/dev/null | sed 's/.*github.com[:/]//' | sed 's/.git$//' || basename "$(pwd)")
BRANCH=$(git branch --show-current 2>/dev/null || echo "main")
COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")

curl -s -X POST "${TURINGMIND_API_URL:-https://api.turingmind.ai}/api/v1/code-review/reviews" \
  -H "Authorization: Bearer $TURINGMIND_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"context\": {\"repo\": \"$REPO\", \"branch\": \"$BRANCH\", \"commit\": \"$COMMIT\", \"review_type\": \"deep\"},
    \"issues\": [...],
    \"summary\": {\"critical\": 0, \"high\": 1, \"medium\": 3, \"low\": 2}
  }"
```

Or use the helper script:
```bash
~/.turingmind/upload_review.sh "$REVIEW_JSON"
```

**Benefits of uploading:**
- Builds memory for future reviews
- Tracks metrics over time (deep reviews especially valuable)
- Enables dashboard analytics
- Syncs false positives across team
- Stores architectural notes for future reference

If upload fails, the review is still valid locally.

---

## Output Rules

- **Always** include filtered issues summary (builds trust)
- **Always** use diff-style fixes (actionable)
- **Never** report pre-existing issues (not in diff)
- **Never** report linter territory (ESLint will catch)
- If no issues found, confirm code looks good for commit
