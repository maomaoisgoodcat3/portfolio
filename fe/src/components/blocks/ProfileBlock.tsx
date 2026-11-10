import type { Block } from "@/lib/api";
import { str } from "@/lib/fields";

type Props = { block: Block };

export function ProfileBlock({ block }: Props) {
  const name = str(block.props, "name");
  const headline = str(block.props, "headline");
  const location = str(block.props, "location");

  return (
    <section>
      <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">{block.title}</h2>
      {name && <h1 className="mt-2 text-4xl font-bold tracking-tight text-slate-950">{name}</h1>}
      {headline && <p className="mt-3 text-xl text-slate-700">{headline}</p>}
      {location && <p className="mt-2 text-slate-500">{location}</p>}
    </section>
  );
}
