import type { Block } from "@/lib/api";
import { str } from "@/lib/fields";

type Props = { block: Block };

export function SkillsBlock({ block }: Props) {
  return (
    <section>
      <h2 className="text-2xl font-semibold text-slate-950">{block.title}</h2>
      <ul className="mt-4 grid gap-3 sm:grid-cols-2">
        {block.items.map((item) => {
          const name = str(item.data, "name");
          const level = str(item.data, "level");
          if (!name && !level) return null;
          return (
            <li key={item.id} className="rounded-lg border border-slate-200 bg-white p-4">
              {name && <span className="font-medium text-slate-900">{name}</span>}
              {level && <span className="ml-2 text-sm text-slate-500">{level}</span>}
            </li>
          );
        })}
      </ul>
    </section>
  );
}
