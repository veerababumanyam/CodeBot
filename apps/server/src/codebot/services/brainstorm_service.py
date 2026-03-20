"""Brainstorm session orchestration for project intake."""

from __future__ import annotations

from copy import deepcopy
import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from agent_sdk.agents.base import AgentInput

from codebot.agents.brainstorming import BrainstormingAgent
from codebot.db.models.project import Project, ProjectStatus, ProjectType


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_project_config(project: Project) -> dict[str, Any]:
    config = deepcopy(project.config or {})
    project.config = config
    return config


def _first_non_empty(*values: str | None) -> str:
    for value in values:
        if value and value.strip():
            return value.strip()
    return ""


def _compact_excerpt(text: str, *, limit: int = 360) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return f"{normalized[: limit - 1].rstrip()}…"


class BrainstormService:
    """Manage the guided brainstorm phase for a project."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_session(self, project: Project) -> dict[str, Any] | None:
        """Return the stored brainstorm session, if any."""
        config = deepcopy(project.config or {})
        brainstorm = config.get("brainstorm")
        return deepcopy(brainstorm) if isinstance(brainstorm, dict) else None

    async def start_session(self, project: Project) -> dict[str, Any]:
        """Create or resume a brainstorm session for a project."""
        existing = await self.get_session(project)
        if existing is not None:
            return self._refresh_summary(project, existing)

        agent_output = await self._run_agent(project)
        refined_brief = self._build_refined_brief(project, [])
        questions = self._generate_questions(project)
        first_question = next((q for q in questions if q["status"] == "open"), None)
        overview = self._build_overview(project)
        messages = [
            self._make_message(
                role="assistant",
                content=(
                    "I’ve turned your intake into a guided brainstorm session. "
                    f"{overview} "
                    + (
                        f"Let’s start with: {first_question['prompt']}"
                        if first_question is not None
                        else "The brief already looks strong, so you can review and finalize it."
                    )
                ),
            )
        ]

        session = {
            "session_id": str(uuid4()),
            "project_id": str(project.id),
            "status": "active",
            "started_at": _now_iso(),
            "updated_at": _now_iso(),
            "overview": overview,
            "refined_brief": refined_brief,
            "questions": questions,
            "messages": messages,
            "source_context": self._build_source_context(project),
            "agent_output": agent_output,
        }
        session["summary"] = self._build_summary(project, session)

        config = _ensure_project_config(project)
        config["brainstorm"] = deepcopy(session)
        if project.status == ProjectStatus.CREATED:
            project.status = ProjectStatus.BRAINSTORMING

        await self._db.commit()
        await self._db.refresh(project)
        return session

    async def respond(
        self,
        project: Project,
        *,
        content: str,
        question_id: str | None,
    ) -> dict[str, Any]:
        """Record a user answer and advance the brainstorm session."""
        session = await self.get_session(project)
        if session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Brainstorm session not found",
            )

        if session.get("status") == "finalized":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Brainstorm session has already been finalized",
            )

        normalized_content = content.strip()
        if not normalized_content:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Response content cannot be empty",
            )

        target_question = self._resolve_question(session, question_id)
        target_question["answer"] = normalized_content
        target_question["status"] = "answered"

        session.setdefault("messages", []).append(
            self._make_message(role="user", content=normalized_content)
        )

        session["refined_brief"] = self._build_refined_brief(project, session.get("questions", []))
        session["summary"] = self._build_summary(project, session)

        next_question = next(
            (q for q in session.get("questions", []) if q.get("status") == "open"),
            None,
        )
        assistant_reply = (
            f"Captured. Next up: {next_question['prompt']}"
            if next_question is not None
            else "Captured. You’ve answered the active brainstorm prompts, so the brief is ready for final review."
        )
        session["messages"].append(self._make_message(role="assistant", content=assistant_reply))
        session["updated_at"] = _now_iso()

        config = _ensure_project_config(project)
        config["brainstorm"] = deepcopy(session)

        await self._db.commit()
        await self._db.refresh(project)
        return session

    async def finalize(self, project: Project) -> dict[str, Any]:
        """Finalize brainstorm once blocking questions have been answered."""
        session = await self.get_session(project)
        if session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Brainstorm session not found",
            )

        session = self._refresh_summary(project, session)
        blockers = list(session.get("summary", {}).get("blockers", []))
        if blockers:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Resolve the remaining blocking brainstorm questions before finalizing",
            )

        session["status"] = "finalized"
        session["updated_at"] = _now_iso()
        session.setdefault("messages", []).append(
            self._make_message(
                role="assistant",
                content="Brainstorm finalized. The refined brief is ready for the next pipeline step.",
            )
        )

        project.prd_content = session.get("refined_brief", project.prd_content)
        project.status = ProjectStatus.PLANNING

        config = _ensure_project_config(project)
        config["brainstorm"] = deepcopy(session)

        await self._db.commit()
        await self._db.refresh(project)
        return session

    async def _run_agent(self, project: Project) -> dict[str, Any]:
        """Seed brainstorm state via the registered brainstorming agent."""
        agent = BrainstormingAgent()
        user_input = _first_non_empty(project.prd_content, project.description, project.name)
        try:
            output = await agent.execute(
                AgentInput(
                    task_id=uuid4(),
                    shared_state={
                        "user_input": user_input,
                        "preferences": project.tech_stack or {},
                        "similar_projects": [],
                    },
                    context_tiers={"l0": {}, "l1": {}, "l2": {}},
                )
            )
            brainstorm_output = output.state_updates.get("brainstorming_output", {})
            return brainstorm_output if isinstance(brainstorm_output, dict) else {}
        except Exception:  # noqa: BLE001
            return {
                "refined_requirements": user_input,
                "alternatives": [],
                "risk_assessment": [],
                "feature_priorities": {},
                "user_personas": [],
                "mvp_scope": {},
            }

    def _refresh_summary(self, project: Project, session: dict[str, Any]) -> dict[str, Any]:
        session["refined_brief"] = self._build_refined_brief(project, session.get("questions", []))
        session["summary"] = self._build_summary(project, session)
        return session

    def _resolve_question(
        self,
        session: dict[str, Any],
        question_id: str | None,
    ) -> dict[str, Any]:
        questions = session.get("questions", [])
        if question_id is not None:
            for question in questions:
                if question.get("id") == question_id:
                    return question
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Brainstorm question not found",
            )

        for question in questions:
            if question.get("status") == "open":
                return question

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No open brainstorm questions remain",
        )

    def _build_overview(self, project: Project) -> str:
        source_text = _first_non_empty(project.description, project.prd_content)
        if source_text:
            return _compact_excerpt(source_text)
        return f"{project.name} is ready for clarification so CodeBot can plan the right execution path."

    def _build_source_context(self, project: Project) -> dict[str, Any]:
        config = dict(project.config or {})
        return {
            "project_type": project.project_type.value.lower(),
            "repository_path": project.repository_path or None,
            "repository_url": project.repository_url,
            "tech_stack": project.tech_stack,
            "pipeline_preset": config.get("pipeline_preset", "full"),
        }

    def _generate_questions(self, project: Project) -> list[dict[str, Any]]:
        haystack = " ".join(
            filter(
                None,
                [
                    project.name,
                    project.description,
                    project.prd_content,
                    json.dumps(project.tech_stack or {}, sort_keys=True),
                ],
            )
        ).lower()
        questions: list[dict[str, Any]] = []

        def add_question(
            *,
            category: str,
            prompt: str,
            required: bool,
            priority: str,
        ) -> None:
            questions.append(
                {
                    "id": str(uuid4()),
                    "category": category,
                    "prompt": prompt,
                    "required": required,
                    "priority": priority,
                    "answer": None,
                    "status": "open",
                }
            )

        if not any(keyword in haystack for keyword in ["user", "customer", "team", "admin", "developer"]):
            add_question(
                category="users",
                prompt="Who is the primary user for v1, and what job are they trying to get done?",
                required=True,
                priority="high",
            )

        if not any(keyword in haystack for keyword in ["web", "mobile", "ios", "android", "desktop", "api", "backend", "frontend"]):
            add_question(
                category="platform",
                prompt="What should the first release target: web app, mobile app, backend API, internal tool, or a mix?",
                required=True,
                priority="high",
            )

        if not any(keyword in haystack for keyword in ["success", "metric", "kpi", "goal", "outcome"]):
            add_question(
                category="success",
                prompt="How will you know this project is successful in the first release?",
                required=True,
                priority="high",
            )

        if not any(keyword in haystack for keyword in ["constraint", "deadline", "budget", "compliance", "security", "latency", "scale"]):
            add_question(
                category="constraints",
                prompt="What non-negotiable constraints should CodeBot respect, such as deadlines, compliance, security, or performance?",
                required=True,
                priority="high",
            )

        if project.project_type is ProjectType.BROWNFIELD or project.repository_path or project.repository_url:
            add_question(
                category="brownfield",
                prompt="For the existing codebase, what areas are safe to refactor and what areas must stay untouched?",
                required=True,
                priority="high",
            )

        if not any(keyword in haystack for keyword in ["integrat", "oauth", "github", "stripe", "slack", "webhook", "api"]):
            add_question(
                category="integrations",
                prompt="Does v1 need to integrate with any external systems, APIs, auth providers, or data sources?",
                required=False,
                priority="medium",
            )

        if not any(keyword in haystack for keyword in ["deploy", "aws", "azure", "gcp", "docker", "kubernetes", "self-host"]):
            add_question(
                category="deployment",
                prompt="Do you already know where this should run in production, or should CodeBot recommend a deployment target?",
                required=False,
                priority="medium",
            )

        if not project.tech_stack:
            add_question(
                category="stack",
                prompt="Do you have preferred languages, frameworks, or infrastructure, or should CodeBot optimize for speed and maintainability?",
                required=False,
                priority="medium",
            )

        if not questions:
            add_question(
                category="scope",
                prompt="What should absolutely be included in the MVP, and what can wait until later iterations?",
                required=True,
                priority="high",
            )

        return questions[:6]

    def _build_refined_brief(self, project: Project, questions: list[dict[str, Any]]) -> str:
        base_brief = _first_non_empty(project.prd_content, project.description)
        if not base_brief:
            base_brief = (
                f"Project shell for {project.name}. A detailed PRD has not been provided yet, "
                "so the brainstorm session is filling in the missing execution context."
            )

        answered = [q for q in questions if q.get("answer")]
        if not answered:
            return base_brief

        lines = [base_brief, "", "Clarified decisions:"]
        for question in answered:
            lines.append(f"- {question['category'].title()}: {question['answer']}")
        return "\n".join(lines).strip()

    def _build_summary(self, project: Project, session: dict[str, Any]) -> dict[str, Any]:
        questions = list(session.get("questions", []))
        answered_questions = [q for q in questions if q.get("status") == "answered"]
        open_questions = [q for q in questions if q.get("status") != "answered"]
        required_questions = [q for q in questions if q.get("required")]
        required_open = [q for q in open_questions if q.get("required")]

        total_required = max(len(required_questions), 1)
        required_answered = len(required_questions) - len(required_open)
        total_questions = max(len(questions), 1)
        readiness_score = round(
            ((required_answered / total_required) * 80)
            + ((len(answered_questions) / total_questions) * 20)
        )
        ready_for_pipeline = len(required_open) == 0
        config = dict(project.config or {})

        return {
            "readiness_score": readiness_score,
            "ready_for_pipeline": ready_for_pipeline,
            "blockers": [q["prompt"] for q in required_open],
            "recommended_preset": str(config.get("pipeline_preset", "full")).replace("-", "_"),
            "recommended_next_step": (
                "Finalize brainstorm and launch the execution plan"
                if ready_for_pipeline
                else "Answer the remaining required questions before pipeline kickoff"
            ),
            "open_questions": len(open_questions),
            "answered_questions": len(answered_questions),
            "required_questions_remaining": len(required_open),
        }

    def _make_message(self, *, role: str, content: str) -> dict[str, str]:
        return {
            "id": str(uuid4()),
            "role": role,
            "content": content,
            "created_at": _now_iso(),
        }