export type Status =
  "waiting" | "in_progress" | "waiting_for_sign_off" | "decided";
export type DecisionKind = "approve" | "decline" | "refer";

export interface ClaimSummary {
  claim_id: string;
  customer_name: string;
  claim_type: string;
  summary: string;
  amount_claimed: number;
  submitted_on: string;
  status: Status;
  decision: DecisionKind | null;
  payout: number | null;
}

export interface Item {
  description: string;
  category: string;
  amount: number;
}

export interface ClaimDocument {
  name: string;
  type: string;
  content: string;
}

export interface Claim {
  claim_id: string;
  policy_id: string;
  customer_id: string;
  claim_type: string;
  submitted_on: string;
  incident_date: string;
  incident_location: string;
  summary: string;
  story: string;
  items: Item[];
  amount_claimed: number;
  documents: ClaimDocument[];
  status: Status;
}

export interface Policy {
  policy_id: string;
  customer_id: string;
  plan: string;
  add_ons: string[];
  purchased_on: string;
  sold_through: string;
  trip: {
    destination: string;
    departs_on: string;
    returns_on: string;
    trip_cost: number;
  };
  travelers: string[];
  status: string;
}

export interface PreviousClaim {
  claim_id: string;
  filed_on: string;
  incident_date: string;
  claim_type: string;
  summary: string;
  outcome: string;
  amount_paid: number;
}

export interface ClaimHistory {
  customer_id: string;
  name: string;
  customer_since: string;
  previous_claims: PreviousClaim[];
}

export interface Instructions {
  text: string;
}

export async function getJson<T>(path: string): Promise<T | null> {
  const response = await fetch(path);
  if (response.status === 404) return null;
  if (!response.ok) throw new Error(`${path} failed`);
  return (await response.json()) as T;
}

export interface Handler {
  handler_id: string;
  name: string;
  role: string;
  email: string;
  can_approve_over_limit: boolean;
}

export interface Step {
  at: string;
  description: string;
}

export interface Progress {
  thread_id: string;
  claim_id: string;
  started_at: string;
  finished_at: string | null;
  steps: Step[];
  seconds_remaining: number | null;
}

export interface Decision {
  claim_id: string;
  decision: DecisionKind;
  payout: number;
  reasons: string;
  policy_section: string;
  confidence: number;
  decided_at: string;
  needs_sign_off: boolean;
  sign_off: { handler_id: string; handler_name: string; at: string } | null;
  payment: { amount: number; paid_at: string } | null;
}

/** Posts to the backend, and rejects with the backend's reason if it refuses. */
export async function post(path: string, body: object): Promise<void> {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const { detail } = (await response.json()) as { detail: string };
    throw new Error(detail);
  }
}

/** The reason a request failed, to show to the handler. */
export function reasonFor(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}
