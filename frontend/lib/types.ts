export type PolicyStatus = "SUPPORTED" | "PARTIAL" | "DEFICIT";

export interface Question {
  id: string;
  question_text: string;
  required_control: string;
  risk_domain: string;
}

export interface Answer {
  question_id: string;
  status: PolicyStatus;
  answer_text: string;
  citations: string[];
  policy_reason: string;
}

export interface RemediationTask {
  question_id: string;
  title: string;
  description: string;
  severity: string;
  suggested_owner: string;
}

export interface TrustPacket {
  answers: Answer[];
  remediation_tasks: RemediationTask[];
  summary: string;
}
