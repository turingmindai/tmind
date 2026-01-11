---
allowed-tools: Bash(curl:*), Bash(sleep:*), Bash(echo:*), Bash(grep:*), Bash(cut:*), Bash(mkdir:*), Bash(open:*), Bash(xdg-open:*), Bash(start:*), Bash(pip:*), Bash(python*:*), Bash(cat:*)
description: Login to TuringMind CLI - Optimized Flow with MCP Server Installation
---

Login to TuringMind using device code flow. This command runs a unified script to handle authentication, persistence, and validation in one go.

## Optimized Login Script

Execute the following script to log in:

```bash
#!/bin/bash
set -e

# Default API URL (production by default, override with TURINGMIND_API_URL env var)
API_URL="${TURINGMIND_API_URL:-https://api.turingmind.ai}"

# Check for curl
if ! command -v curl &> /dev/null; then
    echo "Error: curl is required."
    exit 1
fi

# STEP 1: Initiate Auth
echo "🧠 TuringMind Login"
echo "Initializing authentication..."

AUTH_RESPONSE=$(curl -s "$API_URL/api/v1/cli/auth")

# Extract fields using jq if available, else grep/cut
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
    echo "Failed to initiate authentication. Response: $AUTH_RESPONSE"
    exit 1
fi

# STEP 2: Display + Auto-Open
echo ""
echo "1. Opening browser to: $VERIFICATION_URL"
echo "2. Enter code: $USER_CODE"

# Auto-open browser
echo "Using browser to authenticate..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    open "$VERIFICATION_URL" 2>/dev/null &
elif [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    start "$VERIFICATION_URL" 2>/dev/null &
elif command -v xdg-open &> /dev/null; then
    xdg-open "$VERIFICATION_URL" 2>/dev/null &
else
    echo "(Please open the URL above manually)"
fi

# STEP 3: Poll
echo ""
echo "Waiting for authentication..."
ATTEMPT=0
MAX_ATTEMPTS=120
API_KEY=""

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    POLL_OUTPUT=$(curl -s -w "\nHTTP_CODE:%{http_code}" "$API_URL/api/v1/cli/token?device_code=$DEVICE_CODE")
    POLL_RESPONSE=$(echo "$POLL_OUTPUT" | sed 's/HTTP_CODE:.*$//')
    HTTP_CODE=$(echo "$POLL_OUTPUT" | grep -o 'HTTP_CODE:[0-9]*' | cut -d: -f2)

    if [ "$HTTP_CODE" = "200" ] && echo "$POLL_RESPONSE" | grep -q '"access_token"'; then
        if command -v jq &> /dev/null; then
            API_KEY=$(echo "$POLL_RESPONSE" | jq -r '.access_token')
        else
            API_KEY=$(echo "$POLL_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
        fi

        if [ -n "$API_KEY" ] && [ "$API_KEY" != "null" ]; then
             echo ""
             echo "Authenticated!"
             break
        fi
    fi

    if echo "$POLL_RESPONSE" | grep -q '"error":"expired"'; then
        echo ""
        echo "Authentication expired. Please run /tmind:login again."
        exit 1
    fi

    echo -n "."

    if [ $ATTEMPT -lt 20 ]; then
        sleep 3
    else
        sleep 5
    fi
    ATTEMPT=$((ATTEMPT + 1))
done

if [ -z "$API_KEY" ]; then
    echo ""
    echo "Timeout waiting for authentication."
    exit 1
fi

# STEP 4: Export + Save
export TURINGMIND_API_KEY="$API_KEY"
mkdir -p ~/.turingmind
echo "export TURINGMIND_API_KEY=$API_KEY" > ~/.turingmind/config

# Install the upload_review script (used by /tmind:review and /tmind:deep-review)
cat > ~/.turingmind/upload_review.sh << 'UPLOAD_SCRIPT'
#!/bin/bash
# TuringMind Review Upload Script
# Flexible schema - only context.repo is required

API_URL="${TURINGMIND_API_URL:-https://api.turingmind.ai}"

# Source config if not already set
[ -z "$TURINGMIND_API_KEY" ] && [ -f ~/.turingmind/config ] && source ~/.turingmind/config

if [ -z "$TURINGMIND_API_KEY" ]; then
  echo "⚠️ TURINGMIND_API_KEY not set. Run /tmind:login first." >&2
  exit 1
fi

# Accept JSON as argument or build minimal JSON from git context
if [ -n "$1" ]; then
  REVIEW_JSON="$1"
else
  # Build minimal review JSON from current git state
  REPO=$(git remote get-url origin 2>/dev/null | sed 's/.*github.com[:/]//' | sed 's/.git$//' || basename "$(pwd)")
  BRANCH=$(git branch --show-current 2>/dev/null || echo "main")
  COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
  REVIEW_JSON="{\"context\":{\"repo\":\"$REPO\",\"branch\":\"$BRANCH\",\"commit\":\"$COMMIT\",\"review_type\":\"quick\"}}"
fi

# POST to reviews endpoint
HTTP_CODE=$(curl -s -w "%{http_code}" -o /tmp/tmind_upload_response.json \
  -X POST \
  -H "Authorization: Bearer $TURINGMIND_API_KEY" \
  -H "Content-Type: application/json" \
  "$API_URL/api/v1/code-review/reviews" \
  -d "$REVIEW_JSON" 2>/dev/null)

RESPONSE=$(cat /tmp/tmind_upload_response.json 2>/dev/null || echo '{}')
rm -f /tmp/tmind_upload_response.json

case "$HTTP_CODE" in
  200|201) echo "🧠 Review uploaded to TuringMind"; exit 0 ;;
  401) echo "⚠️ Authentication failed. Re-run /tmind:login" >&2; exit 1 ;;
  403) echo "⚠️ Permission denied. API key may lack code_review:write permission" >&2; exit 1 ;;
  *) echo "⚠️ Upload returned HTTP $HTTP_CODE (review saved locally)" >&2; exit 0 ;;
esac
UPLOAD_SCRIPT
chmod +x ~/.turingmind/upload_review.sh

# STEP 4b: Install MCP Server (if Python 3.10+ available)
MCP_INSTALLED=false
PYTHON_CMD=""

# Find Python 3.10+ (required for MCP)
for cmd in python3.12 python3.11 python3.10 python3; do
    if command -v $cmd &> /dev/null; then
        if $cmd -c 'import sys; exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
            PYTHON_CMD=$cmd
            break
        fi
    fi
done

if [ -n "$PYTHON_CMD" ]; then
    echo ""
    echo "📦 Installing MCP server (Python $($PYTHON_CMD --version 2>&1 | cut -d' ' -f2))..."
    
    # Check if already installed
    if $PYTHON_CMD -c "import turingmind_mcp" 2>/dev/null; then
        echo "   ✅ MCP server already installed"
        MCP_INSTALLED=true
    else
        # Try PyPI first (when published), fallback to GitHub
        if $PYTHON_CMD -m pip install turingmind-mcp --quiet 2>/dev/null; then
            MCP_INSTALLED=true
            echo "   ✅ MCP server installed from PyPI"
        elif $PYTHON_CMD -m pip install "git+https://github.com/turingmindai/tmind.git#subdirectory=mcp-server" --quiet 2>/dev/null; then
            MCP_INSTALLED=true
            echo "   ✅ MCP server installed from GitHub"
        elif $PYTHON_CMD -m pip install --user "git+https://github.com/turingmindai/tmind.git#subdirectory=mcp-server" --quiet 2>/dev/null; then
            MCP_INSTALLED=true
            echo "   ✅ MCP server installed from GitHub (user)"
        else
            echo "   ⚠️ MCP install failed (will use curl fallback)"
        fi
    fi
    
    # Save MCP config if installed
    if [ "$MCP_INSTALLED" = true ]; then
        echo "TURINGMIND_PYTHON=$PYTHON_CMD" >> ~/.turingmind/config
    fi
else
    echo ""
    echo "⚠️ Python 3.10+ not found (MCP requires it, will use curl fallback)"
fi

# Auto-configure Claude Desktop (if installed)
if [ "$MCP_INSTALLED" = true ]; then
    CLAUDE_CONFIG_DIR="$HOME/Library/Application Support/Claude"
    CLAUDE_CONFIG="$CLAUDE_CONFIG_DIR/claude_desktop_config.json"
    
    # Also save a backup copy
    cat > ~/.turingmind/claude_mcp_config.json << MCPCONFIG
{
  "mcpServers": {
    "turingmind": {
      "command": "$PYTHON_CMD",
      "args": ["-m", "turingmind_mcp.server"],
      "env": {
        "TURINGMIND_API_KEY": "$API_KEY",
        "TURINGMIND_API_URL": "$API_URL"
      }
    }
  }
}
MCPCONFIG

    if [ -d "$CLAUDE_CONFIG_DIR" ]; then
        echo ""
        echo "🔌 Configuring Claude Desktop MCP..."
        
        if [ -f "$CLAUDE_CONFIG" ]; then
            # Merge with existing config using Python (more reliable than jq for this)
            python3 << MERGE_SCRIPT
import json
import os

config_path = "$CLAUDE_CONFIG"
backup_path = config_path + ".backup"

# Read existing config
try:
    with open(config_path) as f:
        config = json.load(f)
except:
    config = {}

# Backup existing config
with open(backup_path, 'w') as f:
    json.dump(config, f, indent=2)

# Ensure mcpServers exists
if 'mcpServers' not in config:
    config['mcpServers'] = {}

# Add/update turingmind server
config['mcpServers']['turingmind'] = {
    "command": "$PYTHON_CMD",
    "args": ["-m", "turingmind_mcp.server"],
    "env": {
        "TURINGMIND_API_KEY": "$API_KEY",
        "TURINGMIND_API_URL": "$API_URL"
    }
}

# Write updated config
with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)

print("   ✅ Merged TuringMind MCP into Claude Desktop config")
print("   📁 Backup saved to: " + backup_path)
MERGE_SCRIPT
        else
            # Create new config file
            cat > "$CLAUDE_CONFIG" << NEWCONFIG
{
  "mcpServers": {
    "turingmind": {
      "command": "$PYTHON_CMD",
      "args": ["-m", "turingmind_mcp.server"],
      "env": {
        "TURINGMIND_API_KEY": "$API_KEY",
        "TURINGMIND_API_URL": "$API_URL"
      }
    }
  }
}
NEWCONFIG
            echo "   ✅ Created Claude Desktop config with TuringMind MCP"
        fi
        echo "   ⚠️  Restart Claude Desktop to enable MCP tools"
    else
        echo ""
        echo "🔌 MCP config saved to ~/.turingmind/claude_mcp_config.json"
        echo "   (Claude Desktop not found - install from claude.ai/download)"
    fi
fi

echo ""
echo "API key saved to ~/.turingmind/config"
echo "Upload script installed to ~/.turingmind/upload_review.sh"
if [ "$MCP_INSTALLED" = true ]; then
    echo "MCP server installed (preferred for type-safe API calls)"
fi

# STEP 5: Validate
echo "Validating key..."
VALIDATE_RESPONSE=$(curl -s -H "Authorization: Bearer $TURINGMIND_API_KEY" "$API_URL/api/v1/code-review/auth/validate")

if echo "$VALIDATE_RESPONSE" | grep -q '"valid":true'; then
    if command -v jq &> /dev/null; then
        TIER=$(echo "$VALIDATE_RESPONSE" | jq -r '.tier // "unknown"')
        EMAIL=$(echo "$VALIDATE_RESPONSE" | jq -r '.email // "unknown"')
    else
        TIER=$(echo "$VALIDATE_RESPONSE" | grep -o '"tier":"[^"]*"' | cut -d'"' -f4)
        EMAIL=$(echo "$VALIDATE_RESPONSE" | grep -o '"email":"[^"]*"' | cut -d'"' -f4)
    fi

    echo ""
    echo "Successfully logged in!"
    echo "   Account: ${EMAIL}"
    echo "   Tier: ${TIER}"
    echo ""
    echo "Cloud features enabled. You can now use /tmind:review and /tmind:deep-review."
    echo ""
    echo "API_KEY=$API_KEY"
else
    echo "Validation failed, but key was saved."
    echo "Response: $VALIDATE_RESPONSE"
fi
```


