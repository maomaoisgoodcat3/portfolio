import type { Block } from "@/lib/api";
import { str } from "@/lib/fields";

type Props = { block: Block };

export function StatsBlock({ block }: Props) {
  const provider = str(block.props, "provider");
  const account = str(block.props, "account");

  return (
    <article className="pixel-box w-full bg-surface p-4 text-text">
      <h3 className="font-pixel text-xl text-accent">{block.title}</h3>
      {(provider || account) && <p className="mt-1 text-sm text-muted">{[provider, account].filter(Boolean).join(" · ")}</p>}
      <p className="mt-2 text-muted">Stats coming soon</p>
    </article>
  );
}
