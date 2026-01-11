---
allowed-tools: Bash, Read
description: Deep comprehensive code review with full context analysis
---

This command routes to the appropriate strategy based on your cloud connection status.

## Step 1: Detect Mode & Find Strategy

```bash
# Load API key from config file (persists across sessions)
[ -f ~/.turingmind/config ] && source ~/.turingmind/config

if [ -n "$TURINGMIND_API_KEY" ] && [ "$TURINGMIND_API_KEY" != "" ]; then
  echo "☁️  Cloud Mode (API key detected)"
  echo "MODE=cloud"
  STRATEGY_FILE="deep-review-cloud.md"
else
  echo "💻 Local Mode (no API key)"
  echo "MODE=local"
  echo "Run /tmind:login to enable cloud features."
  STRATEGY_FILE="deep-review-local.md"
fi

# Find the strategy file in plugin cache
STRATEGY_PATH=$(find ~/.claude/plugins/cache -name "$STRATEGY_FILE" -path "*tmind*" 2>/dev/null | head -1)

if [ -n "$STRATEGY_PATH" ]; then
  echo "STRATEGY_PATH=$STRATEGY_PATH"
else
  echo "⚠️ Strategy file not found in plugin cache"
fi
```

## Step 2: Execute Strategy

Read and execute the strategy file found above. The strategy file contains the full review workflow including:
- Fetching memory context (cloud only)
- Running review agents in parallel
- Architecture and impact analysis
- Scoring and filtering issues
- Presenting results with architectural notes
- Uploading to cloud (cloud only)

**Execute the strategy by reading the file at STRATEGY_PATH:**

- If `MODE=cloud`: Read `~/.claude/plugins/cache/tmind/tmind/*/strategies/deep-review-cloud.md`
- If `MODE=local`: Read `~/.claude/plugins/cache/tmind/tmind/*/strategies/deep-review-local.md`

**Important:** After reading the strategy file, execute ALL steps/phases in it including the final upload phase.
