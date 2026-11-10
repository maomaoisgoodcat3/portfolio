import type { Block } from "@/lib/api";
import { str } from "@/lib/fields";

type Props = { block: Block };

export function AboutBlock({ block }: Props) {
  const text = str(block.props, "text");

  return (
    <section>
      <h2 className="text-2xl font-semibold text-slate-950">{block.title}</h2>
      {text && <p className="mt-3 whitespace-pre-wrap leading-7 text-slate-700">{text}</p>}
    </section>
  );
}
