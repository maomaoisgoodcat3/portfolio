import type { Block } from "@/lib/api";
import { str } from "@/lib/fields";

type Props = { block: Block };

export function StatsBlock({ block }: Props) {
  const accounts = block.items
    .map((item) => ({ id: item.id, account: str(item.data, "account") }))
    .filter((item): item is { id: string; account: string } => item.account !== null);

  return (
    <section className="pixel-box bg-surface p-6 text-text">
      <h2 className="font-pixel text-2xl text-accent">{block.title}</h2>
      {accounts.length > 0 && (
        <ul className="mt-4 list-disc space-y-1 pl-5">
          {accounts.map(({ id, account }) => (
            <li key={id}>{account}</li>
          ))}
        </ul>
      )}
      <p className="mt-4 text-muted">Stats coming soon</p>
    </section>
  );
}
