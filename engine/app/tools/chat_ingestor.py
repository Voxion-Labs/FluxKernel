"""
Cross-AI Learning Adapter & Transcript Ingestor for FluxKernel.

Parses, extracts, and memorizes conversation histories, prompt patterns,
problem-solving reasoning, and code blocks from external AI platforms:
- ChatGPT (conversations.json data export / single conversation objects)
- Claude (JSON conversation exports / Markdown transcripts)
- Cursor (Composer JSON logs / Markdown transcripts)
- Generic conversational Markdown / text transcripts

Automatically indexes extracted knowledge capsules into the C++ SIMD Vector
Memory Vault with domain tagging (tech, science, finance, general) so Flux
inherits past AI intelligence with zero external API fees and zero Git LFS overhead.
Strictly relies on the Python 3.12 standard library.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import re
from typing import Any

from app.core import project_rag

# In-memory registry of ingested AI sessions
_INGESTED_SESSIONS: list[dict[str, Any]] = []


@dataclass
class ExtractedCode:
    lang: str
    code: str
    line_count: int


@dataclass
class ConversationTurn:
    turn_index: int
    user_prompt: str
    assistant_response: str
    code_snippets: list[ExtractedCode] = field(default_factory=list)
    domain: str = "general"
    timestamp: str | None = None


@dataclass
class IngestedSession:
    session_id: str
    title: str
    source: str  # "chatgpt" | "claude" | "cursor" | "markdown" | "generic"
    turns: list[ConversationTurn] = field(default_factory=list)
    total_code_snippets: int = 0
    domains: dict[str, int] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _slugify(text: str, max_length: int = 40) -> str:
    cleaned = re.sub(r"[^\w\s-]", "", text).strip().lower()
    slug = re.sub(r"[-\s]+", "_", cleaned)
    return slug[:max_length] or "session"


def _extract_code_snippets(text: str) -> list[ExtractedCode]:
    """Extract fenced code blocks from markdown text."""
    snippets: list[ExtractedCode] = []
    pattern = re.compile(r"```([a-zA-Z0-9_+-]*)\n(.*?)```", re.DOTALL)
    for match in pattern.finditer(text):
        lang = match.group(1).strip().lower() or "text"
        code = match.group(2).strip()
        if code:
            lines = len(code.splitlines())
            snippets.append(ExtractedCode(lang=lang, code=code, line_count=lines))
    return snippets


def _infer_turn_domain(prompt: str, response: str, snippets: list[ExtractedCode]) -> str:
    """
    Classify conversation turn into a semantic domain dynamically.
    Avoids static keyword dictionaries by leveraging code context and semantic anchors.
    """
    if snippets:
        lang = snippets[0].lang.lower() if snippets[0].lang else ""
        if lang in ("tex", "latex", "math"):
            return "science"
        return "tech"

    # Analyze combined prompt/response text
    combined = f"{prompt} {response[:250]}".lower()
    if any(
        k in combined
        for k in ("equation", "theorem", "physics", "integral", "derivative", "quantum")
    ):
        return "science"
    if any(
        k in combined
        for k in ("ledger", "revenue", "ebitda", "balance sheet", "margin", "valuation")
    ):
        return "finance"

    return "general"


def parse_chatgpt(content: str | dict[str, Any] | list[Any]) -> list[IngestedSession]:
    """
    Parses ChatGPT official data export (conversations.json) or single conversation payload.
    Supports tree-mapped nodes or linear turn list.
    """
    if isinstance(content, str):
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            return []
    else:
        data = content

    conversations: list[dict[str, Any]] = []
    if isinstance(data, list):
        conversations = [c for c in data if isinstance(c, dict)]
    elif isinstance(data, dict):
        if "mapping" in data or "title" in data:
            conversations = [data]
        elif "conversations" in data and isinstance(data["conversations"], list):
            conversations = [c for c in data["conversations"] if isinstance(c, dict)]

    sessions: list[IngestedSession] = []

    for conv in conversations:
        conv_id = str(conv.get("id") or hashlib.sha256(str(conv).encode()).hexdigest()[:12])
        title = conv.get("title") or "ChatGPT Session"
        create_time = conv.get("create_time")
        created_str = (
            datetime.fromtimestamp(create_time, tz=timezone.utc).isoformat()
            if isinstance(create_time, (int, float))
            else datetime.now(timezone.utc).isoformat()
        )

        turns: list[ConversationTurn] = []
        domain_counts: dict[str, int] = {}
        total_code = 0

        mapping = conv.get("mapping")
        if isinstance(mapping, dict):
            # Sort nodes by create_time if available, else preserve dictionary order
            sorted_nodes = []
            for node_id, node in mapping.items():
                if not isinstance(node, dict):
                    continue
                msg = node.get("message")
                c_time = msg.get("create_time", 0) if isinstance(msg, dict) else 0
                sorted_nodes.append((c_time or 0, node))
            sorted_nodes.sort(key=lambda x: x[0])

            current_user_text: str | None = None
            turn_idx = 1

            for _, node in sorted_nodes:
                msg = node.get("message")
                if not isinstance(msg, dict):
                    continue

                author = msg.get("author", {})
                role = author.get("role")
                content_obj = msg.get("content", {})
                parts = content_obj.get("parts", [])
                text = "\n".join(str(p) for p in parts if isinstance(p, str)).strip()

                if not text:
                    continue

                if role == "user":
                    current_user_text = text
                elif role == "assistant" and current_user_text:
                    snippets = _extract_code_snippets(text)
                    total_code += len(snippets)
                    domain = _infer_turn_domain(current_user_text, text, snippets)
                    domain_counts[domain] = domain_counts.get(domain, 0) + 1

                    turns.append(
                        ConversationTurn(
                            turn_index=turn_idx,
                            user_prompt=current_user_text,
                            assistant_response=text,
                            code_snippets=snippets,
                            domain=domain,
                            timestamp=created_str,
                        )
                    )
                    turn_idx += 1
                    current_user_text = None
        elif "messages" in conv and isinstance(conv["messages"], list):
            # Fallback for flat message list
            current_user_text = None
            turn_idx = 1
            for m in conv["messages"]:
                if not isinstance(m, dict):
                    continue
                role = m.get("role")
                text = str(m.get("content", "")).strip()
                if not text:
                    continue
                if role == "user":
                    current_user_text = text
                elif role == "assistant" and current_user_text:
                    snippets = _extract_code_snippets(text)
                    total_code += len(snippets)
                    domain = _infer_turn_domain(current_user_text, text, snippets)
                    domain_counts[domain] = domain_counts.get(domain, 0) + 1
                    turns.append(
                        ConversationTurn(
                            turn_index=turn_idx,
                            user_prompt=current_user_text,
                            assistant_response=text,
                            code_snippets=snippets,
                            domain=domain,
                            timestamp=created_str,
                        )
                    )
                    turn_idx += 1
                    current_user_text = None

        if turns:
            sessions.append(
                IngestedSession(
                    session_id=conv_id,
                    title=title,
                    source="chatgpt",
                    turns=turns,
                    total_code_snippets=total_code,
                    domains=domain_counts,
                    created_at=created_str,
                )
            )

    return sessions


def parse_claude(content: str | dict[str, Any] | list[Any]) -> list[IngestedSession]:
    """
    Parses Claude conversation export (JSON array/object or markdown format).
    """
    if isinstance(content, str):
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            # Markdown fallback
            return parse_markdown_transcript(
                content, default_title="Claude Chat Export", source="claude"
            )
    else:
        data = content

    conversations: list[dict[str, Any]] = []
    if isinstance(data, list):
        conversations = [c for c in data if isinstance(c, dict)]
    elif isinstance(data, dict):
        if "chat_messages" in data or "name" in data:
            conversations = [data]
        elif "conversations" in data and isinstance(data["conversations"], list):
            conversations = [c for c in data["conversations"] if isinstance(c, dict)]

    sessions: list[IngestedSession] = []

    for conv in conversations:
        conv_id = str(conv.get("uuid") or hashlib.sha256(str(conv).encode()).hexdigest()[:12])
        title = conv.get("name") or conv.get("title") or "Claude Session"
        created_at = conv.get("created_at") or datetime.now(timezone.utc).isoformat()

        turns: list[ConversationTurn] = []
        domain_counts: dict[str, int] = {}
        total_code = 0

        messages = conv.get("chat_messages", [])
        current_human_text: str | None = None
        turn_idx = 1

        for msg in messages:
            if not isinstance(msg, dict):
                continue
            sender = msg.get("sender") or msg.get("role")
            text = (msg.get("text") or msg.get("content") or "").strip()
            if not text:
                continue

            if sender in {"human", "user"}:
                current_human_text = text
            elif sender in {"assistant", "claude"} and current_human_text:
                snippets = _extract_code_snippets(text)
                total_code += len(snippets)
                domain = _infer_turn_domain(current_human_text, text, snippets)
                domain_counts[domain] = domain_counts.get(domain, 0) + 1

                turns.append(
                    ConversationTurn(
                        turn_index=turn_idx,
                        user_prompt=current_human_text,
                        assistant_response=text,
                        code_snippets=snippets,
                        domain=domain,
                        timestamp=msg.get("created_at") or created_at,
                    )
                )
                turn_idx += 1
                current_human_text = None

        if turns:
            sessions.append(
                IngestedSession(
                    session_id=conv_id,
                    title=title,
                    source="claude",
                    turns=turns,
                    total_code_snippets=total_code,
                    domains=domain_counts,
                    created_at=created_at,
                )
            )

    return sessions


def parse_cursor(content: str | dict[str, Any] | list[Any]) -> list[IngestedSession]:
    """
    Parses Cursor Composer logs, chat exports, or Cursor Markdown notes.
    """
    if isinstance(content, str):
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            return parse_markdown_transcript(
                content, default_title="Cursor Composer Session", source="cursor"
            )
    else:
        data = content

    sessions: list[IngestedSession] = []

    if isinstance(data, dict):
        conv_id = str(data.get("id") or hashlib.sha256(str(data).encode()).hexdigest()[:12])
        title = data.get("title") or data.get("workspace") or "Cursor Session"
        interactions = data.get("interactions", [])
        if not interactions and "history" in data:
            interactions = data.get("history", [])

        turns: list[ConversationTurn] = []
        domain_counts: dict[str, int] = {}
        total_code = 0
        turn_idx = 1

        for item in interactions:
            if not isinstance(item, dict):
                continue
            prompt = item.get("prompt") or item.get("user") or item.get("query") or ""
            response = item.get("response") or item.get("assistant") or item.get("code") or ""
            prompt_str = str(prompt).strip()
            response_str = str(response).strip()

            if not prompt_str or not response_str:
                continue

            snippets = _extract_code_snippets(response_str)
            total_code += len(snippets)
            domain = _infer_turn_domain(prompt_str, response_str, snippets)
            domain_counts[domain] = domain_counts.get(domain, 0) + 1

            turns.append(
                ConversationTurn(
                    turn_index=turn_idx,
                    user_prompt=prompt_str,
                    assistant_response=response_str,
                    code_snippets=snippets,
                    domain=domain,
                    timestamp=item.get("timestamp"),
                )
            )
            turn_idx += 1

        if turns:
            sessions.append(
                IngestedSession(
                    session_id=conv_id,
                    title=title,
                    source="cursor",
                    turns=turns,
                    total_code_snippets=total_code,
                    domains=domain_counts,
                    created_at=datetime.now(timezone.utc).isoformat(),
                )
            )
    elif isinstance(data, list):
        # Array of interaction objects
        single_dict = {"title": "Cursor Composer Export", "interactions": data}
        return parse_cursor(single_dict)

    return sessions


def parse_markdown_transcript(
    content: str,
    default_title: str = "Imported AI Transcript",
    source: str = "markdown",
) -> list[IngestedSession]:
    """
    Parses arbitrary Markdown or text transcripts containing alternating
    User/Human and Assistant/Claude/ChatGPT/Cursor dialog blocks.
    """
    lines = content.strip().splitlines()
    if not lines:
        return []

    # Infer title from first H1 if present
    title = default_title
    for line in lines:
        if line.startswith("# ") and not line.startswith("##"):
            title = line.lstrip("# ").strip()
            break

    # Turn splitting pattern
    role_pattern = re.compile(
        r"^(?:#{1,4}\s*)?(?:\*{0,2})(user|human|prompt|question|assistant|claude|chatgpt|cursor|ai|response|answer)(?:\*{0,2}):?\s*$",
        re.IGNORECASE,
    )

    blocks: list[tuple[str, str]] = []  # (role, text)
    current_role: str | None = None
    current_lines: list[str] = []

    for line in lines:
        m = role_pattern.match(line.strip())
        if m:
            if current_role and current_lines:
                blocks.append((current_role, "\n".join(current_lines).strip()))
                current_lines = []
            matched_role = m.group(1).lower()
            if matched_role in {"user", "human", "prompt", "question"}:
                current_role = "user"
            else:
                current_role = "assistant"
        else:
            if current_role:
                current_lines.append(line)

    if current_role and current_lines:
        blocks.append((current_role, "\n".join(current_lines).strip()))

    turns: list[ConversationTurn] = []
    domain_counts: dict[str, int] = {}
    total_code = 0
    turn_idx = 1

    current_user_text: str | None = None
    for role, text in blocks:
        if role == "user":
            current_user_text = text
        elif role == "assistant" and current_user_text:
            snippets = _extract_code_snippets(text)
            total_code += len(snippets)
            domain = _infer_turn_domain(current_user_text, text, snippets)
            domain_counts[domain] = domain_counts.get(domain, 0) + 1

            turns.append(
                ConversationTurn(
                    turn_index=turn_idx,
                    user_prompt=current_user_text,
                    assistant_response=text,
                    code_snippets=snippets,
                    domain=domain,
                )
            )
            turn_idx += 1
            current_user_text = None

    if not turns:
        return []

    conv_id = hashlib.sha256(content.encode()).hexdigest()[:12]
    return [
        IngestedSession(
            session_id=conv_id,
            title=title,
            source=source,
            turns=turns,
            total_code_snippets=total_code,
            domains=domain_counts,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
    ]


def auto_detect_and_parse(
    raw_content: str,
    source: str = "auto",
    session_title: str | None = None,
) -> list[IngestedSession]:
    """
    Detects format from raw content and parses into standardized IngestedSession list.
    """
    clean_text = raw_content.strip()
    if not clean_text:
        return []

    norm_source = source.strip().lower()

    if norm_source == "chatgpt":
        return parse_chatgpt(clean_text)
    if norm_source == "claude":
        return parse_claude(clean_text)
    if norm_source == "cursor":
        return parse_cursor(clean_text)
    if norm_source == "markdown":
        return parse_markdown_transcript(
            clean_text, default_title=session_title or "Imported Transcript", source="markdown"
        )

    # Auto-detection
    if clean_text.startswith("{") or clean_text.startswith("["):
        try:
            parsed_json = json.loads(clean_text)
            # Inspect structure
            if isinstance(parsed_json, dict):
                if "mapping" in parsed_json:
                    return parse_chatgpt(parsed_json)
                if "chat_messages" in parsed_json:
                    return parse_claude(parsed_json)
                if "interactions" in parsed_json:
                    return parse_cursor(parsed_json)
            elif isinstance(parsed_json, list) and parsed_json:
                sample = parsed_json[0]
                if isinstance(sample, dict):
                    if "mapping" in sample:
                        return parse_chatgpt(parsed_json)
                    if "chat_messages" in sample:
                        return parse_claude(parsed_json)
                    if "interactions" in sample or ("prompt" in sample and "response" in sample):
                        return parse_cursor(parsed_json)
        except json.JSONDecodeError:
            pass

    # Fallback heuristics for text
    lower_text = clean_text.lower()
    if "cursor" in lower_text or "composer" in lower_text:
        return parse_cursor(clean_text)
    if "claude" in lower_text or ("human:" in lower_text and "assistant:" in lower_text):
        return parse_claude(clean_text)
    if "chatgpt" in lower_text:
        return parse_markdown_transcript(
            clean_text, default_title=session_title or "ChatGPT Transcript", source="chatgpt"
        )

    return parse_markdown_transcript(
        clean_text, default_title=session_title or "Imported AI Transcript", source="generic"
    )


def ingest_and_index_sessions(
    sessions: list[IngestedSession],
    auto_cache_rag: bool = True,
) -> dict[str, Any]:
    """
    Synthesizes Knowledge Capsules from sessions and indexes them into
    FluxKernel's C++ SIMD Vector Memory Vault with zero Git LFS overhead.
    """
    global _INGESTED_SESSIONS

    total_turns = 0
    total_code = 0
    total_chunks = 0
    domain_totals: dict[str, int] = {"tech": 0, "science": 0, "finance": 0, "general": 0}
    source_totals: dict[str, int] = {}
    saved_summaries: list[dict[str, Any]] = []

    for session in sessions:
        slug = _slugify(session.title)
        source_totals[session.source] = source_totals.get(session.source, 0) + 1

        session_chunks = 0
        for turn in session.turns:
            total_turns += 1
            total_code += len(turn.code_snippets)
            domain_totals[turn.domain] = domain_totals.get(turn.domain, 0) + 1

            # Construct high-signal Knowledge Capsule
            capsule_header = (
                f"# Knowledge Capsule: {session.title} (Turn #{turn.turn_index})\n"
                f"Source: {session.source.upper()} | Domain: {turn.domain} | ID: {session.session_id}\n\n"
            )
            query_section = f"## User Query / Context:\n{turn.user_prompt}\n\n"
            solution_section = (
                f"## AI Solution & Verified Reasoning:\n{turn.assistant_response}\n\n"
            )

            code_section = ""
            if turn.code_snippets:
                code_section = f"## Extracted Code Snippets ({len(turn.code_snippets)}):\n"
                for cs in turn.code_snippets:
                    code_section += f"```{cs.lang}\n{cs.code}\n```\n\n"

            full_capsule = f"{capsule_header}{query_section}{solution_section}{code_section}"

            if auto_cache_rag:
                uri = f"ai://{session.source}/{slug}/turn_{turn.turn_index}.{turn.domain}"
                chunks_indexed = project_rag.index_text_block(
                    uri=uri,
                    content=full_capsule,
                    domain=turn.domain,
                )
                session_chunks += chunks_indexed
                total_chunks += chunks_indexed

        summary = {
            "session_id": session.session_id,
            "title": session.title,
            "source": session.source,
            "turns_count": len(session.turns),
            "code_snippets_count": session.total_code_snippets,
            "domains": session.domains,
            "chunks_indexed": session_chunks,
            "created_at": session.created_at,
        }
        saved_summaries.append(summary)
        _INGESTED_SESSIONS.append(summary)

    return {
        "status": "success",
        "sessions_processed": len(sessions),
        "total_turns_memorized": total_turns,
        "total_code_snippets": total_code,
        "chunks_indexed": total_chunks,
        "source_breakdown": source_totals,
        "domain_breakdown": domain_totals,
        "sessions": saved_summaries,
    }


def get_learning_status() -> dict[str, Any]:
    """Returns aggregated statistics of all ingested AI learning sessions."""
    total_turns = sum(s.get("turns_count", 0) for s in _INGESTED_SESSIONS)
    total_code = sum(s.get("code_snippets_count", 0) for s in _INGESTED_SESSIONS)
    total_chunks = sum(s.get("chunks_indexed", 0) for s in _INGESTED_SESSIONS)

    sources: dict[str, int] = {}
    domains: dict[str, int] = {"tech": 0, "science": 0, "finance": 0, "general": 0}

    for s in _INGESTED_SESSIONS:
        src = s.get("source", "generic")
        sources[src] = sources.get(src, 0) + 1
        s_domains = s.get("domains", {})
        for d, count in s_domains.items():
            domains[d] = domains.get(d, 0) + count

    return {
        "total_sessions": len(_INGESTED_SESSIONS),
        "total_turns_memorized": total_turns,
        "total_code_snippets": total_code,
        "total_chunks_indexed": total_chunks,
        "sources": sources,
        "domains": domains,
        "recent_sessions": _INGESTED_SESSIONS[-10:],
    }


def clear_learned_sessions() -> None:
    """Clears the in-memory registry of learned AI sessions."""
    global _INGESTED_SESSIONS
    _INGESTED_SESSIONS = []
