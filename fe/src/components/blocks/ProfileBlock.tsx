import type { Block } from "@/lib/api";
import { str } from "@/lib/fields";
import { safeHref } from "@/lib/safe-url";

type Props = { block: Block; variant?: "sidebar" | "main" };

export function ProfileBlock({ block, variant = "main" }: Props) {
  const name = str(block.props, "name");
  const headline = str(block.props, "headline");
  const location = str(block.props, "location");
  const avatar = safeHref(str(block.props, "avatar_url"));
  const avatarHref = avatar?.startsWith("https:") ? avatar : null;

  return (
    <section className={`pixel-box h-full bg-surface text-text ${variant === "sidebar" ? "flex flex-col items-center justify-center p-4 text-center" : "p-6"}`}>
      {variant !== "sidebar" && <h2 className="font-pixel text-xl text-accent">{block.title}</h2>}
      <div className={`mt-3 flex gap-5 ${variant === "sidebar" ? "flex-col items-center justify-center" : "flex-wrap items-center"}`}>
        {avatarHref && (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={avatarHref} alt={name ?? ""} width={96} height={96} referrerPolicy="no-referrer" loading="lazy" className={`border-2 border-accent object-cover ${variant === "sidebar" ? "h-24 w-24 lg:h-32 lg:w-32" : "h-24 w-24"}`} />
        )}
        <div className={variant === "sidebar" ? "text-center" : undefined}>
          {name && <h1 className="font-pixel text-4xl tracking-tight">{name}</h1>}
          {headline && <p className="mt-3 text-xl">{headline}</p>}
          {location && <p className="mt-2 text-muted">{location}</p>}
        </div>
      </div>
    </section>
  );
}
