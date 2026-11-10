import type { Block } from "@/lib/api";
import { str } from "@/lib/fields";

type Props = { block: Block };

export function StatsBlock({ block }: Props) {
  const accounts = block.items
    .map((item) => ({ id: item.id, account: str(item.data, "account") }))
    .filter((item): item is { id: string; account: string } => item.account !== null);

  return (
    <section>
      <h2 className="text-2xl font-semibold text-slate-950">{block.title}</h2>
      {accounts.length > 0 && (
        <ul className="mt-4 list-disc space-y-1 pl-5 text-slate-700">
          {accounts.map(({ id, account }) => (
            <li key={id}>{account}</li>
          ))}
        </ul>
      )}
      <p className="mt-4 text-slate-500">Stats coming soon</p>
    </section>
  );
}
