import { useEffect, useMemo, useState } from "react";
import {
  brainstormApi,
  type BrainstormQuestion,
  type BrainstormSession,
} from "@/api/brainstorm";
import {
  getExecutionPlan,
  getExecutionPlanLabel,
} from "./execution-plan";
import { pipelineApi } from "@/api/pipelines";
import { usePipelineStore } from "@/stores/pipeline-store";
import { useProjectStore } from "@/stores/project-store";
import { useUiStore } from "@/stores/ui-store";

function formatCategory(category: string): string {
  return category
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

export function BrainstormPanel(): React.JSX.Element {
  const activeProjectId = useProjectStore((s) => s.activeProjectId);
  const activeProject = useProjectStore((s) =>
    s.projects.find((project) => project.id === s.activeProjectId),
  );
  const updateProject = useProjectStore((s) => s.updateProject);
  const setActivePanel = useUiStore((s) => s.setActivePanel);
  const upsertPipeline = usePipelineStore((s) => s.upsertPipeline);
  const setActivePipeline = usePipelineStore((s) => s.setActivePipeline);

  const [session, setSession] = useState<BrainstormSession | null>(null);
  const [selectedQuestionId, setSelectedQuestionId] = useState<string | null>(null);
  const [draft, setDraft] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [finalizing, setFinalizing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reviewingPlan, setReviewingPlan] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function loadSession(): Promise<void> {
      if (!activeProjectId) {
        setSession(null);
        setLoading(false);
        return;
      }

      setLoading(true);
      setError(null);

      try {
        const response = await brainstormApi.start(activeProjectId);
        if (!cancelled) {
          setSession(response.data);
          const nextOpen = response.data.questions.find((question) => question.status === "open");
          setSelectedQuestionId(nextOpen?.id ?? null);
          setReviewingPlan(false);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to start brainstorm");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadSession();

    return () => {
      cancelled = true;
    };
  }, [activeProjectId]);

  const openQuestions = useMemo(
    () => session?.questions.filter((question) => question.status === "open") ?? [],
    [session],
  );

  const answeredQuestions = useMemo(
    () => session?.questions.filter((question) => question.status === "answered") ?? [],
    [session],
  );

  const selectedQuestion = useMemo(() => {
    if (!session) {
      return null;
    }
    return (
      session.questions.find((question) => question.id === selectedQuestionId) ??
      openQuestions[0] ??
      null
    );
  }, [openQuestions, selectedQuestionId, session]);

  const executionPlan = useMemo(() => {
    if (!session) {
      return [];
    }

    return getExecutionPlan(session.summary.recommended_preset);
  }, [session]);

  async function handleRespond(question: BrainstormQuestion | null): Promise<void> {
    if (!activeProjectId || !session || !question || !draft.trim()) {
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      const response = await brainstormApi.respond(activeProjectId, {
        content: draft.trim(),
        question_id: question.id,
      });
      setSession(response.data);
      updateProject(activeProjectId, { status: "brainstorming" });
      setDraft("");

      const nextOpen = response.data.questions.find((item) => item.status === "open");
      setSelectedQuestionId(nextOpen?.id ?? null);
      setReviewingPlan(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to submit brainstorm answer");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleFinalize(): Promise<void> {
    if (!activeProjectId || !session) {
      return;
    }

    setFinalizing(true);
    setError(null);
    try {
      const response = await brainstormApi.finalize(activeProjectId);
      setSession(response.data);
      updateProject(activeProjectId, { status: "planning" });

      const mode = String(response.data.summary.recommended_preset).replace(
        /-/g,
        "_",
      ) as "full" | "quick" | "review_only";
      const createdPipeline = await pipelineApi.create(activeProjectId, mode);
      await pipelineApi.start(createdPipeline.data.id);
      const detailedPipeline = await pipelineApi.get(createdPipeline.data.id);
      upsertPipeline(detailedPipeline.data);
      setActivePipeline(detailedPipeline.data.id);
      setActivePanel("pipeline");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to finalize brainstorm");
    } finally {
      setFinalizing(false);
    }
  }

  if (!activeProjectId || !activeProject) {
    return (
      <div className="flex h-full items-center justify-center text-sm text-gray-500 dark:text-gray-400">
        Select a project to start brainstorming.
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-200 border-t-blue-500" />
      </div>
    );
  }

  if (!session) {
    return (
      <div className="flex h-full items-center justify-center px-6 text-sm text-red-500 dark:text-red-400">
        {error ?? "Unable to load brainstorm session."}
      </div>
    );
  }

  return (
    <div className="grid h-full grid-cols-12 gap-4 p-4">
      <section className="col-span-3 flex min-h-0 flex-col rounded-2xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-900">
        <div className="mb-4">
          <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
            Guided questions
          </h3>
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            {session.summary.open_questions} open · {session.summary.answered_questions} answered
          </p>
        </div>

        <div className="space-y-2 overflow-y-auto">
          {session.questions.map((question) => {
            const isSelected = selectedQuestion?.id === question.id;
            const isAnswered = question.status === "answered";
            return (
              <button
                key={question.id}
                type="button"
                onClick={() => setSelectedQuestionId(question.id)}
                className={`w-full rounded-xl border p-3 text-left transition-colors ${
                  isSelected
                    ? "border-blue-500 bg-blue-50 dark:border-blue-400 dark:bg-blue-950"
                    : "border-gray-200 hover:border-gray-300 dark:border-gray-700 dark:hover:border-gray-600"
                }`}
              >
                <div className="mb-1 flex items-center justify-between gap-2">
                  <span className="text-xs font-medium uppercase tracking-wide text-gray-400">
                    {formatCategory(question.category)}
                  </span>
                  <span
                    className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                      isAnswered
                        ? "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300"
                        : question.required
                          ? "bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-300"
                          : "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-300"
                    }`}
                  >
                    {isAnswered ? "Answered" : question.required ? "Required" : "Optional"}
                  </span>
                </div>
                <p className="text-sm text-gray-700 dark:text-gray-200">{question.prompt}</p>
              </button>
            );
          })}
        </div>
      </section>

      <section className="col-span-6 flex min-h-0 flex-col rounded-2xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-900">
        <div className="mb-4 border-b border-gray-200 pb-4 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            {activeProject.name} brainstorm
          </h2>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">{session.overview}</p>
        </div>

        <div className="mb-4 flex-1 space-y-3 overflow-y-auto rounded-xl bg-gray-50 p-4 dark:bg-gray-950">
          {session.messages.map((message) => (
            <div
              key={message.id}
              className={`max-w-[90%] rounded-2xl px-4 py-3 text-sm ${
                message.role === "assistant"
                  ? "bg-white text-gray-700 shadow-sm dark:bg-gray-900 dark:text-gray-200"
                  : "ml-auto bg-blue-600 text-white"
              }`}
            >
              {message.content}
            </div>
          ))}
        </div>

        {reviewingPlan && session.summary.ready_for_pipeline ? (
          <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-5 dark:border-emerald-900 dark:bg-emerald-950">
            <div className="mb-4 flex items-start justify-between gap-4">
              <div>
                <h3 className="text-base font-semibold text-emerald-900 dark:text-emerald-100">
                  Execution summary
                </h3>
                <p className="mt-1 text-sm text-emerald-800 dark:text-emerald-200">
                  CodeBot is ready to launch the {getExecutionPlanLabel(session.summary.recommended_preset).toLowerCase()} pipeline for this clarified brief.
                </p>
              </div>
              <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-emerald-700 shadow-sm dark:bg-emerald-900 dark:text-emerald-200">
                Ready to launch
              </span>
            </div>

            <div className="grid gap-3">
              {executionPlan.map((step, index) => (
                <div
                  key={step.key}
                  className="rounded-xl border border-emerald-200 bg-white p-4 dark:border-emerald-800 dark:bg-emerald-900/40"
                >
                  <div className="flex items-center gap-3">
                    <div className="flex h-7 w-7 items-center justify-center rounded-full bg-emerald-100 text-xs font-semibold text-emerald-700 dark:bg-emerald-900 dark:text-emerald-200">
                      {index + 1}
                    </div>
                    <div>
                      <h4 className="text-sm font-semibold text-gray-900 dark:text-white">
                        {step.label}
                      </h4>
                      <p className="text-sm text-gray-600 dark:text-gray-300">
                        {step.description}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-4 flex items-center justify-between gap-4">
              <p className="text-xs text-emerald-800 dark:text-emerald-200">
                Launching will finalize the brainstorm, create the pipeline, and open the execution view.
              </p>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setReviewingPlan(false)}
                  className="rounded-lg border border-emerald-300 px-4 py-2 text-sm font-medium text-emerald-800 hover:bg-emerald-100 dark:border-emerald-700 dark:text-emerald-200 dark:hover:bg-emerald-900"
                >
                  Back to brief
                </button>
                <button
                  type="button"
                  onClick={() => {
                    void handleFinalize();
                  }}
                  disabled={finalizing}
                  className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:bg-gray-300 disabled:text-gray-500"
                >
                  {finalizing ? "Launching..." : "Launch pipeline"}
                </button>
              </div>
            </div>
          </div>
        ) : selectedQuestion ? (
          <div className="rounded-xl border border-gray-200 p-4 dark:border-gray-700">
            <div className="mb-2 flex items-center justify-between gap-3">
              <div>
                <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
                  {formatCategory(selectedQuestion.category)}
                </h3>
                <p className="mt-1 text-sm text-gray-600 dark:text-gray-300">
                  {selectedQuestion.prompt}
                </p>
              </div>
              {selectedQuestion.required && (
                <span className="rounded-full bg-amber-100 px-2.5 py-1 text-xs font-medium text-amber-700 dark:bg-amber-900 dark:text-amber-300">
                  Required
                </span>
              )}
            </div>

            <textarea
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              placeholder="Answer this question so CodeBot can refine the brief…"
              rows={5}
              className="w-full rounded-xl border border-gray-300 bg-white px-4 py-3 text-sm text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800 dark:text-white"
            />

            <div className="mt-3 flex items-center justify-between">
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Keep answers specific—users, platforms, constraints, and success criteria are especially helpful.
              </p>
              <button
                type="button"
                onClick={() => {
                  void handleRespond(selectedQuestion);
                }}
                disabled={submitting || !draft.trim()}
                className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:bg-gray-300 disabled:text-gray-500"
              >
                {submitting ? "Saving..." : "Send answer"}
              </button>
            </div>
          </div>
        ) : (
          <div className="rounded-xl border border-green-200 bg-green-50 p-4 text-sm text-green-800 dark:border-green-900 dark:bg-green-950 dark:text-green-200">
            All current brainstorm questions are answered. Review the brief, then open the execution summary when you’re ready to launch.
          </div>
        )}

        {error && (
          <div className="mt-3 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600 dark:border-red-800 dark:bg-red-950 dark:text-red-400">
            {error}
          </div>
        )}
      </section>

      <aside className="col-span-3 flex min-h-0 flex-col gap-4">
        <div className="rounded-2xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-900">
          <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
            Readiness
          </h3>
          <div className="mt-3">
            <div className="mb-2 flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
              <span>Kickoff score</span>
              <span>{session.summary.readiness_score}%</span>
            </div>
            <div className="h-2 rounded-full bg-gray-200 dark:bg-gray-700">
              <div
                className="h-2 rounded-full bg-blue-500 transition-all"
                style={{ width: `${String(session.summary.readiness_score)}%` }}
              />
            </div>
          </div>

          <div className="mt-4 space-y-2 text-sm text-gray-600 dark:text-gray-300">
            <div className="flex items-center justify-between">
              <span>Preset</span>
              <span className="font-medium text-gray-900 dark:text-white">
                {String(session.summary.recommended_preset).replaceAll("_", " ")}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span>Required left</span>
              <span className="font-medium text-gray-900 dark:text-white">
                {session.summary.required_questions_remaining}
              </span>
            </div>
          </div>

          <button
            type="button"
            onClick={() => setReviewingPlan(true)}
            disabled={finalizing || !session.summary.ready_for_pipeline}
            className="mt-4 w-full rounded-lg bg-emerald-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-emerald-700 disabled:bg-gray-300 disabled:text-gray-500"
          >
            Review execution plan
          </button>
          <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
            Once the required answers are in place, review the launch plan before CodeBot starts the pipeline.
          </p>
        </div>

        <div className="min-h-0 flex-1 rounded-2xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-900">
          <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
            Refined brief
          </h3>
          <pre className="mt-3 max-h-[340px] overflow-auto whitespace-pre-wrap text-sm leading-6 text-gray-700 dark:text-gray-200">
            {session.refined_brief}
          </pre>

          {session.summary.blockers.length > 0 && (
            <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50 p-3 dark:border-amber-900 dark:bg-amber-950">
              <h4 className="text-xs font-semibold uppercase tracking-wide text-amber-700 dark:text-amber-300">
                Blocking questions
              </h4>
              <ul className="mt-2 space-y-2 text-xs text-amber-800 dark:text-amber-200">
                {session.summary.blockers.map((blocker) => (
                  <li key={blocker}>• {blocker}</li>
                ))}
              </ul>
            </div>
          )}

          {session.summary.ready_for_pipeline && (
            <div className="mt-4 rounded-xl border border-emerald-200 bg-emerald-50 p-3 dark:border-emerald-900 dark:bg-emerald-950">
              <h4 className="text-xs font-semibold uppercase tracking-wide text-emerald-700 dark:text-emerald-300">
                Launch configuration
              </h4>
              <div className="mt-2 space-y-2 text-xs text-emerald-900 dark:text-emerald-200">
                <div className="flex items-center justify-between gap-3">
                  <span>Recommended preset</span>
                  <span className="font-semibold">
                    {getExecutionPlanLabel(session.summary.recommended_preset)}
                  </span>
                </div>
                <div className="flex items-center justify-between gap-3">
                  <span>Planned stages</span>
                  <span className="font-semibold">{executionPlan.length}</span>
                </div>
                <div className="flex items-center justify-between gap-3">
                  <span>Pipeline readiness</span>
                  <span className="font-semibold">{session.summary.readiness_score}%</span>
                </div>
              </div>
            </div>
          )}

          {answeredQuestions.length > 0 && (
            <div className="mt-4 rounded-xl border border-gray-200 p-3 dark:border-gray-700">
              <h4 className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
                Captured answers
              </h4>
              <div className="mt-2 space-y-2 text-xs text-gray-600 dark:text-gray-300">
                {answeredQuestions.map((question) => (
                  <div key={question.id}>
                    <span className="font-semibold text-gray-800 dark:text-gray-100">
                      {formatCategory(question.category)}:
                    </span>{" "}
                    {question.answer}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </aside>
    </div>
  );
}