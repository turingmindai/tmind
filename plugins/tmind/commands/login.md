---
allowed-tools: Bash(curl:*), Bash(sleep:*), Bash(open:*), Bash(xdg-open:*), Bash(start:*), Bash(pip:*), Bash(python*:*), Bash(cat:*), Bash(mkdir:*), Bash(chmod:*), Bash(echo:*), Bash(grep:*), Bash(cut:*), Bash(sed:*), turingmind_initiate_login, turingmind_poll_login, turingmind_validate_auth
description: Login to TuringMind CLI (MCP or bash fallback)
---

Login to TuringMind using device code flow. Uses MCP tools when available, with bash/curl fallback for first-time setup.

## Prerequisites

If MCP tools (`turingmind_initiate_login`, etc.) are not available, run `/tmind:setup` first to install the MCP server, then restart Claude.

## Method Selection

Check if MCP tools are available. If `turingmind_initiate_login` tool exists, use **Method A (MCP)**. Otherwise, use **Method B (Bash Fallback)**.

---

# Method A: MCP Tools (Preferred)

Use this method if MCP tools are available in your environment.

## A1: Initiate Login

```
turingmind_initiate_login()
```

Returns: `verification_url`, `user_code`, `device_code`

## A2: Open Browser & Show Instructions

```bash
VERIFICATION_URL="<from A1>"
if [[ "$OSTYPE" == "darwin"* ]]; then
    open "$VERIFICATION_URL" 2>/dev/null &
elif command -v xdg-open &> /dev/null; then
    xdg-open "$VERIFICATION_URL" 2>/dev/null &
fi
```

Tell user: "Open {verification_url} and enter code: {user_code}"

## A3: Poll for Completion

After user confirms browser auth is complete:

```
turingmind_poll_login({"device_code": "<from A1>"})
```

On success, API key is auto-saved to `~/.turingmind/config`.

## A4: Validate

```
turingmind_validate_auth()
```

---

# Method B: Bash Fallback (First-Time Setup)

Use this method if MCP tools are NOT available (e.g., first-time login before MCP is configured).

## B1: Initiate Login (Bash)

```bash
API_URL="${TURINGMIND_API_URL:-https://api.turingmind.ai}"
echo "🧠 TuringMind Login"
echo "Initializing authentication..."

AUTH_RESPONSE=$(curl -s "$API_URL/api/v1/cli/auth")

# Extract fields
if command -v jq &> /dev/null; then
    DEVICE_CODE=$(echo "$AUTH_RESPONSE" | jq -r '.device_code')
    USER_CODE=$(echo "$AUTH_RESPONSE" | jq -r '.user_code')
    VERIFICATION_URL=$(echo "$AUTH_RESPONSE" | jq -r '.verification_url')
else
    DEVICE_CODE=$(echo "$AUTH_RESPONSE" | grep -o '"device_code":"[^"]*"' | cut -d'"' -f4)
    USER_CODE=$(echo "$AUTH_RESPONSE" | grep -o '"user_code":"[^"]*"' | cut -d'"' -f4)
    VERIFICATION_URL=$(echo "$AUTH_RESPONSE" | grep -o '"verification_url":"[^"]*"' | cut -d'"' -f4)
fi

if [ -z "$DEVICE_CODE" ] || [ "$DEVICE_CODE" = "null" ]; then
    echo "❌ Failed to initiate authentication"
    echo "Response: $AUTH_RESPONSE"
    exit 1
fi

echo ""
echo "1. Open: $VERIFICATION_URL"
echo "2. Enter code: $USER_CODE"
echo ""
echo "DEVICE_CODE=$DEVICE_CODE"
```

## B2: Open Browser (Bash)

```bash
# Auto-open browser (cross-platform)
if [[ "$OSTYPE" == "darwin"* ]]; then
    open "$VERIFICATION_URL" 2>/dev/null &
elif [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    start "$VERIFICATION_URL" 2>/dev/null &
elif command -v xdg-open &> /dev/null; then
    xdg-open "$VERIFICATION_URL" 2>/dev/null &
else
    echo "(Please open the URL above manually)"
fi
```

Display to user:
```
🧠 TuringMind Login

1. A browser window should open automatically
   (If not, open: {VERIFICATION_URL})

2. Enter this code when prompted:
   {USER_CODE}

3. Complete sign-in in your browser

Tell me when you've completed authentication.
```

