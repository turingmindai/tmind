#!/bin/bash
set -e

# Default API URL (use localhost for testing)
API_URL="${TURINGMIND_API_URL:-http://localhost:3000}"

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
elif command -v xdg-open &> /dev/null; then
    xdg-open "$VERIFICATION_URL" 2>/dev/null &
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

echo ""
echo "API key saved to ~/.turingmind/config"

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
