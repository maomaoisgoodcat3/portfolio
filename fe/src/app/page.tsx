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
import { CazungWidget } from "@/components/cazung/CazungWidget";

function renderBlock(block: Block, variant: "sidebar" | "main" = "main") {
  switch (block.type) {
    case "profile":
      return <ProfileBlock key={block.id} block={block} variant={variant} />;
    case "about":
      return <AboutBlock key={block.id} block={block} />;
    case "skills":
      return <SkillsBlock key={block.id} block={block} />;
    case "experience":
    case "projects":
    case "research":
      return <EntryListBlock key={block.id} block={block} />;
    case "links":
      return <LinksBlock key={block.id} block={block} variant={variant} />;
    case "stats":
      return <StatsBlock key={block.id} block={block} />;
    case "contact":
      return <ContactBlock key={block.id} block={block} variant={variant} />;
    default:
      return null;
  }
}

const mainGroupTypes = ["about", "experience", "projects", "research", "skills", "stats"] as const;
const mainGroupLabels: Record<(typeof mainGroupTypes)[number], string> = {
  about: "About",
  experience: "Experience",
  projects: "Projects",
  research: "Research",
  skills: "Skills",
  stats: "Stats",
};

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

  const orderedBlocks = blocks ? [...blocks].sort((a, b) => a.position - b.position) : [];
  const profile = orderedBlocks.find((block) => block.type === "profile");
  const links = orderedBlocks.filter((block) => block.type === "links");
  const contacts = orderedBlocks.filter((block) => block.type === "contact");
  const hasProfile = profile !== undefined;
  const hasLinksOrContacts = links.length > 0 || contacts.length > 0;
  const hasSidebar = hasProfile || hasLinksOrContacts;

  return (
    <div className="min-h-screen bg-bg">
      {hasSidebar && (
        <aside className="w-full bg-bg lg:fixed lg:inset-y-0 lg:top-0 lg:left-0 lg:z-20 lg:flex lg:h-screen lg:w-1/4 lg:flex-col">
          <div className={`lg:grid lg:h-screen ${hasProfile && hasLinksOrContacts ? "lg:grid-rows-2" : "lg:grid-rows-1"} lg:gap-3 lg:p-4`}>
            {hasProfile && (
              <div className="min-h-0">
                {profile && renderBlock(profile, "sidebar")}
              </div>
            )}
            {hasLinksOrContacts && (
              <div className="pixel-box min-h-0 bg-surface p-2 text-text lg:p-3">
                <div className="pixel-scroll min-h-0 overflow-visible overflow-x-hidden lg:h-full lg:overflow-y-auto">
                  <div className="grid grid-cols-2 gap-2 lg:grid-cols-1">
                    {links.map((block) => renderBlock(block, "sidebar"))}
                  </div>
                  <div className="mt-2 space-y-2">
                    {contacts.map((block) => renderBlock(block, "sidebar"))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </aside>
      )}
      <main className={`w-full overflow-wrap-anywhere px-4 py-4 sm:px-8 sm:py-12 ${hasSidebar ? "lg:ml-[25%] lg:w-[75%]" : ""}`}>
        <div className="mx-auto flex w-full max-w-3xl flex-col gap-10">
          {error && <p className="pixel-box border-danger bg-surface p-4 text-danger">{error}</p>}
          {!error && blocks === null && <p className="text-muted">Loading portfolio...</p>}
          {blocks && (
            <div className="space-y-8">
              {mainGroupTypes.map((type) => {
                const group = orderedBlocks.filter((block) => block.type === type);
                if (group.length === 0) return null;
                return (
                  <section key={type} className="space-y-4">
                    <h2 className="font-pixel text-2xl text-accent">{mainGroupLabels[type]}</h2>
                    <div className="space-y-4">{group.map((block) => renderBlock(block))}</div>
                  </section>
                );
              })}
            </div>
          )}
          {blocks && blocks.length === 0 && <p className="text-muted">No portfolio content yet.</p>}
        </div>
      </main>
      <CazungWidget />
    </div>
  );
}
