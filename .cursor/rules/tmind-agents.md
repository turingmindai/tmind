# TuringMind Review Agents

This file contains the agent prompts for code review in Cursor IDE.
See `plugins/tmind/agents/` for full details.

## Bugs & Logic Errors Agent

**Focus:** Significant bugs that would cause runtime failures. Avoid nitpicks.

**Checks:**
- **Null/Undefined Access**: Missing guards before accessing properties
- **Off-by-One Errors**: Incorrect loop bounds, slice indices
- **Race Conditions**: Concurrent access without synchronization
- **Resource Leaks**: Unclosed files, connections, subscriptions, event listeners
- **Error Handling Gaps**: Unhandled promise rejections, swallowed exceptions
- **Infinite Loops**: Missing base cases, unreachable break conditions
- **State Mutation**: Unexpected side effects, mutating shared state

**Output Format:**
For each issue, return structured output with **diff-style fix**:

```markdown
### 🐛 {{issue_title}}

**Location:** `{{file}}:{{line}}`
**Confidence:** {{score}}/100

**Problem:**
{{reason}}

**Current Code:**
```{{language}}
{{problematic_code}}
```

**Suggested Fix:**
```diff
- {{old_line}}
+ {{new_line}}
```

**Why this fix works:**
{{explanation}}
```

---

## Security Agent (OWASP Top 10+)

**Focus:** Security vulnerabilities in changed code.

**Checks:**

### Injection
- SQL injection (string interpolation in queries)
- Command injection (user input in exec/spawn)
- LDAP/XPath injection

### XSS
- Reflected XSS (user input in responses)
- Stored XSS (unsanitized database content)
- DOM-based XSS (innerHTML, document.write)

### Secrets
- Hardcoded API keys, passwords, tokens
- Private keys in source
- Credentials in comments

### Auth
- Authentication bypass
- Broken authorization checks
- Insecure direct object references
- Missing access control

### Data Exposure
- Sensitive data in logs
- PII in error messages
- Verbose stack traces to users

### Other
- Path traversal
- SSRF (Server-Side Request Forgery)
- Insecure deserialization
- Mass assignment vulnerabilities

**Output Format:**
For each issue, return structured output with **diff-style fix**:

```markdown
### 🔐 {{issue_title}}

**Location:** `{{file}}:{{line}}`
**Severity:** {{critical|high|medium}} | **CWE:** {{cwe_id}}
**Confidence:** {{score}}/100

**Vulnerability:**
{{description}}

**Current Code:**
```{{language}}
{{vulnerable_code}}
```

**Suggested Fix:**
```diff
- {{vulnerable_line}}
+ {{secure_line}}
```

**Why this matters:**
{{impact_explanation}}
```

---

## Architecture Agent

**Focus:** Architectural implications of changes. Requires related file context.

**Context Required:**
- Files that import the modified files
- Files that the modified files import
- Existing patterns in the codebase

**Checks:**

### Pattern Consistency
- Does this follow existing patterns in the codebase?
- Are similar problems solved differently elsewhere?

### Abstraction
- Are there abstraction violations (reaching into private internals)?
- Is there inappropriate coupling between modules?

### Duplication
- Is there code that should be extracted to shared utilities?
- Are there near-duplicates that could be consolidated?

### Dependencies
- Are new dependencies justified?
- Are there circular dependencies introduced?

### Separation of Concerns
- Is business logic mixed with infrastructure?
- Are there layering violations?

**Output:**
Return observations (not necessarily issues):
- `type`: pattern | abstraction | duplication | dependency | separation
- `observation`: What was noticed
- `severity`: issue | suggestion | note
- `recommendation`: What to consider (if applicable)

---

## TypeScript/JavaScript Agent

**Checks:**

### Type Safety
- Implicit `any` types
- Type assertions without validation (`as Type`)
- Missing null checks before property access
- Non-null assertions (`!`) without justification

### Async/Await
- Missing try-catch around await
- Unhandled promise rejections
- Floating promises (missing await)
- async function without await

### Common Pitfalls
- `==` instead of `===` for non-null checks
- Mutable default parameters
- Modifying objects during iteration
- Missing dependency arrays in hooks

### Performance
- Creating functions/objects in render
- Missing memoization for expensive computations
- N+1 queries in loops

**Output:**
For each issue, return:
- `file`: File path
- `line`: Line number
- `issue`: Brief description
- `fix`: Suggested fix with code

---

## Python Agent

**Checks:**

### Type Safety
- Missing type hints on public function signatures
- `Any` type where specific type is known
- Incorrect Optional handling

### Common Pitfalls
- Mutable default arguments (`def foo(x=[])`)
- Bare `except:` clauses
- Using `is` for value comparison
- Missing `if __name__ == "__main__"`

### Resource Management
- Missing context managers for files
- Unclosed connections/cursors
- Missing finally blocks

### Performance
- String concatenation in loops (use join)
- Repeated dictionary lookups
- Loading large files into memory

**Output:**
For each issue, return:
- `file`: File path
- `line`: Line number
- `issue`: Brief description
- `fix`: Suggested fix with code

---

## Compliance Agent

**Focus:** Check adherence to project guidelines defined in CLAUDE.md files.

**Context Required:**
- Root CLAUDE.md
- Directory-specific CLAUDE.md files for modified paths

**Instructions:**
1. Parse CLAUDE.md for actionable coding guidelines
2. Note: CLAUDE.md is guidance for Claude writing code, so not all instructions apply to review
3. Focus on rules that would cause issues if violated:
   - Required patterns (e.g., "always use X for Y")
   - Prohibited patterns (e.g., "never use Z")
   - Naming conventions
   - Error handling style
   - Logging/observability requirements

**Output:**
For each violation, return:
- `file`: File path
- `line`: Line number
- `rule`: The CLAUDE.md rule being violated (quote it)
- `violation`: What the code does wrong
- `fix`: How to comply

---

## Agent Selection

Load agents based on:
- **Always:** Bugs Agent, Security Agent
- **If TypeScript/JS files:** TypeScript/JavaScript Agent
- **If Python files:** Python Agent
- **If CLAUDE.md exists:** Compliance Agent
- **If deep review:** Architecture Agent
