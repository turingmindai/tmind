---
allowed-tools: Bash(pip:*), Bash(pipx:*), Bash(python*:*), Bash(cat:*), Bash(mkdir:*), Bash(chmod:*), Bash(echo:*), Bash(command:*), Bash(brew:*)
description: One-time setup for TuringMind MCP server
---

One-time setup to install the TuringMind MCP server and configure Claude Desktop.

**Run this once after installing the tmind skill, then restart Claude.**

## Step 1: Check Python Version

```bash
echo "🧠 TuringMind Setup"
echo "==================="
echo ""

PYTHON_CMD=""
for cmd in python3.12 python3.11 python3.10 python3; do
    if command -v $cmd &> /dev/null; then
        VERSION=$($cmd -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null)
        MAJOR=$(echo $VERSION | cut -d. -f1)
        MINOR=$(echo $VERSION | cut -d. -f2)
        if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 10 ]; then
            PYTHON_CMD=$cmd
            echo "✅ Found Python $VERSION ($cmd)"
            break
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo "❌ Python 3.10+ is required but not found"
    echo ""
    echo "Install Python 3.10+ using one of these methods:"
    echo "  • macOS: brew install python@3.12"
    echo "  • Ubuntu: sudo apt install python3.12"
    echo "  • Windows: Download from python.org"
    exit 1
fi
```

## Step 2: Install MCP Server

```bash
echo ""
echo "📦 Installing TuringMind MCP Server..."

# Check if already installed
if $PYTHON_CMD -c "import turingmind_mcp" 2>/dev/null; then
    echo "   ✅ Already installed"
else
    # Try multiple installation methods
    INSTALLED=false
    
    # Method 1: pipx (recommended for CLI tools, avoids system Python issues)
    if command -v pipx &> /dev/null; then
        echo "   Trying pipx..."
        if pipx install turingmind-mcp 2>/dev/null; then
            INSTALLED=true
            echo "   ✅ Installed via pipx"
        elif pipx install "git+https://github.com/turingmindai/tmind.git#subdirectory=mcp-server" 2>/dev/null; then
            INSTALLED=true
            echo "   ✅ Installed via pipx (from GitHub)"
        fi
    fi
    
    # Method 2: pip with --user flag
    if [ "$INSTALLED" = false ]; then
        echo "   Trying pip --user..."
        if $PYTHON_CMD -m pip install --user turingmind-mcp --quiet 2>/dev/null; then
            INSTALLED=true
            echo "   ✅ Installed via pip --user"
        elif $PYTHON_CMD -m pip install --user "git+https://github.com/turingmindai/tmind.git#subdirectory=mcp-server" --quiet 2>/dev/null; then
            INSTALLED=true
            echo "   ✅ Installed via pip --user (from GitHub)"
        fi
    fi
    
    # Method 3: pip (system, may fail on managed environments)
    if [ "$INSTALLED" = false ]; then
        echo "   Trying pip..."
        if $PYTHON_CMD -m pip install turingmind-mcp --quiet 2>/dev/null; then
            INSTALLED=true
            echo "   ✅ Installed via pip"
        fi
    fi
    
    if [ "$INSTALLED" = false ]; then
        echo "   ❌ Installation failed"
        echo ""
        echo "   Try manually:"
        echo "     pipx install turingmind-mcp"
        echo "   or:"
        echo "     pip install --user turingmind-mcp"
        exit 1
    fi
fi
```

## Step 3: Find MCP Server Python Path

```bash
echo ""
echo "🔍 Locating MCP server..."

# Find the Python that has turingmind_mcp installed
MCP_PYTHON=""

# Check pipx venv first
PIPX_PYTHON="$HOME/.local/pipx/venvs/turingmind-mcp/bin/python"
if [ -f "$PIPX_PYTHON" ] && $PIPX_PYTHON -c "import turingmind_mcp" 2>/dev/null; then
    MCP_PYTHON="$PIPX_PYTHON"
    echo "   ✅ Found in pipx venv: $MCP_PYTHON"
fi

# Check system Python
if [ -z "$MCP_PYTHON" ] && $PYTHON_CMD -c "import turingmind_mcp" 2>/dev/null; then
    MCP_PYTHON=$(which $PYTHON_CMD)
    echo "   ✅ Found in system Python: $MCP_PYTHON"
fi

if [ -z "$MCP_PYTHON" ]; then
    echo "   ❌ Could not locate turingmind_mcp module"
    exit 1
fi
```

## Step 4: Configure Claude Desktop

