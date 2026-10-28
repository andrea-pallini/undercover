import { useState } from "react";
import { ActivityPanel } from "./ActivityPanel";
import type { Claim } from "./api";
import { post, reasonFor } from "./api";
import { BackendDown, StatusChip } from "./Common";
import { HistoryPanel, PolicyPanel } from "./CustomerPanels";
import { DecisionPanel } from "./DecisionPanel";
import { date, label, money } from "./format";
import { useApi } from "./useApi";

function RunButton({
  claimId,
  onStarted,
}: Readonly<{ claimId: string; onStarted: () => void }>) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const start = () => {
    setBusy(true);
    setError("");
    post(`/api/claims/${claimId}/agent`, {}).then(
      () => {
        setBusy(false);
        onStarted();
      },
      (reason: unknown) => {
        setBusy(false);
        setError(reasonFor(reason));
      },
    );
  };

  return (
    <>
      <button className="primary" type="button" disabled={busy} onClick={start}>
        {busy ? "Starting the agent" : "Run the agent"}
      </button>
      {error && (
        <p className="alert" role="alert">
          {error}
        </p>
      )}
    </>
  );
}

export function ClaimPage({ claimId }: Readonly<{ claimId: string }>) {
  const {
    data: claim,
    failed,
    reload,
  } = useApi<Claim>(`/api/claims/${claimId}`, 2000);

  if (claim === null) return <p>There is no claim {claimId}.</p>;
  if (!claim) return failed ? <BackendDown /> : <p>Loading the claim</p>;

  return (
    <>
      {failed && <BackendDown />}
      <a href="#/">Back to the queue</a>
      <div className="claim-head">
        <h1 className="mono">{claim.claim_id}</h1>
        <StatusChip status={claim.status} />
        {claim.status === "waiting" && (
          <RunButton claimId={claim.claim_id} onStarted={reload} />
        )}
      </div>
      <p className="lede">{claim.summary}</p>
      <div className="claim-grid">
        <div>
          <DecisionPanel claimId={claim.claim_id} onSignedOff={reload} />
          <ClaimPanel claim={claim} />
        </div>
        <div>
          <ActivityPanel claimId={claim.claim_id} />
          <PolicyPanel policyId={claim.policy_id} />
          <HistoryPanel customerId={claim.customer_id} />
        </div>
      </div>
    </>
  );
}

function ClaimPanel({ claim }: Readonly<{ claim: Claim }>) {
  return (
    <section className="panel" aria-labelledby="claim-heading">
      <h2 id="claim-heading">The claim</h2>
      <dl className="facts">
        <dt>Type</dt>
        <dd>{label(claim.claim_type)}</dd>
        <dt>Incident</dt>
        <dd>
          {date(claim.incident_date)}, {claim.incident_location}
        </dd>
        <dt>Submitted</dt>
        <dd>{date(claim.submitted_on)}</dd>
      </dl>
      <h3>The customer's story</h3>
      <p className="story">{claim.story}</p>
      <h3>Items claimed</h3>
      <table>
        <thead>
          <tr>
            <th>Item</th>
            <th>Category</th>
            <th className="amount">Amount</th>
          </tr>
        </thead>
        <tbody>
          {claim.items.map((item) => (
            <tr key={item.description}>
              <td>{item.description}</td>
              <td>{label(item.category)}</td>
              <td className="amount">{money(item.amount)}</td>
            </tr>
          ))}
        </tbody>
        <tfoot>
          <tr>
            <th colSpan={2}>Total</th>
            <td className="amount">{money(claim.amount_claimed)}</td>
          </tr>
        </tfoot>
      </table>
      <h3>Documents</h3>
      <ul className="plain">
        {claim.documents.map((document) => (
          <li key={document.name} className="inset">
            <strong>{document.name}</strong>{" "}
            <span className="muted">{label(document.type)}</span>
            <p>{document.content}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}
