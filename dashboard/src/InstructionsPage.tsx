import type { Instructions } from "./api";
import { BackendDown } from "./Common";
import { useApi } from "./useApi";

export function InstructionsPage() {
  const { data: instructions, failed } =
    useApi<Instructions>("/api/instructions");

  return (
    <>
      <h1>Agent instructions</h1>
      <p className="muted">
        Read only. The agent reads these at the start of every claim.
      </p>
      {failed && <BackendDown />}
      {instructions && (
        <section className="panel">
          <div className="instructions">{instructions.text}</div>
        </section>
      )}
    </>
  );
}
