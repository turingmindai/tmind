# Testing TuringMind Plugin Locally

This guide shows how to install and test the TuringMind plugin locally before pushing changes.

## Environment Setup for Local Development

**Important:** The plugin defaults to production (`https://api.turingmind.ai`). For local testing, set:

```bash
export TURINGMIND_API_URL=http://localhost:3000
```

Add this to your shell profile (`~/.zshrc` or `~/.bashrc`) to persist across sessions.

## Prerequisites

1. **Backend running locally:**
   ```bash
   # In repochatindex directory
   cd /Users/turingmindai/Documents/VSCodeProjects/Turingmind-App/repochatindex
   python run_fastapi.py
   # Backend should be running on http://localhost:8000
   ```

2. **Frontend running locally:**
   ```bash
   # In repochat-ui directory
   cd /Users/turingmindai/Documents/VSCodeProjects/Turingmind-App/repochat-ui
   npm run dev
   # Frontend should be running on http://localhost:3000
   ```

## Step 1: Install Plugin Locally

### Option A: Install from Local Path (Recommended for Development)

In Claude Code terminal, try:
```bash
# Try pointing to the plugin directory
/plugin install file:///Users/turingmindai/Documents/VSCodeProjects/tmind/plugins/tmind
```

If that doesn't work, Claude Code might cache plugins. Try:
```bash
# List installed plugins
/plugin list

# If tmind is already installed, it should use files from disk
# If not, you may need to install from marketplace first, then modify files
```

### Option B: Install from Marketplace, Then Modify

1. Install from marketplace:
   ```bash
   /plugin marketplace add turingmindai/tmind
   /plugin install turingmind@tmind
   ```

2. The plugin files are typically cached. For local testing, you can:
   - Modify the installed plugin files directly (location depends on Claude Code)
   - Or test using the commands directly (Claude Code reads from the installed location)

## Step 2: Login to Get API Key

1. **Run the login command:**
   ```bash
   /tmind:login
   ```

2. **Or test manually using the test script:**
   ```bash
   cd /Users/turingmindai/Documents/VSCodeProjects/tmind
   ./test_login.sh
   ```

3. **After login completes**, the API key will be saved to Claude Code config:
   ```
   TURINGMIND_API_KEY=tmk_...
   ```

## Step 3: Test Review on Your Repo

1. **Navigate to a repo with uncommitted changes:**
   ```bash
   cd /path/to/your/repo
   # Make sure you have some uncommitted changes
   git status
   ```

2. **Run the review command:**
   ```bash
   /tmind:review
   ```

3. **The review will:**
   - Analyze your uncommitted changes
   - Find issues and suggest fixes
   - **Automatically upload results to cloud** (if `TURINGMIND_API_KEY` is set)
   - Show "🧠 Synced to TuringMind" at the end if upload succeeded

## Step 4: Verify Results Were Uploaded

Check the backend logs to see if the review was received:

```bash
# In repochatindex directory, check logs
tail -f logs/api_key_audit.log
# Or check FastAPI console output
```

The review should be posted to: `POST /api/v1/code-review/reviews`

## Step 5: Test Deep Review

For a more thorough analysis:

```bash
/tmind:deep-review
```

This will:
- Do a deeper analysis
- Check architecture compliance
- Upload results to cloud

## Troubleshooting

### Plugin Not Loading Changes

If changes to `login.md` or other files aren't being picked up:

1. **Check if plugin is cached:**
   - Claude Code may cache plugin files
   - Try restarting Claude Code
   - Or reinstall the plugin

2. **Test directly:**
   - You can test the login flow using `./test_login.sh` directly
   - This bypasses the plugin system

### API Key Not Working

1. **Verify API key is set:**
   ```bash
   echo $TURINGMIND_API_KEY
   ```

2. **Test API key validation:**
   ```bash
   curl -s -H "Authorization: Bearer $TURINGMIND_API_KEY" \
     "http://localhost:3000/api/v1/code-review/auth/validate"
   ```

### Results Not Uploading

1. **Check API key is set** (required for uploads)
2. **Check backend is running** on localhost:8000
3. **Check frontend proxy** is working (localhost:3000 → localhost:8000)
4. **Check backend logs** for errors

## Quick Test Checklist

- [ ] Backend running on localhost:8000
- [ ] Frontend running on localhost:3000  
- [ ] Plugin installed (or using test script)
- [ ] Login completed and API key saved
- [ ] Repo with uncommitted changes ready
- [ ] Review command runs successfully
- [ ] Results appear in backend logs

## Next Steps

After testing locally:
1. Commit your changes
2. Push to the repository
3. The plugin will be available from the marketplace with your updates

