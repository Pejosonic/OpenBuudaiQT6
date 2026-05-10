#!/usr/bin/env python3
"""
Agentic loop: Claude reads the repo, attempts a fix, writes files.
Exits with JSON: {"comment": "...", "attempted_fix": true/false}
"""

import anthropic
import json
import os
import subprocess
import sys

SYSTEM = """You are an automated code assistant for OpenBuudaiQT6, an open-source Qt6
oscilloscope application for Buudai/SainSmart USB oscilloscopes (DDS120, DDS140).
The codebase is C++17 + Qt6, built with CMake. Source files are under Source/src/.

When given a GitHub issue or comment:
1. Use the available tools to read relevant source files and understand the problem.
2. If you can fix it with a small, safe code change, do so using write_file.
3. Only fix what is clearly described. Do not refactor or change unrelated code.
4. After writing files (or deciding no fix is possible), write a clear comment explaining
   your analysis and what you did (or why you could not fix it automatically).
   End with "*(Automated analysis)*".

If the issue is a feature request, unclear, or requires large changes, just analyse it
and explain why it needs manual work. Do not attempt a fix."""

TOOLS = [
    {
        "name": "read_file",
        "description": "Read a source file from the repository.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path relative to repo root"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "write_file",
        "description": "Write or overwrite a file. Use for applying fixes.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"}
            },
            "required": ["path", "content"]
        }
    },
    {
        "name": "list_files",
        "description": "Find files matching a glob pattern (searches Source/src by default).",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Filename pattern, e.g. '*.cpp'"}
            },
            "required": ["pattern"]
        }
    },
    {
        "name": "grep",
        "description": "Search for a string across source files.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string"},
                "path": {"type": "string", "description": "Directory or file to search (default: Source/src)"}
            },
            "required": ["pattern"]
        }
    },
]


def run_tool(name: str, inputs: dict) -> str:
    try:
        if name == "read_file":
            with open(inputs["path"]) as f:
                return f.read()[:8000]

        elif name == "write_file":
            path = inputs["path"]
            os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
            with open(path, "w") as f:
                f.write(inputs["content"])
            return f"Wrote {len(inputs['content'])} bytes to {path}"

        elif name == "list_files":
            result = subprocess.run(
                ["find", "Source/src", "-name", inputs["pattern"], "-not", "-path", "*/build/*"],
                capture_output=True, text=True, timeout=10
            )
            return result.stdout.strip() or "No files found"

        elif name == "grep":
            search_path = inputs.get("path", "Source/src")
            result = subprocess.run(
                ["grep", "-rn", "--include=*.cpp", "--include=*.h", inputs["pattern"], search_path],
                capture_output=True, text=True, timeout=10
            )
            out = result.stdout.strip()
            return out[:4000] if out else "No matches"

    except Exception as e:
        return f"Error: {e}"

    return f"Unknown tool: {name}"


def build_prompt() -> str:
    event = os.environ.get("EVENT_NAME", "")
    action = os.environ.get("EVENT_ACTION", "")
    number = os.environ.get("ISSUE_NUMBER", "?")
    title = os.environ.get("ISSUE_TITLE", "")
    body = os.environ.get("ISSUE_BODY", "")
    comment_author = os.environ.get("COMMENT_AUTHOR", "")
    comment_body = os.environ.get("COMMENT_BODY", "")
    label = os.environ.get("LABEL_NAME", "")
    assignee = os.environ.get("ASSIGNEE", "")
    existing_comments = os.environ.get("ISSUE_COMMENTS", "")

    if event == "workflow_dispatch":
        parts = [
            f"Manual triage of issue #{number}.",
            f"\nTitle: {title}",
            f"\nBody:\n{body}",
        ]
        if existing_comments:
            parts.append(f"\nExisting comments:\n{existing_comments}")
        parts.append("\nAnalyse the full issue including all comments. Attempt a fix if the problem is clear and small.")
        return "\n".join(parts)

    if event == "issue_comment":
        return (
            f"A new comment was added to issue #{number}.\n\n"
            f"Issue title: {title}\n"
            f"Issue body:\n{body}\n\n"
            f"New comment by {comment_author}:\n{comment_body}\n\n"
            "If the comment describes a bug or provides new technical details that suggest a fix, attempt it. "
            "If it is a question, answer it. If off-topic, write a brief acknowledgement only."
        )

    if action == "opened":
        return (
            f"A new issue was opened (#{number}).\n\n"
            f"Title: {title}\n\n"
            f"Body:\n{body}\n\n"
            "Analyse the issue. If it describes a clear, small bug you can fix by editing source files, fix it. "
            "Otherwise explain the problem and suggest manual next steps."
        )

    if action == "closed":
        return (
            f"Issue #{number} ('{title}') was just closed. "
            "Write a brief 2-sentence closing summary. Do not attempt any code fix."
        )

    if action == "reopened":
        return (
            f"Issue #{number} ('{title}') was reopened. "
            "Acknowledge this and ask the reporter to provide any new details. Do not attempt a code fix."
        )

    if action == "labeled":
        return (
            f"Issue #{number} ('{title}') was labeled '{label}'. "
            "Write one sentence acknowledging the label. Do not attempt a code fix."
        )

    if action == "assigned":
        return (
            f"Issue #{number} ('{title}') was assigned to {assignee}. "
            "Write one sentence acknowledging the assignment. Do not attempt a code fix."
        )

    return f"Issue #{number} ('{title}') had action '{action}'. Write a brief acknowledgement."


def main():
    prompt = build_prompt()
    if not prompt:
        print(json.dumps({"comment": "No prompt could be built.", "attempted_fix": False}))
        sys.exit(1)

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    messages = [{"role": "user", "content": prompt}]
    final_text = ""

    for _ in range(20):  # max 20 tool-call rounds
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=SYSTEM,
            tools=TOOLS,
            messages=messages,
        )

        for block in response.content:
            if block.type == "text":
                final_text = block.text

        if response.stop_reason != "tool_use":
            break

        messages.append({"role": "assistant", "content": response.content})
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                result = run_tool(block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": str(result),
                })
        messages.append({"role": "user", "content": tool_results})

    diff = subprocess.run(["git", "diff", "--name-only"], capture_output=True, text=True).stdout.strip()
    attempted = bool(diff)

    print(json.dumps({"comment": final_text, "attempted_fix": attempted}))


if __name__ == "__main__":
    main()
