import type { Block } from "@/lib/api";
import { str } from "@/lib/fields";
import { safeHref } from "@/lib/safe-url";

type Props = { block: Block; variant?: "sidebar" | "main" };

export function LinksBlock({ block, variant = "main" }: Props) {
  const href = safeHref(str(block.props, "url"));
  if (!href) return null;

  return (
    <section className={`pixel-box bg-surface text-text ${variant === "sidebar" ? "p-4" : "p-6"}`}>
      <h2 className="font-pixel text-2xl text-accent">{block.title}</h2>
      <a className={variant === "sidebar" ? "pixel-button mt-3 block w-full border-accent px-3 py-2 text-accent" : "mt-3 inline-block text-accent underline"} href={href}>
        {block.title}
      </a>
    </section>
  );
}
