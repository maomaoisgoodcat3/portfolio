"use client";

import { useState } from "react";
import type { Block } from "@/lib/api";
import { str } from "@/lib/fields";

type Props = { block: Block; variant?: "sidebar" | "main" };

export function ContactBlock({ block, variant = "main" }: Props) {
  const content = str(block.props, "content");
  const [revealed, setRevealed] = useState(false);

  return (
    <section className={`pixel-box bg-surface text-text ${variant === "sidebar" ? "p-4" : "p-6"}`}>
      <h2 className="font-pixel text-2xl text-accent">{block.title}</h2>
      <button type="button" className="pixel-button mt-3 border-accent px-3 py-2 text-accent" onClick={() => setRevealed((current) => !current)}>
        {revealed ? "Hide" : "Reveal"}
      </button>
      {revealed && content && <p className="mt-2 whitespace-pre-line leading-7">{content}</p>}
    </section>
  );
}
