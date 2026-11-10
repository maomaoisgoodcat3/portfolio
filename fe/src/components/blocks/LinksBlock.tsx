import type { Block } from "@/lib/api";
import { str } from "@/lib/fields";
import { safeHref } from "@/lib/safe-url";

type Props = { block: Block };

export function LinksBlock({ block }: Props) {
  return (
    <section>
      <h2 className="text-2xl font-semibold text-slate-950">{block.title}</h2>
      <ul className="mt-4 space-y-2">
        {block.items.map((item) => {
          const label = str(item.data, "label");
          const href = safeHref(str(item.data, "url"));
          if (!label || !href) return null;
          return (
            <li key={item.id}>
              <a className="text-blue-700 underline" href={href}>
                {label}
              </a>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
