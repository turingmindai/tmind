#!/usr/bin/env python3
"""
TuringMind MCP Server

Provides type-safe tools for Claude to interact with TuringMind cloud:
- turingmind_validate_auth: Check API key and account status
- turingmind_upload_review: Upload code review results
- turingmind_get_context: Get memory context for a repository

Run with: turingmind-mcp
Configure in Claude Desktop config:
  - macOS: ~/Library/Application Support/Claude/claude_desktop_config.json
  - Windows: %APPDATA%/Claude/claude_desktop_config.json
  - Linux: ~/.config/Claude/claude_desktop_config.json
"""

import os
import sys
import asyncio
import logging
from typing import Optional, Any
from enum import Enum

import httpx
from pydantic import BaseModel, Field
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# ============================================================================
# LOGGING
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr  # MCP uses stdout for protocol, stderr for logs
)
logger = logging.getLogger("turingmind-mcp")

# ============================================================================
# CONFIGURATION
# ============================================================================

DEFAULT_API_URL = "https://api.turingmind.ai"
CONFIG_PATH = os.path.expanduser("~/.turingmind/config")


def get_config() -> tuple[str, str]:
    """Get API URL and API key from environment or config file."""
    api_url = os.environ.get("TURINGMIND_API_URL", DEFAULT_API_URL)
    api_key = os.environ.get("TURINGMIND_API_KEY", "")
    
    # Try loading from config file if not in environment
    if not api_key and os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("export TURINGMIND_API_KEY="):
                        api_key = line.split("=", 1)[1].strip().strip('"\'')
                    elif line.startswith("export TURINGMIND_API_URL="):
                        api_url = line.split("=", 1)[1].strip().strip('"\'')
        except Exception as e:
            logger.warning(f"Failed to read config: {e}")
    
    return api_url, api_key


# ============================================================================
# TOOL SCHEMAS (Pydantic models for type-safe input)
# ============================================================================

