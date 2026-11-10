import type { Block } from "@/lib/api";
import { str } from "@/lib/fields";
import { safeHref } from "@/lib/safe-url";

type Props = { block: Block; variant?: "sidebar" | "main" };

export function LinksBlock({ block, variant = "main" }: Props) {
  const href = safeHref(str(block.props, "url"));
  if (!href) return null;

  return (
    <section className={variant === "sidebar" ? "min-w-0" : "pixel-box bg-surface p-6 text-text"}>
      {variant !== "sidebar" && <h2 className="font-pixel text-2xl text-accent">{block.title}</h2>}
      <a className={variant === "sidebar" ? "pixel-button block min-h-11 w-full min-w-0 overflow-wrap-anywhere border-accent px-3 py-2 text-center text-accent" : "mt-3 inline-block text-accent underline"} href={href}>
        {block.title}
      </a>
    </section>
  );
}
