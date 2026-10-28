import type { ClaimSummary } from "./api";
import { BackendDown, DecisionChip, StatusChip } from "./Common";
import { STATUS_LABELS, STATUSES, date, label, money } from "./format";
import { useApi } from "./useApi";

export function QueuePage() {
  const { data: claims, failed } = useApi<ClaimSummary[]>("/api/claims", 5000);

  if (!claims) return failed ? <BackendDown /> : <p>Loading the queue</p>;

  return (
    <>
      {failed && <BackendDown />}
      <h1>Claims queue</h1>
      <ul className="tiles" aria-label="Claims by status">
        {STATUSES.map((status) => (
          <li key={status} className="panel tile">
            <span className={`dot status-${status}`} />
            <span className="tile-label">{STATUS_LABELS[status]}</span>{" "}
            <span className="tile-count">
              {claims.filter((claim) => claim.status === status).length}
            </span>
          </li>
        ))}
      </ul>
      <section className="panel table-panel">
        <table>
          <thead>
            <tr>
              <th>Claim</th>
              <th>Customer</th>
              <th>Type</th>
              <th>Summary</th>
              <th className="amount">Claimed</th>
              <th>Submitted</th>
              <th>Status</th>
              <th>Decision</th>
            </tr>
          </thead>
          <tbody>
            {claims.map((claim) => (
              <tr key={claim.claim_id}>
                <td className="nowrap">
                  <a className="mono" href={`#/claims/${claim.claim_id}`}>
                    {claim.claim_id}
                  </a>
                </td>
                <td>{claim.customer_name}</td>
                <td>{label(claim.claim_type)}</td>
                <td>{claim.summary}</td>
                <td className="amount">{money(claim.amount_claimed)}</td>
                <td className="nowrap">{date(claim.submitted_on)}</td>
                <td>
                  <StatusChip status={claim.status} />
                </td>
                <td className="nowrap">
                  {claim.decision && <DecisionChip decision={claim.decision} />}
                  {claim.payout ? (
                    <span className="mono payout">{money(claim.payout)}</span>
                  ) : null}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}
