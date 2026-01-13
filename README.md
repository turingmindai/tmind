<div align="center">

# 🧠 TuringMind Code Review

**Catch bugs before they catch you.**

A [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skill and [Cursor IDE](https://cursor.sh) integration for AI-powered code review of your uncommitted changes. Install from the marketplace, review instantly.

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Claude Code Skill](https://img.shields.io/badge/Claude_Code-Skill-blueviolet)](https://docs.anthropic.com/en/docs/claude-code)
[![Install from Marketplace](https://img.shields.io/badge/Marketplace-Install-green)](https://github.com/turingmindai/tmind)

[Quick Start](#-quick-start) • [Features](#-features) • [Examples](#-example-output) • [Contributing](#-contributing)

</div>

---

## 📦 What is This?

**TuringMind Code Review** is a **Claude Code skill** and **Cursor IDE integration** — a reusable, shareable plugin that extends Claude Code and Cursor with specialized code review capabilities. 

- **Claude Code:** Skills are installed via the built-in plugin marketplace and add new slash commands to your Claude Code environment.
- **Cursor IDE:** Uses MCP (Model Context Protocol) tools and Cursor Rules for seamless integration.

---

## 💡 Why TuringMind?

You're about to commit. ESLint passes. Types check. Tests are green.

**But there's a SQL injection on line 23.**

TuringMind catches what linters miss:
- 🐛 Logic errors that compile but fail at runtime
- 🔐 Security vulnerabilities (OWASP Top 10)
- 📐 Architecture violations your team agreed to avoid
- 🎯 Issues *in your diff*, not pre-existing tech debt

> "Like having a senior engineer review every commit — in seconds."

---

## 🚀 Quick Start

### Supported IDEs

TuringMind works with:

- **Claude Code** (Claude Desktop) - Global MCP configuration
- **Cursor IDE** - Project-specific MCP configuration

Both IDEs are automatically detected and configured during setup.

### Install from Marketplace (Claude Code)

Open Claude Code in your terminal and run:

```bash
# Step 1: Add the TuringMind marketplace
/plugin marketplace add turingmindai/tmind
```

```bash
# Step 2: Install the skill
/plugin install tmind@tmind
```

```bash
# Step 3: One-time setup (installs MCP server, configures IDE)
/tmind:setup
```

```bash
# Step 4: Restart your IDE (Claude Desktop or Cursor), then login
/tmind:login
```

### Use the Commands (Claude Code)

```bash
# Quick review — fast, pre-commit check
/tmind:review

# Deep review — thorough analysis before PRs
/tmind:deep-review
```

### Use in Cursor IDE

In Cursor, use natural language in the chat:

```
Review my staged changes for bugs and security issues
```

Or use the `cursor-agent` CLI directly:

```bash
# Quick review
cursor-agent -p "Run TuringMind code review on my staged changes"

# Deep review
cursor-agent -p "Run TuringMind deep code review including architecture analysis"
```

Cursor Rules (`.cursor/rules/tmind-*.md`) guide the AI to follow the TuringMind workflow.

That's it. Reviews work locally. Cloud features (memory, analytics) require login.

### Requirements

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) or [Cursor IDE](https://cursor.sh) installed and configured
- Git repository with uncommitted changes

### Optional: Git Hooks

Git hooks work with **both** Claude Code and Cursor IDE. They automatically detect which CLI is available.

#### Pre-Commit Hook (Recommended)

Automatically run code review on **staged changes** before every commit:

```bash
# Manual install
cp hooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

What it does:
- 🔴 **Critical issues (95-100)** → Blocks the commit
- 🟠 **Warning issues (80-94)** → Shows warning, allows commit
- ✅ **No issues** → Commit proceeds normally
- 🔄 **Detects CLI** → Uses `claude` or `cursor-agent` automatically

To uninstall: `rm .git/hooks/pre-commit`

#### Pre-Push Hook

Automatically run code review before every `git push`:

```bash
# One-liner install (run in your project)
curl -sSL https://raw.githubusercontent.com/turingmindai/tmind/dev/scripts/install-hooks.sh | bash
```

What it does:
- 🔴 **Critical issues (95-100)** → Blocks the push
- 🟠 **Warning issues (80-94)** → Shows warning, allows push
- ✅ **No issues** → Push proceeds normally
- 🔄 **Detects CLI** → Uses `claude` or `cursor-agent` automatically

To uninstall: `rm .git/hooks/pre-push`

### Optional: TuringMind Pro (Cloud Features)

Supercharge your reviews with cloud-powered memory and analytics:

```bash
# Easy login flow (recommended)
/tmind:login

# Or manually set API key
/config set TURINGMIND_API_KEY tm_sk_your_key_here
```

The `/tmind:login` command will:
1. Open a browser for authentication
2. Generate and save your API key automatically
3. Enable cloud features immediately

**What Pro enables:**

| Feature | Free | Pro |
|---------|------|-----|
| Local code review | ✅ | ✅ |
| All review agents | ✅ | ✅ |
| **Memory** (learns from past reviews) | ❌ | ✅ |
| **Dashboard** (metrics & trends) | ❌ | ✅ |
| **False positive learning** | ❌ | ✅ |
| **Team conventions sync** | ❌ | ✅ |
| **Hotspot detection** | ❌ | ✅ |

**Privacy:** Your code never leaves your machine. We only sync issue metadata (file paths, line numbers, issue types) — never source code.

---

## ✨ Features

### Two Review Modes

| | Quick Review | Deep Review |
|---|---|---|
| **Command** | `/tmind:review` | `/tmind:deep-review` |
| **Speed** | ⚡ Fast | 🔍 Thorough |
| **Best for** | Pre-commit checks | Before PRs |
| **Agents** | 4 Sonnet | 6 Sonnet + 3 Haiku |
| **Architecture analysis** | — | ✅ |
| **Impact analysis** | — | ✅ |
| **Test coverage check** | — | ✅ |

### What Gets Checked

<table>
<tr>
<td width="50%">

**🐛 Bugs & Logic**
- Null/undefined access
- Off-by-one errors
- Race conditions
- Resource leaks

</td>
<td width="50%">

**🔐 Security (OWASP Top 10)**
- SQL/Command injection
- XSS vulnerabilities
- Hardcoded secrets
- Auth bypass

</td>
</tr>
<tr>
<td>

**📐 Architecture** *(deep only)*
- Pattern consistency
- Abstraction violations
- Circular dependencies

</td>
<td>

**🎯 Project Rules**
- CLAUDE.md compliance
- Team conventions
- Naming standards

</td>
</tr>
</table>

### Smart Filtering

TuringMind won't waste your time. It automatically filters:
- ❌ Pre-existing issues (not your fault)
- ❌ Linter territory (let ESLint handle it)
- ❌ Pedantic nitpicks (no "add semicolon" spam)
- ❌ Intentional changes (you meant to do that)

---

## 📸 Example Output

### Quick Review

```
## Code Review

**Summary:** Reviewed 3 files, 47 lines changed

### Critical (95-100) 🔴
Must fix before committing:

1. **api/auth.ts:23** - SQL injection vulnerability

   User input directly interpolated into SQL query.
   
   ```diff
   - const query = `SELECT * FROM users WHERE email = '${email}'`;
   + const query = `SELECT * FROM users WHERE email = $1`;
   + const result = await db.query(query, [email]);
   ```

### Warning (80-94) 🟠
Should fix:

1. **utils/parse.ts:15** - Unchecked null access

   `data.user.name` accessed without null check. Will throw if user is undefined.
   
   Suggested fix: `data.user?.name ?? 'Unknown'`
```

### Deep Review

Includes everything above, plus:

```
### Architectural Notes 📐
- Pattern consistency: ✅ Follows existing patterns
- Test coverage: ⚠️ No tests for new `validateEmail` function
- Documentation: ✅ JSDoc comments present

### Impact Analysis 💥
- **Affected files:** `routes/login.ts`, `middleware/auth.ts`
- **Blast radius:** Auth flow - high business impact
- **Breaking changes:** None detected
```

---

## 🏗️ Architecture

Modular design for easy customization:

```text
tmind/
├── plugins/tmind/          # Claude Code skill files
│   ├── commands/           # Review orchestration
│   │   ├── review.md
│   │   ├── deep-review.md
│   │   ├── login.md
│   │   └── setup.md        # One-time MCP setup
│   ├── agents/             # Specialized reviewers
│   │   ├── bugs.md
│   │   ├── security.md
│   │   ├── compliance.md
│   │   ├── architecture.md
│   │   ├── index.md        # Agent router
│   │   └── language-*.md
│   └── templates/          # Output & filtering
│       ├── output-format.md
│       ├── memory-context.md   # Cloud memory injection
│       └── false-positive-rules.md
├── .cursor/                # Cursor IDE integration
│   └── rules/
│       ├── tmind-review.md     # Review workflow for Cursor
│       └── tmind-agents.md     # Agent prompts for Cursor
├── hooks/                  # Git hooks (both IDEs)
│   ├── pre-commit
│   └── pre-push
└── scripts/
    ├── install-hooks.sh
    └── tmind-review        # CLI wrapper
```

### Extending

```bash
# Add Go support
cp agents/language-typescript.md agents/language-go.md
# Edit with Go-specific checks

# Add custom security rules
# Edit agents/security.md
```

---

## 🧠 TuringMind Pro Features

### Memory System

When Pro is enabled, TuringMind remembers:

| Memory Type | How It Helps |
|-------------|--------------|
| **False Positives** | "You dismissed this pattern 5 times — skipping" |
| **Hotspot Files** | "This file has had 12 issues this month — extra scrutiny" |
| **Team Conventions** | "Your team prefers optional chaining over null checks" |
| **Open Issues** | "Check if this commit fixes the SQL injection on line 45" |

### Dashboard

Track your code quality over time:
- 📈 Issues found/fixed trends
- 🔥 Hotspot files (where bugs cluster)
- 📊 Team metrics and leaderboards
- 🎯 Quality score per repository

### How Data Flows

```
┌─────────────────────┐      ┌─────────────────────────┐
│   Your Machine      │      │   TuringMind Cloud      │
│   (Code stays here) │      │   (Metadata only)       │
├─────────────────────┤      ├─────────────────────────┤
│                     │      │                         │
│  📁 Source code     │  ❌  │  Never sent             │
│  📝 File paths      │  ──▶ │  ✅ For tracking        │
│  🔢 Line numbers    │  ──▶ │  ✅ For analytics       │
│  🏷️ Issue types     │  ──▶ │  ✅ For learning        │
│  📊 Review metrics  │  ──▶ │  ✅ For dashboard       │
│                     │      │                         │
│  ◀── Memory context │  ◀── │  False positives, etc.  │
│                     │      │                         │
└─────────────────────┘      └─────────────────────────┘
```

---

## 🔧 Troubleshooting

### Git Hooks Issues

#### Hooks Not Running

**Problem:** Git hooks don't execute when committing/pushing.

**Solutions:**
```bash
# Check if hooks are installed
ls -la .git/hooks/pre-commit .git/hooks/pre-push

# Reinstall hooks
cp hooks/pre-commit .git/hooks/pre-commit
cp hooks/pre-push .git/hooks/pre-push
chmod +x .git/hooks/pre-commit .git/hooks/pre-push
```

#### "No supported CLI found" Warning

**Problem:** Hooks skip review because neither `claude` nor `cursor-agent` is found.

**Solutions:**
- **Claude Code:** `npm install -g @anthropic-ai/claude-code`
- **Cursor:** Install Cursor IDE (includes `cursor-agent` CLI)
- Verify installation: `which claude` or `which cursor-agent`

#### Review Times Out

**Problem:** Review hangs and times out after 5 minutes.

**Solutions:**
- Check network connectivity
- Review may be too large - try reviewing smaller changesets
- Increase timeout: `export TMIND_TIMEOUT=600` (10 minutes)
- Check CLI authentication status

### Cursor IDE Issues

#### "Cursor CLI found but not authenticated"

**Problem:** Git hooks fail because `cursor-agent` isn't authenticated.

**Solutions:**

**Option 1: API Key (Recommended for Git Hooks)**
```bash
# Generate API key in Cursor dashboard:
# Settings > Integrations > User API Keys

# Set in your shell profile (~/.bashrc, ~/.zshrc)
export CURSOR_API_KEY=your_api_key_here

# Or set per-command
CURSOR_API_KEY=your_key git commit -m "fix: something"
```

**Option 2: Browser Login**
```bash
# Login interactively (one-time)
cursor-agent login

# Verify authentication
cursor-agent status
```

**Note:** Browser login may not work in CI/CD environments. Use API keys instead.

#### Cursor Rules Not Working

**Problem:** Cursor doesn't follow TuringMind review workflow.

**Solutions:**
- Ensure `.cursor/rules/tmind-review.md` exists in project root
- Ensure `.cursor/rules/tmind-agents.md` exists
- Restart Cursor IDE after adding rules
- Check Cursor Rules are enabled in settings

### Claude Code Issues

#### "Claude CLI not found"

**Problem:** `claude` command not available.

**Solutions:**
```bash
# Install Claude Code CLI
npm install -g @anthropic-ai/claude-code

# Verify installation
claude --version
```

#### MCP Server Not Found

**Problem:** Setup fails to find `turingmind_mcp` module.

**Solutions:**
```bash
# Reinstall MCP server
pipx install turingmind-mcp

# Or with pip
pip install --user turingmind-mcp

# Verify installation
python -m turingmind_mcp.server --help
```

### Authentication Issues

#### API Key Not Working

**Problem:** `TURINGMIND_API_KEY` set but not recognized.

**Solutions:**
```bash
# Check if key is set
echo $TURINGMIND_API_KEY

# Verify key format (should start with tm_sk_)
# Re-login to get fresh key
/tmind:login
```

#### Login Flow Fails

**Problem:** Browser doesn't open or login times out.

**Solutions:**
- Check internet connectivity
- Try manual login: Visit the URL shown in terminal
- Check firewall/proxy settings
- Verify API URL: `export TURINGMIND_API_URL=https://api.turingmind.ai`

### Performance Issues

#### Reviews Are Slow

**Problem:** Code review takes too long.

**Solutions:**
- Use quick review (`/tmind:review`) instead of deep review
- Review smaller changesets (commit more frequently)
- Check if timeout is too high: `echo $TMIND_TIMEOUT`
- Ensure CLI is up to date

#### High Memory Usage

**Problem:** Review process uses too much memory.

**Solutions:**
- Review smaller files/changesets
- Close other applications
- Check for memory leaks in CLI tools

### General Issues

#### "Review failed to run. Allowing commit."

**Problem:** Review fails but commit proceeds.

**Solutions:**
- Check error output shown in hook
- Verify CLI is working: `claude --version` or `cursor-agent status`
- Check authentication (see above)
- Enable verbose mode: `export TMIND_DEBUG=true` (if supported)

#### False Positives

**Problem:** Review flags issues that aren't real problems.

**Solutions:**
- Submit feedback: Use `turingmind_submit_feedback` MCP tool
- Add ignore comments in code (if supported)
- Adjust review sensitivity in settings
- Use cloud mode to learn from past dismissals

---

## ⚠️ Limitations

This is **AI-assisted** code review. It's powerful, but:

- 🔧 **Complements, doesn't replace** SAST tools (Semgrep, CodeQL, Snyk)
- 🔗 Can't trace complex multi-file data flows
- 🧪 Doesn't run tests or type checking

For security-critical code, layer this with dedicated security scanners.

---

## 🤝 Contributing

Contributions welcome! Here's how:

1. **Add language support** — Create `agents/language-{lang}.md`
2. **Improve detection** — Enhance agent prompts in `agents/`
3. **Fix false positives** — Tune `templates/false-positive-rules.md`
4. **Report issues** — Open a GitHub issue

---

## 📄 License

MIT © [TuringMind](LICENSE)

---

<div align="center">

**[⬆ Back to top](#-turingmind-code-review)**

Made with 🧠 by developers, for developers.

</div>