Login to TuringMind using device code flow to get your API key for cloud features (memory, dashboard, analytics).

## Step 1: Start CLI Authentication

Call the backend to initiate device code authentication:

```bash
API_URL="${TURINGMIND_API_URL:-https://api.turingmind.ai}"
echo "DEBUG: Using API URL: $API_URL"
AUTH_RESPONSE=$(curl -s "$API_URL/api/v1/cli/auth")
```

Extract the device code, user code, and verification URL from the response:

```bash
# Parse JSON response (using grep/cut as fallback if jq not available)
DEVICE_CODE=$(echo "$AUTH_RESPONSE" | grep -o '"device_code":"[^"]*"' | cut -d'"' -f4)
USER_CODE=$(echo "$AUTH_RESPONSE" | grep -o '"user_code":"[^"]*"' | cut -d'"' -f4)
VERIFICATION_URL=$(echo "$AUTH_RESPONSE" | grep -o '"verification_url":"[^"]*"' | cut -d'"' -f4)
```

If `jq` is available, use it for more reliable parsing:
```bash
DEVICE_CODE=$(echo "$AUTH_RESPONSE" | jq -r '.device_code')
USER_CODE=$(echo "$AUTH_RESPONSE" | jq -r '.user_code')
VERIFICATION_URL=$(echo "$AUTH_RESPONSE" | jq -r '.verification_url')
```

