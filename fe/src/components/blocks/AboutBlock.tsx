import type { Block } from "@/lib/api";
import { str } from "@/lib/fields";

type Props = { block: Block };

export function AboutBlock({ block }: Props) {
  const text = str(block.props, "text");

  return (
    <section className="pixel-box bg-surface p-6 text-text">
      <h2 className="font-pixel text-2xl text-accent">{block.title}</h2>
      {text && <p className="mt-3 whitespace-pre-wrap leading-7">{text}</p>}
    </section>
  );
}
