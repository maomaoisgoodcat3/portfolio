"use client";

import { useState } from "react";
import type { Block } from "@/lib/api";
import { getBlockSchema } from "@/lib/block-schemas";
import { SchemaForm } from "./SchemaForm";

type Props = {
  block: Block;
  editing: boolean;
  onEdit: () => void;
  onUpdate: (id: string, payload: { title?: string; visibility?: string; props?: Record<string, unknown> }) => Promise<void>;
};

export function BlockEditor({ block, editing, onEdit, onUpdate }: Props) {
  const [title, setTitle] = useState(block.title);
  const [visibility, setVisibility] = useState(block.visibility);
  const schema = getBlockSchema(block.type);

  return (
    <article className="pixel-box border-muted bg-surface p-4 text-text">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="font-pixel text-xl text-accent">{block.title}</h2>
          <p className="text-sm text-muted">Position {block.position}</p>
        </div>
      </div>
      <div className="mt-4">
        {editing && <label className="block text-sm text-muted">
          Title
          <input className="mt-1 w-full border-2 border-muted bg-bg p-2 text-text" value={title} onChange={(event) => setTitle(event.target.value)} />
        </label>}
      </div>
      {editing && <SchemaForm
          key={`${block.id}-${block.type}`}
          fields={schema.props}
          initialValue={block.props}
          submitLabel="Save block"
          onSubmit={async (props) => {
            await onUpdate(block.id, { title, visibility, props });
            onEdit();
          }}
        >
          <label className="block text-sm text-muted">
            Visibility
            <select className="mt-1 w-full border-2 border-muted bg-bg p-2 text-text" value={visibility} onChange={(event) => setVisibility(event.target.value)}>
              <option value="admin">admin</option>
              <option value="public">public</option>
            </select>
            <span className="mt-1 block text-xs text-muted">Admin = hidden on the public site</span>
          </label>
        </SchemaForm>}
    </article>
  );
}