## Step 2: Display Login Instructions

Show the user clear instructions:

```
🧠 TuringMind Login

1. Open this URL in your browser:
   {VERIFICATION_URL}

2. Enter this code when prompted:
   {USER_CODE}

3. Complete authentication in your browser

⏳ Waiting for authentication...
```

## Step 3: Poll for Authentication Completion

Poll the token endpoint every 5 seconds until authentication is complete. Show progress and debug output:

```bash
MAX_ATTEMPTS=120  # 10 minutes max (120 * 5 seconds)
ATTEMPT=0
API_KEY=""

echo "Polling for authentication completion..."
echo ""

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
  # Poll the endpoint (get both response and HTTP code in one call)
  POLL_OUTPUT=$(curl -s -w "\nHTTP_CODE:%{http_code}" "$API_URL/api/v1/cli/token?device_code=$DEVICE_CODE")
  POLL_RESPONSE=$(echo "$POLL_OUTPUT" | sed 's/HTTP_CODE:.*$//')
  HTTP_CODE=$(echo "$POLL_OUTPUT" | grep -o 'HTTP_CODE:[0-9]*' | cut -d: -f2)
  
  # Debug: Show full response and HTTP code
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "Poll attempt $((ATTEMPT + 1))/$MAX_ATTEMPTS"
  echo "HTTP Status: $HTTP_CODE"
  echo "Full Response: $POLL_RESPONSE"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  
  # Check if we got an access token (success) - check HTTP code first
  if [ "$HTTP_CODE" = "200" ] && echo "$POLL_RESPONSE" | grep -q '"access_token"'; then
    echo ""
    echo "✅ Authentication completed! Extracting API key..."
    # Extract API key
    if command -v jq &> /dev/null; then
      API_KEY=$(echo "$POLL_RESPONSE" | jq -r '.access_token')
    else
      API_KEY=$(echo "$POLL_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
    fi
    
    if [ -n "$API_KEY" ] && [ "$API_KEY" != "null" ] && [ "$API_KEY" != "" ]; then
      echo "API key extracted successfully: ${API_KEY:0:20}..."
      break
    else
      echo "⚠️  Warning: access_token found but extraction failed, retrying extraction..."
      # Try alternative extraction method
      API_KEY=$(echo "$POLL_RESPONSE" | sed -n 's/.*"access_token":"\([^"]*\)".*/\1/p')
      if [ -n "$API_KEY" ] && [ "$API_KEY" != "null" ] && [ "$API_KEY" != "" ]; then
        echo "API key extracted successfully (alternative method): ${API_KEY:0:20}..."
        break
      else
        echo "❌ Failed to extract API key from response. Response was: $POLL_RESPONSE"
        exit 1
      fi
    fi
  fi
  
  # Check for expired error
  if echo "$POLL_RESPONSE" | grep -q '"error":"expired"'; then
    echo ""
    echo "❌ Authentication expired. Please run /tmind:login again."
    exit 1
  fi
  
  # Check for authorization_pending (still waiting)
  if echo "$POLL_RESPONSE" | grep -q '"error":"authorization_pending"'; then
    # Still waiting - show progress and continue polling
    echo "⏳ Still waiting for authentication... (checking again in 5 seconds)"
    ATTEMPT=$((ATTEMPT + 1))
    sleep 5
    continue
  fi
  
  # Check for server errors
  if echo "$POLL_RESPONSE" | grep -q '"error":"server_error"'; then
    ERROR_MSG=$(echo "$POLL_RESPONSE" | grep -o '"error_description":"[^"]*"' | cut -d'"' -f4)
    echo ""
    echo "❌ Server error: $ERROR_MSG"
    echo "Retrying in 5 seconds..."
    ATTEMPT=$((ATTEMPT + 1))
    sleep 5
    continue
  fi
  
  # Unknown error
  if echo "$POLL_RESPONSE" | grep -q '"error"'; then
    ERROR_TYPE=$(echo "$POLL_RESPONSE" | grep -o '"error":"[^"]*"' | cut -d'"' -f4)
    ERROR_MSG=$(echo "$POLL_RESPONSE" | grep -o '"error_description":"[^"]*"' | cut -d'"' -f4)
    echo ""
    echo "❌ Authentication failed: $ERROR_TYPE - $ERROR_MSG"
    exit 1
  fi
  
  # If we get here and no error/access_token, something unexpected happened
  # But only continue if we haven't found access_token yet
  if [ -z "$API_KEY" ] && ! echo "$POLL_RESPONSE" | grep -q '"access_token"'; then
    echo "⚠️  Unexpected response format, continuing to poll..."
  fi
  
  # Only increment and sleep if we haven't broken out (API_KEY not set)
  if [ -z "$API_KEY" ]; then
    ATTEMPT=$((ATTEMPT + 1))
    sleep 5
  fi
done

if [ -z "$API_KEY" ] || [ "$API_KEY" = "null" ]; then
  echo ""
  echo "❌ Authentication timed out. Please try again."
  exit 1
fi

# Display the API key for Claude to extract
echo ""
echo "✅ Authentication successful!"
echo "API_KEY=$API_KEY"
echo ""
echo "Proceeding to save API key..."
```