```bash
echo ""
echo "🔌 Configuring Claude Desktop..."

# Detect Claude Desktop config path
if [[ "$OSTYPE" == "darwin"* ]]; then
    CLAUDE_CONFIG_DIR="$HOME/Library/Application Support/Claude"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "win32" ]]; then
    CLAUDE_CONFIG_DIR="${APPDATA:-$HOME/AppData/Roaming}/Claude"
else
    CLAUDE_CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/Claude"
fi

CLAUDE_CONFIG="$CLAUDE_CONFIG_DIR/claude_desktop_config.json"

# Check if Claude Desktop is installed
if [ ! -d "$CLAUDE_CONFIG_DIR" ]; then
    echo "   ⚠️  Claude Desktop config directory not found"
    echo "   Creating: $CLAUDE_CONFIG_DIR"
    mkdir -p "$CLAUDE_CONFIG_DIR"
fi

# Read existing API key if available
API_KEY=""
API_URL="https://api.turingmind.ai"
if [ -f ~/.turingmind/config ]; then
    source ~/.turingmind/config 2>/dev/null
    API_KEY="${TURINGMIND_API_KEY:-}"
    API_URL="${TURINGMIND_API_URL:-https://api.turingmind.ai}"
fi

# Use Python to safely merge JSON config
$PYTHON_CMD << MERGE_SCRIPT
import json
import os

config_path = "$CLAUDE_CONFIG"
mcp_python = "$MCP_PYTHON"
api_key = "$API_KEY" or "YOUR_API_KEY_HERE"
api_url = "$API_URL"

# Read existing config or create new
try:
    with open(config_path) as f:
        config = json.load(f)
    print("   Found existing config")
except (FileNotFoundError, json.JSONDecodeError):
    config = {}
    print("   Creating new config")

# Backup if exists
if os.path.exists(config_path):
    backup_path = config_path + ".backup"
    with open(backup_path, 'w') as f:
        json.dump(config, f, indent=2)
    print(f"   Backup saved to: {backup_path}")

# Add TuringMind MCP server
if 'mcpServers' not in config:
    config['mcpServers'] = {}

config['mcpServers']['turingmind'] = {
    "command": mcp_python,
    "args": ["-m", "turingmind_mcp.server"],
    "env": {
        "TURINGMIND_API_KEY": api_key,
        "TURINGMIND_API_URL": api_url
    }
}

# Write config
with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)

print("   ✅ Claude Desktop configured")
MERGE_SCRIPT
```

## Step 5: Install Helper Scripts

```bash
echo ""
echo "📝 Installing helper scripts..."

mkdir -p ~/.turingmind

# Install upload_review.sh fallback script
cat > ~/.turingmind/upload_review.sh << 'UPLOAD_SCRIPT'
#!/bin/bash
API_URL="${TURINGMIND_API_URL:-https://api.turingmind.ai}"
[ -z "$TURINGMIND_API_KEY" ] && [ -f ~/.turingmind/config ] && source ~/.turingmind/config
if [ -z "$TURINGMIND_API_KEY" ]; then
  echo "⚠️ TURINGMIND_API_KEY not set" >&2; exit 1
fi
REVIEW_JSON="${1:-$(cat)}"
curl -s -X POST "$API_URL/api/v1/code-review/reviews" \
  -H "Authorization: Bearer $TURINGMIND_API_KEY" \
  -H "Content-Type: application/json" \
  -d "$REVIEW_JSON"
UPLOAD_SCRIPT
chmod +x ~/.turingmind/upload_review.sh
echo "   ✅ Helper scripts installed"
```

## Step 6: Summary

```bash
echo ""
echo "=========================================="
echo "✅ TuringMind Setup Complete!"
echo "=========================================="
echo ""
echo "MCP Server: $MCP_PYTHON"
echo "Config: $CLAUDE_CONFIG"
if [ -n "$API_KEY" ] && [ "$API_KEY" != "YOUR_API_KEY_HERE" ]; then
    echo "API Key: Configured ✅"
else
    echo "API Key: Not set (run /tmind:login after restart)"
fi
echo ""
echo "NEXT STEPS:"
echo "1. Restart Claude Desktop (Cmd+Q then reopen)"
echo "2. Run /tmind:login to authenticate"
echo "3. Start reviewing code with /tmind:review"
echo ""
```

## Troubleshooting

If setup fails:

| Issue | Solution |
|-------|----------|
| Python not found | Install Python 3.10+: `brew install python@3.12` |
| pip install fails | Use pipx: `brew install pipx && pipx install turingmind-mcp` |
| Permission denied | Use `pip install --user` or pipx |
| Claude not found | Install Claude Desktop from claude.ai/download |

## Manual Installation

If automatic setup doesn't work:

```bash
# Install MCP server
pipx install turingmind-mcp

# Find Python path
PYTHON_PATH=$(pipx list --json | python3 -c "import sys,json; print(json.load(sys.stdin)['venvs']['turingmind-mcp']['metadata']['main_package']['app_paths'][0]['path'])" 2>/dev/null)
# Or use: ~/.local/pipx/venvs/turingmind-mcp/bin/python

# Add to Claude config manually
# Edit: ~/Library/Application Support/Claude/claude_desktop_config.json
```

