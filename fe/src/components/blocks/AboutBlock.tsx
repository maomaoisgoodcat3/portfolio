import type { Block } from "@/lib/api";
import { str } from "@/lib/fields";

type Props = { block: Block };

export function AboutBlock({ block }: Props) {
  const content = str(block.props, "content");

  return (
    <article className="pixel-box bg-surface p-4 text-text">
      <h3 className="font-pixel text-xl text-accent">{block.title}</h3>
      {content && <p className="mt-2 whitespace-pre-line leading-7">{content}</p>}
    </article>
  );
}
