---
allowed-tools: Bash(git diff:*), Bash(git status:*), Bash(git log:*), Bash(git blame:*), Bash(git show:*), Bash(curl:*), Bash(~/.turingmind/upload_review.sh:*), Read, Grep, Glob, LS, turingmind_validate_auth, turingmind_upload_review, turingmind_get_context
description: Deep comprehensive code review with full context analysis (Cloud Mode)
---

Comprehensive code review with full context analysis. Includes architecture review, test coverage, and impact analysis.
Running in **Cloud Mode** (API key detected).

## Phase 0: Initialize TuringMind Cloud

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
  "${TURINGMIND_API_URL:-https://api.turingmind.ai}/api/v1/code-review/context/$REPO"
```

- **API details:** See `@agents/cloud-sync.md`
- **What gets injected:** See `@templates/memory-context.md`

Memory improves reviews by skipping known false positives, flagging hotspot files, and enforcing team conventions.

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

If cloud connected, apply memory-based adjustments (see `@templates/false-positive-rules.md#memory-based-scoring`).

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

## Phase 7: Upload to Cloud

Upload review results to TuringMind cloud for analytics and memory.

### Option A: MCP Tool (Preferred)

If TuringMind MCP server is configured, use the type-safe `turingmind_upload_review` tool:

```
turingmind_upload_review({
  repo: "owner/repo",           // from git remote
  branch: "feature/branch",     // from git branch
  commit: "abc123",             // from git rev-parse
  review_type: "deep",
  issues: [
    {
      title: "Issue title from Phases 3-5",
      severity: "critical|high|medium|low",
      category: "security|bug|compliance|architecture",
      file: "path/to/file.ts",
      line: 42,
      description: "Detailed explanation with impact analysis",
      cwe: "CWE-79",            // if applicable
      confidence: 95
    }
  ],
  summary: {
    critical: 0,    // counts from your analysis
    high: 1,
    medium: 3,
    low: 2
  },
  raw_content: "Full review markdown including architectural notes and impact analysis"
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
curl -s -X POST "${TURINGMIND_API_URL:-https://api.turingmind.ai}/api/v1/code-review/reviews" \
  -H "Authorization: Bearer $TURINGMIND_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"context\": {\"repo\": \"$REPO\", \"branch\": \"$BRANCH\", \"commit\": \"$COMMIT\", \"review_type\": \"deep\"},
    \"issues\": [...],
    \"summary\": {\"critical\": 0, \"high\": 1, \"medium\": 3, \"low\": 2}
  }"
```

### Notes

- MCP provides type-safe schema validation before sending
- Curl fallback works everywhere but is more error-prone
- Deep reviews should include `raw_content` with architectural notes
- If upload fails, the review is still valid locally
- Cloud sync enables memory features for future reviews
