import { useState } from "react";
import type { PipelineResult } from "../types";
import { approveDraft, rejectDraft, regenerateDraft, getErrorMessage } from "../api/client";

interface Props {
  result: PipelineResult;
  onChange: (updated: PipelineResult) => void;
}

const STATUS_STYLES: Record<PipelineResult["approval_status"], string> = {
  pending: "bg-warn/15 text-warn",
  approved: "bg-accent/15 text-accent",
  rejected: "bg-danger/15 text-danger",
};

function worthinessColor(score: number): string {
  if (score >= 70) return "bg-accent";
  if (score >= 30) return "bg-warn";
  return "bg-danger";
}

export function DraftCard({ result, onChange }: Props) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [note, setNote] = useState("");
  const [showNoteInput, setShowNoteInput] = useState(false);

  async function handleApprove() {
    setBusy(true);
    setError(null);
    try {
      await approveDraft(result.repo_name, result.commit_sha);
      onChange({ ...result, approval_status: "approved" });
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  async function handleReject() {
    setBusy(true);
    setError(null);
    try {
      await rejectDraft(result.repo_name, result.commit_sha);
      onChange({ ...result, approval_status: "rejected" });
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  async function handleRegenerate() {
    setBusy(true);
    setError(null);
    try {
      const { draft, verified } = await regenerateDraft(result.repo_name, result.commit_sha, note || undefined);
      onChange({
        ...result,
        draft,
        verification: { verified, issues: verified ? [] : result.verification.issues },
        approval_status: "pending",
      });
      setNote("");
      setShowNoteInput(false);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <article className="border border-line rounded-lg bg-white p-5 space-y-4">
      <header className="flex items-start justify-between gap-4">
        <div>
          <p className="font-mono text-xs text-muted">
            {result.repo_name} · {result.commit_sha.slice(0, 8)}
          </p>
          <p className="text-ink font-medium mt-0.5">{result.commit_message.split("\n")[0]}</p>
        </div>
        <span className={`text-xs px-2 py-1 rounded-full font-medium shrink-0 ${STATUS_STYLES[result.approval_status]}`}>
          {result.approval_status}
        </span>
      </header>

      <div className="flex items-center gap-3">
        <span className="text-xs font-mono text-muted uppercase">{result.classification.change_type}</span>
        <div className="flex-1 h-1.5 rounded-full bg-line overflow-hidden">
          <div
            className={`h-full rounded-full ${worthinessColor(result.worthiness.score)}`}
            style={{ width: `${result.worthiness.score}%` }}
          />
        </div>
        <span className="text-xs font-mono text-muted">{result.worthiness.score}/100</span>
      </div>
      <p className="text-xs text-muted">{result.worthiness.reason}</p>

      {!result.verification.verified && (
        <p className="text-xs text-danger bg-danger-soft rounded px-2 py-1">
          Not fully grounded: {result.verification.issues.join("; ")}
        </p>
      )}

      <div className="space-y-3">
        <div>
          <p className="text-xs font-mono text-muted mb-1">LinkedIn</p>
          <p className="text-sm text-ink whitespace-pre-wrap">{result.draft.linkedin_post}</p>
        </div>
        <div>
          <p className="text-xs font-mono text-muted mb-1">X</p>
          <p className="text-sm text-ink whitespace-pre-wrap">{result.draft.x_post}</p>
        </div>
      </div>

      {error && <p className="text-xs text-danger">{error}</p>}

      {showNoteInput && (
        <input
          type="text"
          value={note}
          onChange={(e) => setNote(e.target.value)}
          placeholder="What should change? (optional)"
          className="w-full text-sm border border-line rounded px-3 py-1.5 outline-none focus:border-accent"
        />
      )}

      <div className="flex gap-2 pt-1">
        <button
          onClick={handleApprove}
          disabled={busy}
          className="text-sm px-3 py-1.5 rounded bg-accent text-white disabled:opacity-50"
        >
          Approve
        </button>
        <button
          onClick={handleReject}
          disabled={busy}
          className="text-sm px-3 py-1.5 rounded border border-line text-ink disabled:opacity-50"
        >
          Reject
        </button>
        <button
          onClick={showNoteInput ? handleRegenerate : () => setShowNoteInput(true)}
          disabled={busy}
          className="text-sm px-3 py-1.5 rounded border border-line text-ink disabled:opacity-50"
        >
          {showNoteInput ? "Send & regenerate" : "Regenerate"}
        </button>
      </div>
    </article>
  );
}