import { useState } from "react";
import type { Decision, Handler } from "./api";
import { post, reasonFor } from "./api";
import { DecisionChip } from "./Common";
import { moment, money } from "./format";
import { useApi } from "./useApi";

function SignOffForm({
  decision,
  onSignedOff,
}: Readonly<{ decision: Decision; onSignedOff: () => void }>) {
  const { data: handlers } = useApi<Handler[]>("/api/handlers");
  const [handlerId, setHandlerId] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const signOff = () => {
    setBusy(true);
    post(`/api/claims/${decision.claim_id}/sign-off`, {
      handler_id: handlerId,
    }).then(onSignedOff, (reason: unknown) => {
      setBusy(false);
      setError(reasonFor(reason));
    });
  };

  return (
    <form
      className="sign-off"
      onSubmit={(event) => {
        event.preventDefault();
        signOff();
      }}
    >
      <label>
        Handler{" "}
        <select
          value={handlerId}
          onChange={(event) => {
            setHandlerId(event.target.value);
          }}
        >
          <option value="">Choose a handler</option>
          {handlers?.map((handler) => (
            <option key={handler.handler_id} value={handler.handler_id}>
              {handler.name}
            </option>
          ))}
        </select>
      </label>
      <button className="primary" type="submit" disabled={!handlerId || busy}>
        Sign off and pay {money(decision.payout)}
      </button>
      {error && (
        <p className="alert" role="alert">
          {error}
        </p>
      )}
    </form>
  );
}

function PaymentState({
  decision,
  onSignedOff,
}: Readonly<{ decision: Decision; onSignedOff: () => void }>) {
  if (decision.payment) {
    return (
      <>
        <p className="paid">
          Paid {money(decision.payment.amount)} on{" "}
          {moment(decision.payment.paid_at)}
        </p>
        {decision.sign_off && (
          <p>
            Signed off by {decision.sign_off.handler_name} on{" "}
            {moment(decision.sign_off.at)}
          </p>
        )}
      </>
    );
  }
  if (decision.needs_sign_off) {
    return (
      <>
        <p className="notice">Waiting for a handler's sign-off</p>
        <SignOffForm decision={decision} onSignedOff={onSignedOff} />
      </>
    );
  }
  return <p className="muted">Not paid yet</p>;
}

export function DecisionPanel({
  claimId,
  onSignedOff,
}: Readonly<{ claimId: string; onSignedOff: () => void }>) {
  const { data: decision, reload } = useApi<Decision>(
    `/api/claims/${claimId}/decision`,
    2000,
  );

  return (
    <section className="panel" aria-labelledby="decision-heading">
      <h2 id="decision-heading">Decision</h2>
      {decision === null && <p className="muted">No decision yet.</p>}
      {decision && (
        <>
          <p className="verdict">
            <DecisionChip decision={decision.decision} />
            {decision.decision === "approve" && (
              <span className="mono">{money(decision.payout)}</span>
            )}
          </p>
          <p className="reasons">{decision.reasons}</p>
          <dl className="facts">
            <dt>Policy section</dt>
            <dd>{decision.policy_section}</dd>
            <dt>Confidence</dt>
            <dd className="mono">{decision.confidence}%</dd>
            <dt>Decided</dt>
            <dd>{moment(decision.decided_at)}</dd>
          </dl>
          {decision.decision === "approve" && (
            <PaymentState
              decision={decision}
              onSignedOff={() => {
                reload();
                onSignedOff();
              }}
            />
          )}
        </>
      )}
    </section>
  );
}
