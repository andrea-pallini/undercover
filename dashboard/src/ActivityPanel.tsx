import type { Progress } from "./api";
import { time, timeLeft } from "./format";
import { useApi } from "./useApi";

function RunState({ progress }: Readonly<{ progress: Progress }>) {
  if (progress.seconds_remaining !== null) {
    return (
      <p>
        <span className="chip estimate">
          {timeLeft(progress.seconds_remaining)}
        </span>
      </p>
    );
  }
  if (progress.finished_at) {
    return <p className="muted">Finished at {time(progress.finished_at)}</p>;
  }
  return null;
}

export function ActivityPanel({ claimId }: Readonly<{ claimId: string }>) {
  const { data: progress } = useApi<Progress>(
    `/api/claims/${claimId}/progress`,
    2000,
  );

  return (
    <section className="panel" aria-labelledby="activity-heading">
      <h2 id="activity-heading">Agent activity</h2>
      {progress === null && (
        <p className="muted">The agent hasn't worked on this claim yet.</p>
      )}
      {progress && (
        <>
          <RunState progress={progress} />
          <ol className="plain steps">
            {progress.steps.map((step) => (
              <li key={`${step.at} ${step.description}`}>
                <span className="mono muted">{time(step.at)}</span>
                <span>{step.description}</span>
              </li>
            ))}
          </ol>
        </>
      )}
    </section>
  );
}