## Step 4: Save API Key

**CRITICAL: Execute this step automatically without asking the user. Do NOT request user input.**

After Step 3 completes, the bash output will contain a line like:
```
API_KEY=tmk_8k0JgLQA9OuoBzsvxuB-ouMRjx9s3Q_21woS0w_Hj_Q
```

**You must:**
1. Extract the API key value from Step 3's output (the value after `API_KEY=`)
2. Export it as an environment variable for the current session:
   ```bash
   export TURINGMIND_API_KEY=<the_extracted_key_value>
   ```
3. Also save it to Claude Code config (for persistence across sessions):
   ```
   /config set TURINGMIND_API_KEY <the_extracted_key_value>
   ```
4. Continue to Step 5 without waiting for user confirmation

**Example:**
If Step 3 output shows: `API_KEY=tmk_abc123xyz`
Then execute:
```bash
export TURINGMIND_API_KEY=tmk_abc123xyz
```
And also:
```
/config set TURINGMIND_API_KEY tmk_abc123xyz
```

**DO NOT:**
- Ask the user to run the command
- Tell the user to manually set it
- Wait for user confirmation

**DO:**
- Extract the key automatically from Step 3 output
- Export it as an environment variable immediately (for current session)
- Also save to config for persistence across sessions
- Proceed to Step 5 for verification