## B3: Poll for Completion (Bash)

After user confirms they completed browser authentication, poll for the API key:

```bash
API_URL="${TURINGMIND_API_URL:-https://api.turingmind.ai}"
# DEVICE_CODE should be set from B1

echo "Checking authentication status..."
MAX_ATTEMPTS=60
ATTEMPT=0
API_KEY=""

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    POLL_RESPONSE=$(curl -s "$API_URL/api/v1/cli/token?device_code=$DEVICE_CODE")
    
    # Check for success
    if echo "$POLL_RESPONSE" | grep -q '"access_token"'; then
        if command -v jq &> /dev/null; then
            API_KEY=$(echo "$POLL_RESPONSE" | jq -r '.access_token')
        else
            API_KEY=$(echo "$POLL_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
        fi
        
        if [ -n "$API_KEY" ] && [ "$API_KEY" != "null" ]; then
            echo "✅ Authentication successful!"
            break
        fi
    fi
    
    # Check for errors
    if echo "$POLL_RESPONSE" | grep -q '"error":"expired"'; then
        echo "❌ Device code expired. Please run /tmind:login again."
        exit 1
    fi
    
    if echo "$POLL_RESPONSE" | grep -q '"error":"access_denied"'; then
        echo "❌ Access denied. Please run /tmind:login again."
        exit 1
    fi
    
    # Still pending - wait and retry
    echo -n "."
    sleep 3
    ATTEMPT=$((ATTEMPT + 1))
done

if [ -z "$API_KEY" ]; then
    echo ""
    echo "❌ Timeout waiting for authentication."
    exit 1
fi

echo ""
echo "API_KEY=$API_KEY"
```

## B4: Save API Key (Bash)

After B3 outputs the API key, save it:

```bash
mkdir -p ~/.turingmind
echo "export TURINGMIND_API_KEY=$API_KEY" > ~/.turingmind/config
echo "export TURINGMIND_API_URL=${API_URL:-https://api.turingmind.ai}" >> ~/.turingmind/config
echo "✅ API key saved to ~/.turingmind/config"
```

## B5: Validate (Bash)

```bash
source ~/.turingmind/config
VALIDATE_RESPONSE=$(curl -s -H "Authorization: Bearer $TURINGMIND_API_KEY" \
  "${TURINGMIND_API_URL:-https://api.turingmind.ai}/api/v1/code-review/auth/validate")

if echo "$VALIDATE_RESPONSE" | grep -q '"valid":true'; then
    if command -v jq &> /dev/null; then
        TIER=$(echo "$VALIDATE_RESPONSE" | jq -r '.tier // "unknown"')
        EMAIL=$(echo "$VALIDATE_RESPONSE" | jq -r '.email // "unknown"')
    else
        TIER=$(echo "$VALIDATE_RESPONSE" | grep -o '"tier":"[^"]*"' | cut -d'"' -f4)
        EMAIL=$(echo "$VALIDATE_RESPONSE" | grep -o '"email":"[^"]*"' | cut -d'"' -f4)
    fi
    echo ""
    echo "✅ Successfully logged in!"
    echo "   Account: ${EMAIL:-unknown}"
    echo "   Tier: ${TIER:-unknown}"
else
    echo "⚠️ Validation failed, but key was saved."
fi
```

---

# Post-Login Setup (Both Methods)

After successful login, optionally install helper components:

## Install Fallback Upload Script

