import type { Block } from "@/lib/api";
import { str } from "@/lib/fields";
import { safeHref } from "@/lib/safe-url";

type Props = { block: Block };

export function ProfileBlock({ block }: Props) {
  const name = str(block.props, "name");
  const headline = str(block.props, "headline");
  const location = str(block.props, "location");
  const avatar = safeHref(str(block.props, "avatar_url"));
  const avatarHref = avatar?.startsWith("https:") ? avatar : null;

  return (
    <section className="pixel-box bg-surface p-6 text-text">
      <h2 className="font-pixel text-xl text-accent">{block.title}</h2>
      <div className="mt-3 flex flex-wrap items-center gap-5">
        {avatarHref && (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={avatarHref} alt={name ?? ""} width={96} height={96} referrerPolicy="no-referrer" loading="lazy" className="border-2 border-accent object-cover" />
        )}
        <div>
          {name && <h1 className="font-pixel text-4xl tracking-tight">{name}</h1>}
          {headline && <p className="mt-3 text-xl">{headline}</p>}
          {location && <p className="mt-2 text-muted">{location}</p>}
        </div>
      </div>
    </section>
  );
}