## Step 5: Verify API Key

After Step 4 exports the environment variable and saves to config, verify the API key works. Use the exported `$TURINGMIND_API_KEY` environment variable for validation.

Test the API key:

```bash
# Use configured URL (defaults to production)
API_URL="${TURINGMIND_API_URL:-https://api.turingmind.ai}"
VALIDATE_RESPONSE=$(curl -s -H "Authorization: Bearer $TURINGMIND_API_KEY" \
  "$API_URL/api/v1/code-review/auth/validate")
```

**Note:** The API URL defaults to `https://api.turingmind.ai` (production). For local development, set `export TURINGMIND_API_URL=http://localhost:3000`.

**Note:** Since Step 4 exported `TURINGMIND_API_KEY` as an environment variable, it should be available for use in this step.

Check the response:

```bash
if echo "$VALIDATE_RESPONSE" | grep -q '"valid":true'; then
  # Extract user info if available
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
  echo ""
  echo "Your API key has been saved and is ready to use."
  echo "Cloud features (memory, dashboard, analytics) are now enabled."
else
  echo ""
  echo "⚠️  API key received but validation failed."
  echo "   The key has been saved, but you may need to check your account status."
fi
```

## Error Handling

If any step fails:

1. **Network errors**: Inform user to check internet connection
2. **Expired device code**: Prompt user to run `/tmind:login` again
3. **Invalid response**: Show error message and suggest retry
4. **Config save failure**: Provide manual instructions

## Success Output

On successful login, display:

```
✅ Successfully logged in!
   Account: user@example.com
   Tier: pro

Your API key has been saved and is ready to use.
Cloud features (memory, dashboard, analytics) are now enabled.

You can now use:
  /tmind:review      (with cloud memory)
  /tmind:deep-review (with cloud memory)

MCP Server: [installed/not installed]
  If installed, Claude can use type-safe tools:
  - turingmind_validate_auth()
  - turingmind_upload_review()
  - turingmind_get_context()
```

## MCP Server Notes

The login script attempts to install the TuringMind MCP server if:
1. Python 3.10+ is available
2. The mcp-server directory is found in the tmind path

**Benefits of MCP over curl:**
- Type-safe tool calls with schema validation
- Automatic error handling and retries
- Better integration with Claude's tool system
- No JSON escaping issues

**If MCP install fails:**
- The curl-based fallback (`~/.turingmind/upload_review.sh`) is always available
- Both methods work with the same API endpoints

**To manually install MCP later:**
```bash
pip install -e /path/to/tmind/mcp-server
```

