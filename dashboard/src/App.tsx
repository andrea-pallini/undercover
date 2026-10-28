import { useEffect, useState } from "react";
import { ClaimPage } from "./ClaimPage";
import { InstructionsPage } from "./InstructionsPage";
import { QueuePage } from "./QueuePage";

function useHash(): string {
  const [hash, setHash] = useState(() => window.location.hash);

  useEffect(() => {
    const update = () => {
      setHash(window.location.hash);
    };
    window.addEventListener("hashchange", update);
    return () => {
      window.removeEventListener("hashchange", update);
    };
  }, []);

  return hash;
}

function Page({
  claim,
  onInstructions,
}: Readonly<{
  claim: string | undefined;
  onInstructions: boolean;
}>) {
  if (claim) return <ClaimPage key={claim} claimId={claim} />;
  if (onInstructions) return <InstructionsPage />;
  return <QueuePage />;
}

export function App() {
  const hash = useHash();
  const claim = /^#\/claims\/(.+)$/.exec(hash)?.[1];
  const onInstructions = hash === "#/instructions";

  return (
    <>
      <header className="masthead">
        <a className="brand" href="#/">
          UnderCover
        </a>
        <span className="tagline">Claims desk</span>
        <nav aria-label="Main">
          <a
            href="#/"
            aria-current={!claim && !onInstructions ? "page" : undefined}
          >
            Claims queue
          </a>
          <a
            href="#/instructions"
            aria-current={onInstructions ? "page" : undefined}
          >
            Agent instructions
          </a>
        </nav>
      </header>
      <main>
        <Page claim={claim} onInstructions={onInstructions} />
      </main>
    </>
  );
}
