import type { Block } from "@/lib/api";
import { strList } from "@/lib/fields";

type Props = { block: Block };

export function SkillsBlock({ block }: Props) {
  const tags = strList(block.props, "tags");
  return (
    <article className="pixel-box w-full bg-surface p-4 text-text">
      <h3 className="font-pixel text-xl text-accent">{block.title}</h3>
      <ul className="mt-2 flex flex-wrap gap-2">
        {tags.map((tag) => <li key={tag} className="border border-accent px-2 py-1 text-xs text-accent">{tag}</li>)}
      </ul>
    </article>
  );
}