class Severity(str, Enum):
    """Issue severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ReviewType(str, Enum):
    """Code review types"""
    QUICK = "quick"
    DEEP = "deep"


class Issue(BaseModel):
    """A single code review issue"""
    title: str = Field(..., description="Short issue title (max 500 chars)")
    severity: Severity = Field(..., description="Issue severity: critical, high, medium, low")
    category: str = Field("bug", description="Category: security, bug, compliance, performance")
    file: str = Field(..., description="File path where issue was found")
    line: int = Field(..., ge=1, description="Line number (1-indexed)")
    description: Optional[str] = Field(None, description="Detailed description of the issue")
    cwe: Optional[str] = Field(None, description="CWE ID if security issue (e.g., CWE-79)")
    confidence: int = Field(85, ge=0, le=100, description="Confidence score 0-100")


class UploadReviewInput(BaseModel):
    """Input schema for turingmind_upload_review tool"""
    repo: str = Field(..., description="Repository identifier (owner/repo)")
    branch: Optional[str] = Field(None, description="Git branch name")
    commit: Optional[str] = Field(None, description="Git commit SHA (short or full)")
    review_type: ReviewType = Field(ReviewType.QUICK, description="Review type: quick or deep")
    issues: list[dict] = Field(default_factory=list, description="List of issues found")
    raw_content: Optional[str] = Field(None, description="Full review content as markdown")
    summary: Optional[dict] = Field(None, description="Summary with critical/high/medium/low counts")
    files_reviewed: list[dict] = Field(default_factory=list, description="Files that were reviewed")


class GetContextInput(BaseModel):
    """Input schema for turingmind_get_context tool"""
    repo: str = Field(..., description="Repository identifier (owner/repo)")


# ============================================================================
# MCP SERVER
# ============================================================================

server = Server("turingmind")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available TuringMind tools."""
    return [
        Tool(
            name="turingmind_validate_auth",
            description=(
                "Validate TuringMind API key and get account information. "
                "Returns tier, quota remaining, and user info. "
                "Call this first to verify cloud features are available."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="turingmind_upload_review",
            description=(
                "Upload code review results to TuringMind cloud for analytics and memory. "
                "Stores issues found, files reviewed, and review metadata. "
                "Returns review ID on success. Requires code_review:write permission."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "repo": {
                        "type": "string",
                        "description": "Repository identifier (owner/repo format)"
                    },
                    "branch": {
                        "type": "string",
                        "description": "Git branch name (optional)"
                    },
                    "commit": {
                        "type": "string",
                        "description": "Git commit SHA (optional)"
                    },
                    "review_type": {
                        "type": "string",
                        "enum": ["quick", "deep"],
                        "default": "quick",
                        "description": "Type of review performed"
                    },
                    "issues": {
                        "type": "array",
                        "description": "List of issues found during review",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string", "description": "Issue title"},
                                "severity": {
                                    "type": "string",
                                    "enum": ["critical", "high", "medium", "low"]
                                },
                                "category": {
                                    "type": "string",
                                    "description": "Category: security, bug, compliance"
                                },
                                "file": {"type": "string", "description": "File path"},
                                "line": {"type": "integer", "description": "Line number"},
                                "description": {"type": "string", "description": "Details"},
                                "cwe": {"type": "string", "description": "CWE ID if applicable"},
                                "confidence": {
                                    "type": "integer",
                                    "minimum": 0,
                                    "maximum": 100
                                }
                            },
                            "required": ["title", "severity", "file", "line"]
                        }
                    },
                    "raw_content": {
                        "type": "string",
                        "description": "Full review as markdown (optional)"
                    },
                    "summary": {
                        "type": "object",
                        "description": "Summary counts",
                        "properties": {
                            "critical": {"type": "integer"},
                            "high": {"type": "integer"},
                            "medium": {"type": "integer"},
                            "low": {"type": "integer"}
                        }
                    },
                    "files_reviewed": {
                        "type": "array",
                        "description": "Files that were reviewed",
                        "items": {
                            "type": "object",
                            "properties": {
                                "path": {"type": "string"},
                                "lines_added": {"type": "integer"},
                                "lines_removed": {"type": "integer"}
                            }
                        }
                    }
                },
                "required": ["repo"]
            }
        ),
        Tool(
            name="turingmind_get_context",
            description=(
                "Get memory context for a repository from TuringMind cloud. "
                "Returns recent open issues, hotspot files, false positive patterns, "
                "and team conventions. Use this before reviewing to avoid duplicate reports."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "repo": {
                        "type": "string",
                        "description": "Repository identifier (owner/repo format)"
                    }
                },
                "required": ["repo"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Execute a TuringMind tool."""
    api_url, api_key = get_config()
    
    if not api_key:
        return [TextContent(
            type="text",
            text=(
                "❌ **TURINGMIND_API_KEY not configured**\n\n"
                "Run `/tmind:login` first to authenticate, or set the environment variable:\n"
                "```bash\n"
                "export TURINGMIND_API_KEY=tmk_your_key_here\n"
                "```"
            )
        )]
    
    logger.info(f"Executing tool: {name}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "turingmind-mcp/0.1.0"
        }
        
        try:
            # ─────────────────────────────────────────────────────────────
            # VALIDATE AUTH
            # ─────────────────────────────────────────────────────────────
            if name == "turingmind_validate_auth":
                response = await client.get(
                    f"{api_url}/api/v1/code-review/auth/validate",
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    quota = data.get("quota", {})
                    return [TextContent(
                        type="text",
                        text=(
                            f"✅ **TuringMind Authentication Valid**\n\n"
                            f"- **Tier:** {data.get('tier', 'unknown')}\n"
                            f"- **Quota:** {quota.get('reviews_remaining', '?')}"
                            f"/{quota.get('reviews_limit', '?')} reviews remaining\n"
                            f"- **User:** {data.get('user_id', 'unknown')[:20]}...\n\n"
                            f"Cloud features are enabled. You can use `turingmind_upload_review` "
                            f"and `turingmind_get_context`."
                        )
                    )]
                elif response.status_code == 401:
                    return [TextContent(
                        type="text",
                        text=(
                            "❌ **Authentication Failed**\n\n"
                            "API key is invalid or expired. Run `/tmind:login` to re-authenticate."
                        )
                    )]
                else:
                    return [TextContent(
                        type="text",
                        text=f"❌ **Auth check failed:** HTTP {response.status_code}\n{response.text[:200]}"
                    )]
            
            # ─────────────────────────────────────────────────────────────
            # UPLOAD REVIEW
            # ─────────────────────────────────────────────────────────────
            elif name == "turingmind_upload_review":
                # Validate input
                try:
                    review = UploadReviewInput(**arguments)
                except Exception as e:
                    return [TextContent(
                        type="text",
                        text=f"❌ **Invalid input:** {e}\n\nRequired field: `repo`"
                    )]
                
                # Count issues by severity for auto-summary
                issues = review.issues or []
                auto_summary = {
                    "critical": sum(1 for i in issues if i.get("severity") == "critical"),
                    "high": sum(1 for i in issues if i.get("severity") == "high"),
                    "medium": sum(1 for i in issues if i.get("severity") == "medium"),
                    "low": sum(1 for i in issues if i.get("severity") == "low"),
                }
                
                # Build request body
                body = {
                    "context": {
                        "repo": review.repo,
                        "branch": review.branch,
                        "commit": review.commit,
                        "review_type": review.review_type.value if isinstance(review.review_type, ReviewType) else review.review_type
                    },
                    "issues": issues,
                    "raw_content": review.raw_content,
                    "summary": review.summary or auto_summary,
                    "files_reviewed": review.files_reviewed or []
                }
                
                logger.info(f"Uploading review for {review.repo} with {len(issues)} issues")
                
                response = await client.post(
                    f"{api_url}/api/v1/code-review/reviews",
                    headers=headers,
                    json=body
                )
                
                if response.status_code in (200, 201):
                    data = response.json()
                    return [TextContent(
                        type="text",
                        text=(
                            f"🧠 **Review Uploaded to TuringMind**\n\n"
                            f"- **Review ID:** `{data.get('review_id', 'unknown')}`\n"
                            f"- **Repository:** {review.repo}\n"
                            f"- **Issues:** {len(issues)}\n"
                            f"- **Summary:** {auto_summary['critical']} critical, "
                            f"{auto_summary['high']} high, {auto_summary['medium']} medium, "
                            f"{auto_summary['low']} low\n\n"
                            f"Review data is now available in TuringMind cloud for analytics "
                            f"and future context."
                        )
                    )]
                elif response.status_code == 403:
                    return [TextContent(
                        type="text",
                        text=(
                            "❌ **Permission Denied**\n\n"
                            "API key lacks `code_review:write` permission.\n"
                            "Run `/tmind:login` to create a new key with proper permissions."
                        )
                    )]
                elif response.status_code == 422:
                    return [TextContent(
                        type="text",
                        text=(
                            f"❌ **Validation Error**\n\n"
                            f"Request body failed validation:\n```\n{response.text[:500]}\n```"
                        )
                    )]
                else:
                    return [TextContent(
                        type="text",
                        text=f"❌ **Upload failed:** HTTP {response.status_code}\n{response.text[:200]}"
                    )]
            
            # ─────────────────────────────────────────────────────────────
            # GET CONTEXT
            # ─────────────────────────────────────────────────────────────
            elif name == "turingmind_get_context":
                repo = arguments.get("repo", "")
                if not repo:
                    return [TextContent(
                        type="text",
                        text="❌ **Missing required field:** `repo`"
                    )]
                
                logger.info(f"Fetching context for {repo}")
                
                response = await client.get(
                    f"{api_url}/api/v1/code-review/context/{repo}",
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Format open issues
                    open_issues = data.get("recent_open_issues", [])
                    issues_text = ""
                    if open_issues:
                        issues_text = "\n**Recent Open Issues:**\n"
                        for issue in open_issues[:5]:
                            issues_text += f"- `{issue.get('file', '?')}:{issue.get('line', '?')}` - {issue.get('title', 'Unknown')}\n"
                    
                    # Format hotspots
                    hotspots = data.get("hotspot_files", [])
                    hotspots_text = ""
                    if hotspots:
                        hotspots_text = "\n**Hotspot Files (frequent issues):**\n"
                        for hs in hotspots[:5]:
                            hotspots_text += f"- `{hs.get('path', '?')}` ({hs.get('issue_count', 0)} issues)\n"
                    
                    # Format conventions
                    conventions = data.get("team_conventions", [])
                    conventions_text = ""
                    if conventions:
                        conventions_text = "\n**Team Conventions:**\n"
                        for conv in conventions[:5]:
                            conventions_text += f"- {conv}\n"
                    
                    # Format false positives
                    fps = data.get("false_positive_patterns", [])
                    fp_text = ""
                    if fps:
                        fp_text = "\n**Known False Positives (skip these patterns):**\n"
                        for fp in fps[:5]:
                            fp_text += f"- {fp.get('pattern', '?')}: {fp.get('reason', 'N/A')}\n"
                    
                    return [TextContent(
                        type="text",
                        text=(
                            f"📚 **Memory Context for {repo}**\n\n"
                            f"- Open issues: {len(open_issues)}\n"
                            f"- Hotspot files: {len(hotspots)}\n"
                            f"- Team conventions: {len(conventions)}\n"
                            f"- False positive patterns: {len(fps)}\n"
                            f"{issues_text}{hotspots_text}{conventions_text}{fp_text}"
                        )
                    )]
                elif response.status_code == 400:
                    return [TextContent(
                        type="text",
                        text=f"⚠️ **No context available for {repo}**\n\nThis may be a new repository or invalid identifier."
                    )]
                else:
                    return [TextContent(
                        type="text",
                        text=f"⚠️ **Context fetch failed:** HTTP {response.status_code}"
                    )]
            
            # ─────────────────────────────────────────────────────────────
            # UNKNOWN TOOL
            # ─────────────────────────────────────────────────────────────
            else:
                return [TextContent(
                    type="text",
                    text=f"❌ **Unknown tool:** `{name}`\n\nAvailable tools: turingmind_validate_auth, turingmind_upload_review, turingmind_get_context"
                )]
                
        except httpx.ConnectError:
            return [TextContent(
                type="text",
                text=(
                    f"❌ **Connection Error**\n\n"
                    f"Could not connect to TuringMind API at `{api_url}`.\n"
                    f"Check your network connection or API URL configuration."
                )
            )]
        except httpx.TimeoutException:
            return [TextContent(
                type="text",
                text="❌ **Request Timeout**\n\nTuringMind API did not respond in time. Try again."
            )]
        except Exception as e:
            logger.exception(f"Tool {name} failed")
            return [TextContent(
                type="text",
                text=f"❌ **Error:** {type(e).__name__}: {e}"
            )]


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run the TuringMind MCP server."""
    logger.info("Starting TuringMind MCP server...")
    
    api_url, api_key = get_config()
    logger.info(f"API URL: {api_url}")
    logger.info(f"API Key: {'configured' if api_key else 'NOT SET'}")
    
    asyncio.run(run_server())


async def run_server():
    """Run the MCP server with stdio transport."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    main()

