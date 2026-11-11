"use client";

import { useState } from "react";
import type { Block } from "@/lib/api";
import { str } from "@/lib/fields";

type Props = { block: Block; variant?: "sidebar" | "main" };

export function ContactBlock({ block, variant = "main" }: Props) {
  const content = str(block.props, "content");
  const [revealed, setRevealed] = useState(false);

  return (
    <section id="contact" className={`pixel-box min-w-0 bg-surface text-text ${variant === "sidebar" ? "p-2" : "p-6"}`}>
      <h2 className={`${variant === "sidebar" ? "text-base" : "text-2xl"} font-pixel text-accent`}>{block.title}</h2>
      <div className={`${variant === "sidebar" ? "mt-2" : "mt-3"} flex min-w-0 flex-wrap items-center gap-2`}>
        <button type="button" className="pixel-button min-h-11 shrink-0 border-accent px-3 py-2 text-accent" onClick={() => setRevealed((current) => !current)}>
          {revealed ? "Hide" : "Reveal"}
        </button>
        {revealed && content && <p className="min-w-0 flex-1 overflow-wrap-anywhere whitespace-pre-line leading-7">{content}</p>}
      </div>
    </section>
  );
}
