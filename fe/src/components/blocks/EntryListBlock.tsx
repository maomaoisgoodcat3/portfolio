import type { Block } from "@/lib/api";
import { str, strList } from "@/lib/fields";
import { safeHref } from "@/lib/safe-url";

type Props = { block: Block };

export function EntryListBlock({ block }: Props) {
  const subtitle = str(block.props, "subtitle");
  const period = str(block.props, "period");
  const content = str(block.props, "content");
  const href = safeHref(str(block.props, "url"));
  const tags = strList(block.props, "tags");

  return (
    <article className="pixel-box w-full bg-surface p-4 text-text">
      <h3 className="font-pixel text-xl text-accent">{block.title}</h3>
      {(subtitle || period) && <p className="mt-1 text-sm text-muted">{[subtitle, period].filter(Boolean).join(" · ")}</p>}
      {content && <p className="mt-2 whitespace-pre-line leading-7">{content}</p>}
      {href && <a className="mt-2 inline-block text-accent underline" href={href}>Open link</a>}
      {tags.length > 0 && (
        <ul className="mt-2 flex flex-wrap gap-2">
          {tags.map((tag) => <li key={tag} className="border border-accent px-2 py-1 text-xs text-accent">{tag}</li>)}
        </ul>
      )}
    </article>
  );
}
