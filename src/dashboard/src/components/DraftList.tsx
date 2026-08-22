import { useEffect, useState } from "react";
import type { PipelineResult } from "../types";
import { fetchDrafts, getErrorMessage } from "../api/client";
import { DraftCard } from "./DraftCard";

export function DraftList() {
  const [drafts, setDrafts] = useState<PipelineResult[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchDrafts()
      .then(setDrafts)
      .catch((err) => setError(getErrorMessage(err)));
  }, []);

  function handleChange(updated: PipelineResult) {
    setDrafts((prev) => prev?.map((d) => (d.commit_sha === updated.commit_sha ? updated : d)) ?? null);
  }

  if (error) {
    return <p className="text-danger text-sm p-6">Couldn't load drafts: {error}</p>;
  }
  if (drafts === null) {
    return <p className="text-muted text-sm p-6">Loading drafts…</p>;
  }
  if (drafts.length === 0) {
    return <p className="text-muted text-sm p-6">No drafts yet — push a commit and check back.</p>;
  }

  return (
    <div className="max-w-2xl mx-auto py-8 px-4 space-y-4">
      {drafts.map((draft) => (
        <DraftCard key={draft.commit_sha} result={draft} onChange={handleChange} />
      ))}
    </div>
  );
}