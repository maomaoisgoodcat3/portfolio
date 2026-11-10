"use client";

import { useState } from "react";
import type { BlockItem } from "@/lib/api";
import { getBlockSchema } from "@/lib/block-schemas";
import { SchemaForm } from "./SchemaForm";

type Props = {
  blockType: string;
  item: BlockItem;
  onUpdate: (id: string, payload: { data?: Record<string, unknown>; visibility?: string }) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
};

export function ItemEditor({ blockType, item, onUpdate, onDelete }: Props) {
  const [editing, setEditing] = useState(false);
  const [visibility, setVisibility] = useState(item.visibility);
  const fields = getBlockSchema(blockType).items;

  if (!editing) {
    return (
      <div className="flex items-center justify-between gap-3 border-t-2 border-muted py-3 text-sm">
        <span className="text-muted">Item {item.position}</span>
        <div className="flex gap-2">
          <button type="button" className="pixel-button border-accent px-2 py-1 text-accent" onClick={() => setEditing(true)}>Edit</button>
          <button type="button" className="pixel-button border-danger px-2 py-1 text-danger" onClick={() => window.confirm("Delete this item?") && void onDelete(item.id)}>Delete</button>
        </div>
      </div>
    );
  }

  return (
    <div className="border-t-2 border-muted py-3">
      <SchemaForm
        fields={fields}
        initialValue={item.data}
        submitLabel="Save item"
        onSubmit={async (data) => {
          await onUpdate(item.id, { data, visibility });
          setEditing(false);
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
        <div className="flex gap-2">
          <button type="button" className="pixel-button border-muted px-3 py-2 text-muted" onClick={() => setEditing(false)}>Cancel</button>
          <button type="button" className="pixel-button border-danger px-3 py-2 text-danger" onClick={() => window.confirm("Delete this item?") && void onDelete(item.id)}>Delete</button>
        </div>
      </SchemaForm>
    </div>
  );
}
