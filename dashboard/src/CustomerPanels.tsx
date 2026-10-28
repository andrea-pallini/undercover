import type { ClaimHistory, Policy } from "./api";
import { date, label, money } from "./format";
import { useApi } from "./useApi";

export function PolicyPanel({ policyId }: Readonly<{ policyId: string }>) {
  const { data: policy } = useApi<Policy>(`/api/policies/${policyId}`);

  return (
    <section className="panel" aria-labelledby="policy-heading">
      <h2 id="policy-heading">Policy</h2>
      {policy && (
        <dl className="facts">
          <dt>Policy</dt>
          <dd className="mono">{policy.policy_id}</dd>
          <dt>Plan</dt>
          <dd>{label(policy.plan)}</dd>
          <dt>Add-ons</dt>
          <dd>
            {policy.add_ons.length
              ? policy.add_ons.map(label).join(", ")
              : "None"}
          </dd>
          <dt>Bought</dt>
          <dd>
            {date(policy.purchased_on)}, through {policy.sold_through}
          </dd>
          <dt>Trip</dt>
          <dd>
            {policy.trip.destination}, {date(policy.trip.departs_on)} to{" "}
            {date(policy.trip.returns_on)}
          </dd>
          <dt>Trip cost</dt>
          <dd className="mono">{money(policy.trip.trip_cost)}</dd>
          <dt>Travelers</dt>
          <dd>{policy.travelers.join(", ")}</dd>
        </dl>
      )}
    </section>
  );
}

export function HistoryPanel({ customerId }: Readonly<{ customerId: string }>) {
  const { data: history } = useApi<ClaimHistory>(
    `/api/customers/${customerId}/history`,
  );

  return (
    <section className="panel" aria-labelledby="history-heading">
      <h2 id="history-heading">Customer</h2>
      {history && (
        <>
          <p>
            <strong>{history.name}</strong>, a customer since{" "}
            {date(history.customer_since)}
          </p>
          <h3>Earlier claims</h3>
          {history.previous_claims.length ? (
            <ul className="plain">
              {history.previous_claims.map((claim) => (
                <li key={claim.claim_id} className="inset">
                  <span className="mono">{claim.claim_id}</span>,{" "}
                  {date(claim.filed_on)}: {claim.summary}.{" "}
                  {label(claim.outcome)}, paid{" "}
                  <span className="mono">{money(claim.amount_paid)}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="muted">No earlier claims.</p>
          )}
        </>
      )}
    </section>
  );
}
