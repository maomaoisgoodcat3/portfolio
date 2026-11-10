import type { Block } from "@/lib/api";
import { str } from "@/lib/fields";

type Props = { block: Block };

export function SkillsBlock({ block }: Props) {
  return (
    <section className="pixel-box bg-surface p-6 text-text">
      <h2 className="font-pixel text-2xl text-accent">{block.title}</h2>
      <ul className="mt-4 grid gap-3 sm:grid-cols-2">
        {block.items.map((item) => {
          const name = str(item.data, "name");
          const level = str(item.data, "level");
          if (!name && !level) return null;
          return (
            <li key={item.id} className="border-2 border-muted bg-bg p-3">
              {name && <span className="font-medium">{name}</span>}
              {level && <span className="ml-2 text-sm text-muted">{level}</span>}
            </li>
          );
        })}
      </ul>
    </section>
  );
}
