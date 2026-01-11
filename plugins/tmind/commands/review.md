---
allowed-tools: Bash, Read
description: Quick code review for uncommitted local changes
---

This command routes to the appropriate strategy based on your cloud connection status.

## Strategy Selection

First load the TuringMind config (contains API key), then check which strategy to use.

```bash
# Load API key from config file (persists across sessions)
[ -f ~/.turingmind/config ] && source ~/.turingmind/config

if [ -n "$TURINGMIND_API_KEY" ] && [ "$TURINGMIND_API_KEY" != "" ]; then
  echo "Cloud key detected. Using Cloud Strategy..."
  echo "STRATEGY=cloud"
else
  echo "No cloud key detected. Using Local Strategy..."
  echo "STRATEGY=local"
  echo "Run /tmind:login to enable cloud features."
fi
```

### Next Steps

Run the file returned by the strategy selection above:

- If **Local**: `@strategies/review-local.md` (No internet access required)
- If **Cloud**: `@strategies/review-cloud.md` (Syncs results to cloud)
