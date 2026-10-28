import { vi } from "vitest";
import type {
  Claim,
  ClaimHistory,
  ClaimSummary,
  Instructions,
  Policy,
} from "./api";

/** Stubs fetch with a response for each path. Any other path returns 404. */
export function stubApi(routes: Record<string, unknown>) {
  const fetchMock = vi.fn((path: string) =>
    Promise.resolve(
      path in routes
        ? new Response(JSON.stringify(routes[path]))
        : new Response("{}", { status: 404 }),
    ),
  );
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

export const summaries: ClaimSummary[] = [
  {
    claim_id: "CLM-1001",
    customer_name: "Maya Patel",
    claim_type: "trip_delay",
    summary: "Flight home canceled by the airline",
    amount_claimed: 420,
    submitted_on: "2026-06-24",
    status: "decided",
    decision: "approve",
    payout: 420,
  },
  {
    claim_id: "CLM-1002",
    customer_name: "Tom Okafor",
    claim_type: "baggage",
    summary: "Suitcase lost on a connecting flight",
    amount_claimed: 1150,
    submitted_on: "2026-07-02",
    status: "waiting",
    decision: null,
    payout: null,
  },
];

export const claim: Claim = {
  claim_id: "CLM-1001",
  policy_id: "POL-2001",
  customer_id: "CUS-3001",
  claim_type: "trip_delay",
  submitted_on: "2026-06-24",
  incident_date: "2026-06-18",
  incident_location: "Rome, Italy",
  summary: "Flight home canceled by the airline",
  story: "My flight home from Rome was canceled.",
  items: [
    { description: "Airport hotel", category: "accommodation", amount: 245 },
    { description: "Dinner", category: "meals", amount: 175 },
  ],
  amount_claimed: 420,
  documents: [
    {
      name: "Hotel receipt",
      type: "receipt",
      content: "One night: $245.00.",
    },
  ],
  status: "waiting",
};

export const policy: Policy = {
  policy_id: "POL-2001",
  customer_id: "CUS-3001",
  plan: "premium",
  add_ons: ["electronics_plus"],
  purchased_on: "2026-04-22",
  sold_through: "Meridian Air checkout",
  trip: {
    destination: "Rome, Italy",
    departs_on: "2026-06-10",
    returns_on: "2026-06-18",
    trip_cost: 3100,
  },
  travelers: ["Maya Patel"],
  status: "active",
};

export const history: ClaimHistory = {
  customer_id: "CUS-3001",
  name: "Maya Patel",
  customer_since: "2023-04-11",
  previous_claims: [
    {
      claim_id: "CLM-0412",
      filed_on: "2024-08-19",
      incident_date: "2024-08-09",
      claim_type: "baggage_delay",
      summary: "Checked bag arrived 30 hours late",
      outcome: "approved",
      amount_paid: 140,
    },
  ],
};

export const instructions: Instructions = {
  text: "# The UnderCover Agent\n\nYou decide claims.",
};

export const claimRoutes = {
  "/api/claims/CLM-1001": claim,
  "/api/policies/POL-2001": policy,
  "/api/customers/CUS-3001/history": history,
};
