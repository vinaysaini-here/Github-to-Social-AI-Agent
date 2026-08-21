export interface Classification {
  change_type: string;
  reasoning: string;
}

export interface Worthiness {
  score: number;
  reason: string;
}

export interface Draft {
  linkedin_post: string;
  x_post: string;
}

export interface Verification {
  verified: boolean;
  issues: string[];
}

export interface PipelineResult {
  repo_name: string;
  commit_sha: string;
  commit_message: string;
  approval_status: "pending" | "approved" | "rejected";
  classification: Classification;
  worthiness: Worthiness;
  draft: Draft;
  verification: Verification;
}