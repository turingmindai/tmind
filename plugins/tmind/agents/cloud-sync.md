---
name: TuringMind Cloud Sync
description: Syncs review results to TuringMind cloud for memory and analytics
model: haiku
---

# TuringMind Cloud Sync Agent

This agent handles communication with the TuringMind cloud API for:
- Fetching memory context (past reviews, false positives, team conventions)
- Syncing review results (issues found, metrics)
- Tracking issue feedback (fixed, dismissed, false positive)

## Preferred Method: MCP Tools

If the TuringMind MCP server is configured, use these type-safe tools:

| Tool | Purpose |
|------|---------|
| `turingmind_validate_auth` | Check API key, get account info |
| `turingmind_upload_review` | Upload review results (type-safe schema) |
| `turingmind_get_context` | Fetch memory context for a repo |

MCP advantages:
- Type-safe input validation before sending
- No field name mismatches (`findings` vs `issues`)
- Clear error messages
- Schema enforced by tool definition

See `tmind/mcp-server/README.md` for installation.

## Fallback Method: REST API

If MCP is not available, use the REST API directly.

### Prerequisites

Requires `TURINGMIND_API_KEY` environment variable to be set.

```bash
# Check if API key is configured
if [ -z "$TURINGMIND_API_KEY" ]; then
  echo "TURINGMIND_API_KEY not set - cloud features disabled"
  echo "To enable: Run /tmind:login to authenticate and set your API key"
fi
```

**Setting the API key:**
- Run `/tmind:login` - this will export the API key for the current session
- Or manually: `export TURINGMIND_API_KEY=your_key_here`

If not set, cloud features are disabled and reviews run in local-only mode.

## API Endpoints

Base URL: `${TURINGMIND_API_URL:-http://localhost:3000}/api/v1/code-review`

> **Note:** Default is localhost for local development
> 
> **Override:** Set `TURINGMIND_API_URL` environment variable to use a different endpoint 

### Authentication

All requests include:
```
Authorization: Bearer $TURINGMIND_API_KEY
Content-Type: application/json
```

### 1. Validate API Key

```bash
API_URL="${TURINGMIND_API_URL:-http://localhost:3000}"
curl -s -H "Authorization: Bearer $TURINGMIND_API_KEY" \
  "$API_URL/api/v1/code-review/auth/validate"
```

Response:
```json
{
  "valid": true,
  "tier": "pro",
  "user_id": "user_abc123",
  "org": "turingmindai",
  "quota": {
    "reviews_remaining": 450,
    "reviews_limit": 500,
    "reviews_used": 50
  }
}
```

Tier values: `free`, `pro`, `team`, `enterprise`

### 2. Fetch Memory Context

```bash
# Get repo identifier from git remote
REPO=$(git remote get-url origin 2>/dev/null | sed 's/.*github.com[:/]//' | sed 's/.git$//' || echo "local")

API_URL="${TURINGMIND_API_URL:-http://localhost:3000}"
curl -s -H "Authorization: Bearer $TURINGMIND_API_KEY" \
  "$API_URL/api/v1/code-review/context/$REPO"
```

Response:
```json
{
  "repo": "turingmindai/myapp",
  "known_false_positives": [
    {
      "pattern": "config?.optional",
      "reason": "Config is always defined in this codebase",
      "count_dismissed": 12
    }
  ],
  "hotspot_files": [
    { "path": "src/auth.ts", "issue_count": 15, "last_issue": "2026-01-05" }
  ],
  "recent_open_issues": [
    {
      "id": "iss_abc",
      "file": "src/auth.ts",
      "line": 20,
      "title": "SQL Injection",
      "status": "open"
    }
  ],
  "team_conventions": [
    "Always use parameterized queries",
    "Prefer optional chaining over null checks"
  ]
}
```

### 3. Upload Review Results

**Endpoint:** `POST /api/v1/code-review/reviews`

The schema is flexible - only `context.repo` is required. All other fields are optional.

#### Minimal Upload (Recommended)

```bash
source ~/.turingmind/config
curl -s -X POST "${TURINGMIND_API_URL:-http://localhost:3000}/api/v1/code-review/reviews" \
  -H "Authorization: Bearer $TURINGMIND_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "context": {
      "repo": "owner/repo",
      "branch": "main",
      "commit": "abc123",
      "review_type": "quick"
    },
    "raw_content": "Review summary in markdown format...",
    "summary": {"critical": 0, "warning": 1}
  }'
```

#### Full Upload (Optional structured data)

```bash
curl -s -X POST "${TURINGMIND_API_URL:-http://localhost:3000}/api/v1/code-review/reviews" \
  -H "Authorization: Bearer $TURINGMIND_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "context": {"repo": "owner/repo", "review_type": "deep"},
    "raw_content": "Full markdown review here...",
    "files_reviewed": [{"path": "src/file.ts"}],
    "issues": [{"title": "Issue found", "file": "src/file.ts"}],
    "summary": {"critical": 0, "warning": 1, "medium": 0}
  }'
```

Response:
```json
{
  "review_id": "rev_abc123def456",
  "stored": true,
  "message": "Review stored successfully"
}
```

### 4. Send Issue Feedback

```bash
API_URL="${TURINGMIND_API_URL:-http://localhost:3000}"
curl -X POST -H "Authorization: Bearer $TURINGMIND_API_KEY" \
  -H "Content-Type: application/json" \
  "$API_URL/api/v1/code-review/issues/$ISSUE_ID/feedback" \
  -d '{
    "action": "fixed",
    "timestamp": "2026-01-09T12:30:00Z",
    "repo": "turingmindai/myapp",
    "review_id": "rev_uuid",
    "file": "src/auth.ts",
    "line": 23,
    "title": "SQL Injection vulnerability",
    "category": "security"
  }'
```

Actions:
- `fixed` — User fixed the issue (tracks time-to-fix metrics)
- `dismissed` — User dismissed as not important (lowers future priority)
- `false_positive` — User marked as false positive (adds pattern to memory)

For `false_positive`, include `pattern` and `reason`:
```json
{
  "action": "false_positive",
  "repo": "turingmindai/myapp",
  "pattern": "config?.optional",
  "reason": "Config is always defined in this codebase"
}
```

## Integration Points

### On Review Start

1. Check for `TURINGMIND_API_KEY`
2. If present, validate and fetch memory context
3. Inject context into review agents

### On Review Complete

1. Format review results as JSON
2. Run `~/.turingmind/upload_review.sh "$REVIEW_JSON"` (async, non-blocking)
3. Handle failures gracefully (don't break review)

### On User Feedback

When user indicates an issue was:
- **Fixed**: Track for metrics
- **Dismissed**: Learn to deprioritize
- **False Positive**: Add to memory to skip in future

## Privacy

**What we send:**
- File paths
- Line numbers
- Issue titles and descriptions
- Metrics (lines changed, review time)

**What we NEVER send:**
- Full source code
- Code snippets (unless user opts in)
- Credentials or secrets
- Personal information

## Error Handling

```
If API call fails:
├── Network error → Log warning, continue review
├── 401 Unauthorized → Log "API key invalid", continue in local mode
├── 429 Rate Limited → Log "Quota exceeded", continue in local mode
└── 5xx Server Error → Log warning, continue review

Reviews should NEVER fail due to cloud sync issues.
```

## Local Mode Fallback

If `TURINGMIND_API_KEY` is not set or invalid:
- All cloud features are disabled
- Review runs purely locally
- No data is sent anywhere
- Full functionality preserved (just no memory/sync)

