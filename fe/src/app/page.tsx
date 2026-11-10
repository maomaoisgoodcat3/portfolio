"use client";

import { useEffect, useState } from "react";
import type { Block } from "@/lib/api";
import { apiGet } from "@/lib/api";
import { AboutBlock } from "@/components/blocks/AboutBlock";
import { ContactBlock } from "@/components/blocks/ContactBlock";
import { EntryListBlock } from "@/components/blocks/EntryListBlock";
import { LinksBlock } from "@/components/blocks/LinksBlock";
import { ProfileBlock } from "@/components/blocks/ProfileBlock";
import { SkillsBlock } from "@/components/blocks/SkillsBlock";
import { StatsBlock } from "@/components/blocks/StatsBlock";

function renderBlock(block: Block) {
  switch (block.type) {
    case "profile":
      return <ProfileBlock key={block.id} block={block} />;
    case "about":
      return <AboutBlock key={block.id} block={block} />;
    case "skills":
      return <SkillsBlock key={block.id} block={block} />;
    case "experience":
    case "projects":
    case "research":
      return <EntryListBlock key={block.id} block={block} />;
    case "links":
      return <LinksBlock key={block.id} block={block} />;
    case "stats":
      return <StatsBlock key={block.id} block={block} />;
    case "contact":
      return <ContactBlock key={block.id} block={block} />;
    default:
      return null;
  }
}

export default function Home() {
  const [blocks, setBlocks] = useState<Block[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    apiGet<Block[]>("/api/public/blocks")
      .then((result) => {
        if (active) setBlocks(result ?? []);
      })
      .catch(() => {
        if (active) setError("Unable to load portfolio content.");
      });

    return () => {
      active = false;
    };
  }, []);

  return (
    <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-10 px-6 py-12 sm:px-8">
      {error && <p className="pixel-box border-danger bg-surface p-4 text-danger">{error}</p>}
      {!error && blocks === null && <p className="text-muted">Loading portfolio...</p>}
      {blocks && blocks.length > 0 && <div className="space-y-10">{blocks.map(renderBlock)}</div>}
      {blocks && blocks.length === 0 && <p className="text-muted">No portfolio content yet.</p>}
    </main>
  );
}
