# TuringMind MCP Server

Model Context Protocol (MCP) server for TuringMind cloud integration. Provides type-safe tools for Claude to upload code reviews and fetch repository context.

> **Requires Python 3.10+** (MCP SDK requirement)

## Why MCP?

Instead of Claude generating raw JSON and curl commands (which can fail silently due to field name mismatches or malformed data), MCP provides:

- **Type-safe tool definitions** - Claude sees the exact schema
- **Validated input** - Errors caught before sending
- **No endpoint guessing** - Correct URL hardcoded
- **Better error messages** - Clear feedback on failures

## Installation

### From PyPI (when published)

```bash
pip install turingmind-mcp
```

### From Source

```bash
cd mcp-server
pip install -e .
```

### Verify Installation

```bash
turingmind-mcp --help
```

## Configuration

### Claude Desktop

Add to your Claude Desktop config file:
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux:** `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "turingmind": {
      "command": "turingmind-mcp",
      "env": {
        "TURINGMIND_API_URL": "https://api.turingmind.ai"
      }
    }
  }
}
```

### For Local Development

```json
{
  "mcpServers": {
    "turingmind": {
      "command": "turingmind-mcp",
      "env": {
        "TURINGMIND_API_URL": "http://localhost:3000"
      }
    }
  }
}
```

### Authentication

The server reads the API key from:
1. `TURINGMIND_API_KEY` environment variable
2. `~/.turingmind/config` file (created by `/tmind:login`)

## Available Tools

### `turingmind_validate_auth`

Validate API key and get account info.

```
No parameters required
```

**Returns:**
- Tier (free, pro, enterprise)
- Quota remaining
- User ID

### `turingmind_upload_review`

Upload code review results to TuringMind cloud.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `repo` | string | ✅ | Repository (owner/repo) |
| `branch` | string | | Git branch name |
| `commit` | string | | Git commit SHA |
| `review_type` | "quick" \| "deep" | | Review type (default: quick) |
| `issues` | array | | List of issues found |
| `raw_content` | string | | Full review as markdown |
| `summary` | object | | {critical, high, medium, low} counts |
| `files_reviewed` | array | | Files that were reviewed |

**Issue Schema:**

```json
{
  "title": "SQL Injection vulnerability",
  "severity": "critical",
  "category": "security",
  "file": "src/db.py",
  "line": 42,
  "description": "User input passed directly to query",
  "cwe": "CWE-89",
  "confidence": 95
}
```

### `turingmind_get_context`

Get memory context for a repository.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `repo` | string | ✅ | Repository (owner/repo) |

**Returns:**
- Recent open issues
- Hotspot files (frequent issues)
- Team conventions
- Known false positive patterns

## Usage in Claude

Once configured, Claude will automatically have access to these tools:

```
User: Review my code changes and upload to TuringMind

Claude: I'll validate authentication first, then review and upload.

[Calls turingmind_validate_auth]
✅ TuringMind Authentication Valid
- Tier: pro
- Quota: 495/500 reviews remaining

[Reviews code...]

[Calls turingmind_upload_review]
🧠 Review Uploaded to TuringMind
- Review ID: rev_abc123
- Issues: 3
```

## Development

### Run Locally

```bash
cd mcp-server
pip install -e ".[dev]"
python -m turingmind_mcp.server
```

### Test with MCP Inspector

```bash
npx @modelcontextprotocol/inspector turingmind-mcp
```

### Debug Logging

```bash
TURINGMIND_DEBUG=1 turingmind-mcp
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `TURINGMIND_API_URL` | API server URL | `https://api.turingmind.ai` |
| `TURINGMIND_API_KEY` | API key for authentication | Read from `~/.turingmind/config` |
| `TURINGMIND_DEBUG` | Enable debug logging | `0` |

## Troubleshooting

### "TURINGMIND_API_KEY not configured"

Run `/tmind:login` to authenticate, or set the environment variable:

```bash
export TURINGMIND_API_KEY=tmk_your_key_here
```

### "Permission Denied"

API key lacks `code_review:write` permission. Re-run `/tmind:login` to create a new key with proper permissions.

### "Connection Error"

Check that:
1. `TURINGMIND_API_URL` is correct
2. Network is available
3. Backend server is running (for local development)

## License

MIT