```bash
mkdir -p ~/.turingmind
cat > ~/.turingmind/upload_review.sh << 'UPLOAD_SCRIPT'
#!/bin/bash
API_URL="${TURINGMIND_API_URL:-https://api.turingmind.ai}"
[ -z "$TURINGMIND_API_KEY" ] && [ -f ~/.turingmind/config ] && source ~/.turingmind/config
if [ -z "$TURINGMIND_API_KEY" ]; then
  echo "⚠️ TURINGMIND_API_KEY not set. Run /tmind:login first." >&2
  exit 1
fi
if [ -n "$1" ]; then REVIEW_JSON="$1"
else
  REPO=$(git remote get-url origin 2>/dev/null | sed 's/.*github.com[:/]//' | sed 's/.git$//' || basename "$(pwd)")
  BRANCH=$(git branch --show-current 2>/dev/null || echo "main")
  COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
  REVIEW_JSON="{\"context\":{\"repo\":\"$REPO\",\"branch\":\"$BRANCH\",\"commit\":\"$COMMIT\",\"review_type\":\"quick\"}}"
fi
HTTP_CODE=$(curl -s -w "%{http_code}" -o /tmp/tmind_upload_response.json \
  -X POST -H "Authorization: Bearer $TURINGMIND_API_KEY" -H "Content-Type: application/json" \
  "$API_URL/api/v1/code-review/reviews" -d "$REVIEW_JSON" 2>/dev/null)
rm -f /tmp/tmind_upload_response.json
case "$HTTP_CODE" in
  200|201) echo "🧠 Review uploaded"; exit 0 ;;
  401) echo "⚠️ Auth failed" >&2; exit 1 ;;
  *) echo "⚠️ HTTP $HTTP_CODE" >&2; exit 0 ;;
esac
UPLOAD_SCRIPT
chmod +x ~/.turingmind/upload_review.sh
echo "✅ Upload script installed"
```

## Install MCP Server (Optional)

```bash
PYTHON_CMD=""
for cmd in python3.12 python3.11 python3.10 python3; do
    if command -v $cmd &> /dev/null; then
        if $cmd -c 'import sys; exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
            PYTHON_CMD=$cmd
            break
        fi
    fi
done

if [ -n "$PYTHON_CMD" ]; then
    echo "📦 Checking MCP server..."
    if $PYTHON_CMD -c "import turingmind_mcp" 2>/dev/null; then
        echo "   ✅ Already installed"
    else
        echo "   Installing from PyPI..."
        $PYTHON_CMD -m pip install turingmind-mcp --quiet 2>/dev/null || \
        echo "   ⚠️ Install failed (will use curl fallback)"
    fi
else
    echo "⚠️ Python 3.10+ not found (MCP optional)"
fi
```

## Configure Claude Desktop (Optional)

```bash
if [ -n "$PYTHON_CMD" ] && $PYTHON_CMD -c "import turingmind_mcp" 2>/dev/null; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
        CLAUDE_CONFIG_DIR="$HOME/Library/Application Support/Claude"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        CLAUDE_CONFIG_DIR="${APPDATA:-$HOME/AppData/Roaming}/Claude"
    else
        CLAUDE_CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/Claude"
    fi
    
    if [ -d "$CLAUDE_CONFIG_DIR" ]; then
        echo "🔌 Configuring Claude Desktop..."
        $PYTHON_CMD << MERGE_SCRIPT
import json, os
config_path = "$CLAUDE_CONFIG_DIR/claude_desktop_config.json"
api_key = api_url = ""
try:
    with open(os.path.expanduser("~/.turingmind/config")) as f:
        for line in f:
            if "TURINGMIND_API_KEY=" in line: api_key = line.split("=",1)[1].strip()
            if "TURINGMIND_API_URL=" in line: api_url = line.split("=",1)[1].strip()
except: pass
if not api_key: print("   ⚠️ No API key"); exit(1)
try:
    with open(config_path) as f: config = json.load(f)
except: config = {}
if os.path.exists(config_path):
    with open(config_path+".backup",'w') as f: json.dump(config,f,indent=2)
config.setdefault('mcpServers',{})['turingmind'] = {
    "command": "$PYTHON_CMD", "args": ["-m","turingmind_mcp.server"],
    "env": {"TURINGMIND_API_KEY": api_key, "TURINGMIND_API_URL": api_url or "https://api.turingmind.ai"}
}
with open(config_path,'w') as f: json.dump(config,f,indent=2)
print("   ✅ Configured"); print("   ⚠️ Restart Claude Desktop")
MERGE_SCRIPT
    fi
fi
```

---

## Success Output

```
✅ Successfully logged in to TuringMind!

Account: {email}
Tier: {tier}

Cloud features enabled:
  • Memory (learns from past reviews)
  • Dashboard (metrics & trends)
  • False positive learning

You can now use:
  /tmind:review      — Quick pre-commit review
  /tmind:deep-review — Thorough pre-PR review
```

## Error Handling

| Error | Action |
|-------|--------|
| Network error | Check internet, retry |
| Device code expired | Run `/tmind:login` again |
| Access denied | Run `/tmind:login` again |
| MCP tools not available | Use Method B (bash fallback) |
