import axios from "axios";
import type { PipelineResult , Media } from "../types";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
});

export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    return error.response?.data?.detail ?? error.message;
  }
  return error instanceof Error ? error.message : "Unknown error";
}

export async function fetchDrafts(status?: string): Promise<PipelineResult[]> {
  const { data } = await api.get<PipelineResult[]>("/drafts", { params: { status } });
  return data;
}

export async function approveDraft(repoName: string, commitSha: string): Promise<void> {
  await api.post(`/drafts/${encodeURIComponent(repoName)}/${commitSha}/approve`);
}

export async function rejectDraft(repoName: string, commitSha: string): Promise<void> {
  await api.post(`/drafts/${encodeURIComponent(repoName)}/${commitSha}/reject`);
}

export async function regenerateDraft(
  repoName: string,
  commitSha: string,
  note?: string
): Promise<{ draft: PipelineResult["draft"]; verified: boolean }> {
  const { data } = await api.post(
    `/drafts/${encodeURIComponent(repoName)}/${commitSha}/regenerate`,
    { note: note ?? null }
  );
  return data;
}

export async function uploadMedia(repoName: string, commitSha: string, file: File): Promise<{ media: Media }> {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await api.post(
    `/drafts/${encodeURIComponent(repoName)}/${commitSha}/media`,
    formData,
    { headers: { "Content-Type": "multipart/form-data" } }
  );
  return data;
}