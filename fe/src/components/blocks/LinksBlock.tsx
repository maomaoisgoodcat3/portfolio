import type { Block } from "@/lib/api";
import { str } from "@/lib/fields";
import { safeHref } from "@/lib/safe-url";

type Props = { block: Block };

export function LinksBlock({ block }: Props) {
  return (
    <section className="pixel-box bg-surface p-6 text-text">
      <h2 className="font-pixel text-2xl text-accent">{block.title}</h2>
      <ul className="mt-4 space-y-2">
        {block.items.map((item) => {
          const label = str(item.data, "label");
          const href = safeHref(str(item.data, "url"));
          if (!label || !href) return null;
          return (
            <li key={item.id}>
              <a className="text-accent underline" href={href}>
                {label}
              </a>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
