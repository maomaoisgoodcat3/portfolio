import { useState, type ComponentProps } from "react";
import type { Block } from "@/lib/api";
import { BlockEditor } from "./BlockEditor";

type Props = {
  blocks: Block[];
  onUpdate: ComponentProps<typeof BlockEditor>["onUpdate"];
  onDelete: (id: string) => Promise<void>;
  onAddItem: ComponentProps<typeof BlockEditor>["onAddItem"];
  onUpdateItem: ComponentProps<typeof BlockEditor>["onUpdateItem"];
  onDeleteItem: ComponentProps<typeof BlockEditor>["onDeleteItem"];
  onMove: (id: string, direction: -1 | 1) => Promise<void>;
};

export function BlockList({ blocks, onUpdate, onDelete, onAddItem, onUpdateItem, onDeleteItem, onMove }: Props) {
  const [editingId, setEditingId] = useState<string | null>(null);

  return (
    <div className="space-y-6">
      {blocks.map((block, index) => (
        <article className="pixel-box border-muted bg-surface p-4 text-text" key={block.id}>
          <header className="flex flex-wrap items-center gap-2">
            <span className="font-pixel text-accent">{block.type}</span>
            <span className={`border px-2 py-1 text-xs ${block.visibility === "public" ? "border-ok text-ok" : "border-warn text-warn"}`}>
              {block.visibility.toUpperCase()}
            </span>
            <button type="button" className="pixel-button border-muted px-2 py-1 text-muted" disabled={index === 0} onClick={() => void onMove(block.id, -1)}>Up</button>
            <button type="button" className="pixel-button border-muted px-2 py-1 text-muted" disabled={index === blocks.length - 1} onClick={() => void onMove(block.id, 1)}>Down</button>
            <button type="button" className="pixel-button border-accent px-2 py-1 text-accent" onClick={() => setEditingId(editingId === block.id ? null : block.id)}>Edit</button>
            <button type="button" className="pixel-button border-danger px-2 py-1 text-danger" onClick={() => window.confirm("Delete this block?") && void onDelete(block.id)}>Delete</button>
          </header>
          <div className="mt-4">
            <BlockEditor block={block} editing={editingId === block.id} onEdit={() => setEditingId(null)} onUpdate={onUpdate} onAddItem={onAddItem} onUpdateItem={onUpdateItem} onDeleteItem={onDeleteItem} />
          </div>
        </article>
      ))}
    </div>
  );
}
