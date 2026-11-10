import type { Block } from "@/lib/api";
import { str, strList } from "@/lib/fields";
import { safeHref } from "@/lib/safe-url";

type Props = { block: Block };

export function EntryListBlock({ block }: Props) {
  return (
    <section>
      <h2 className="text-2xl font-semibold text-slate-950">{block.title}</h2>
      <div className="mt-4 space-y-5">
        {block.items.map((item) => {
          const title = str(item.data, "title");
          const subtitle = str(item.data, "subtitle");
          const period = str(item.data, "period");
          const description = str(item.data, "description");
          const href = safeHref(str(item.data, "url"));
          const tags = strList(item.data, "tags");
          if (!title && !subtitle && !period && !description && !href && tags.length === 0) {
            return null;
          }

          return (
            <article key={item.id} className="border-l-2 border-slate-200 pl-4">
              {title && <h3 className="font-semibold text-slate-900">{title}</h3>}
              {subtitle && <p className="mt-1 text-slate-700">{subtitle}</p>}
              {period && <p className="mt-1 text-sm text-slate-500">{period}</p>}
              {description && <p className="mt-2 whitespace-pre-wrap leading-7 text-slate-700">{description}</p>}
              {href && (
                <a className="mt-2 inline-block text-blue-700 underline" href={href}>
                  Visit link
                </a>
              )}
              {tags.length > 0 && (
                <ul className="mt-3 flex flex-wrap gap-2">
                  {tags.map((tag) => (
                    <li key={tag} className="rounded-full bg-slate-100 px-3 py-1 text-sm text-slate-600">
                      {tag}
                    </li>
                  ))}
                </ul>
              )}
            </article>
          );
        })}
      </div>
    </section>
  );
}
