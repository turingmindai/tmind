<div align="center">

# 🧠 TuringMind Code Review

**Catch bugs before they catch you.**

A [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skill for AI-powered code review of your uncommitted changes. Install from the marketplace, review instantly.

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Claude Code Skill](https://img.shields.io/badge/Claude_Code-Skill-blueviolet)](https://docs.anthropic.com/en/docs/claude-code)
[![Install from Marketplace](https://img.shields.io/badge/Marketplace-Install-green)](https://github.com/turingmindai/tmind)

[Quick Start](#-quick-start) • [Features](#-features) • [Examples](#-example-output) • [Contributing](#-contributing)

</div>

---

## 📦 What is This?

**TuringMind Code Review** is a **Claude Code skill** — a reusable, shareable plugin that extends Claude Code with specialized code review capabilities. 

Claude Code skills are installed via the built-in plugin marketplace and add new slash commands to your Claude Code environment.

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

### Install from Marketplace

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
# Step 3: One-time setup (installs MCP server)
/tmind:setup
```

```bash
# Step 4: Restart Claude, then login
/tmind:login
```

### Use the Commands

```bash
# Quick review — fast, pre-commit check
/tmind:review

# Deep review — thorough analysis before PRs
/tmind:deep-review
```

That's it. Reviews work locally. Cloud features (memory, analytics) require login.

### Requirements

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) installed and configured
- Git repository with uncommitted changes

### Optional: Git Hooks

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
plugins/tmind/
├── commands/           # Review orchestration
│   ├── review.md
│   ├── deep-review.md
│   ├── login.md
│   └── setup.md        # One-time MCP setup
├── agents/             # Specialized reviewers
│   ├── bugs.md
│   ├── security.md
│   ├── compliance.md
│   ├── architecture.md
│   ├── index.md        # Agent router
│   └── language-*.md
└── templates/          # Output & filtering
    ├── output-format.md
    ├── memory-context.md   # Cloud memory injection
    └── false-positive-rules.md
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
