---
allowed-tools: Bash(curl:*), Bash(sleep:*), Bash(echo:*), Bash(grep:*), Bash(cut:*), Bash(mkdir:*), Bash(cat:*), Read, Write
description: Login to TuringMind and get API key for cloud features
---

Login to TuringMind using device code flow to get your API key for cloud features (memory, dashboard, analytics).

## Step 1: Start CLI Authentication

Call the backend to initiate device code authentication:

```bash
API_URL="${TURINGMIND_API_URL:-https://api-dev.turingmind.ai}"
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

Poll the token endpoint every 5 seconds until authentication is complete:

```bash
MAX_ATTEMPTS=120  # 10 minutes max (120 * 5 seconds)
ATTEMPT=0
API_KEY=""

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
  POLL_RESPONSE=$(curl -s "$API_URL/api/v1/cli/token?device_code=$DEVICE_CODE")
  
  # Check if we got an access token (success)
  if echo "$POLL_RESPONSE" | grep -q '"access_token"'; then
    # Extract API key
    if command -v jq &> /dev/null; then
      API_KEY=$(echo "$POLL_RESPONSE" | jq -r '.access_token')
    else
      API_KEY=$(echo "$POLL_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
    fi
    
    if [ -n "$API_KEY" ] && [ "$API_KEY" != "null" ]; then
      break
    fi
  fi
  
  # Check for expired error
  if echo "$POLL_RESPONSE" | grep -q '"error":"expired"'; then
    echo ""
    echo "❌ Authentication expired. Please run /tmind:login again."
    exit 1
  fi
  
  # Check for other errors
  if echo "$POLL_RESPONSE" | grep -q '"error":"authorization_pending"'; then
    # Still waiting - continue polling
    ATTEMPT=$((ATTEMPT + 1))
    sleep 5
    continue
  fi
  
  # Unknown error
  if echo "$POLL_RESPONSE" | grep -q '"error"'; then
    ERROR_MSG=$(echo "$POLL_RESPONSE" | grep -o '"error_description":"[^"]*"' | cut -d'"' -f4)
    echo ""
    echo "❌ Authentication failed: $ERROR_MSG"
    exit 1
  fi
  
  ATTEMPT=$((ATTEMPT + 1))
  sleep 5
done

if [ -z "$API_KEY" ] || [ "$API_KEY" = "null" ]; then
  echo ""
  echo "❌ Authentication timed out. Please try again."
  exit 1
fi

# Display the API key for Claude to use
echo "API_KEY=$API_KEY"
```

## Step 4: Save API Key to Claude Code Config

After Step 3 completes successfully and you have the API key value, save it using Claude Code's config system.

**Action Required:** Extract the API key value from the bash output (it will be displayed as `API_KEY=...`) and execute this Claude Code command:

```
/config set TURINGMIND_API_KEY <extracted_api_key_value>
```

**Example:** If the bash output shows `API_KEY=tmk_abc123...`, then execute:
```
/config set TURINGMIND_API_KEY tmk_abc123...
```

**Note:** The `/config set` command is a Claude Code command that must be executed directly by Claude, not within a bash script.

## Step 5: Verify API Key

After saving the API key in Step 4, verify it works by validating it. The API key should now be available as `$TURINGMIND_API_KEY` environment variable (set by `/config set`).

Test the API key:

```bash
API_URL="${TURINGMIND_API_URL:-https://api-dev.turingmind.ai}"
VALIDATE_RESPONSE=$(curl -s -H "Authorization: Bearer $TURINGMIND_API_KEY" \
  "$API_URL/api/v1/code-review/auth/validate")
```

**Note:** If `$TURINGMIND_API_KEY` is not available, extract it from Step 3's output where it was displayed as `API_KEY=...`.

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
```

