"use client";

import { useState } from "react";
import type { Block } from "@/lib/api";
import { getBlockSchema, schemaTemplate } from "@/lib/block-schemas";
import { SchemaForm } from "./SchemaForm";
import { ItemEditor } from "./ItemEditor";

type Props = {
  block: Block;
  editing: boolean;
  onEdit: () => void;
  onUpdate: (id: string, payload: { title?: string; visibility?: string; props?: Record<string, unknown> }) => Promise<void>;
  onAddItem: (blockId: string, payload: { data: Record<string, unknown>; visibility: string }) => Promise<boolean>;
  onUpdateItem: (id: string, payload: { data?: Record<string, unknown>; visibility?: string }) => Promise<void>;
  onDeleteItem: (id: string) => Promise<void>;
};

export function BlockEditor({ block, editing, onEdit, onUpdate, onAddItem, onUpdateItem, onDeleteItem }: Props) {
  const [title, setTitle] = useState(block.title);
  const [visibility, setVisibility] = useState(block.visibility);
  const [addingItem, setAddingItem] = useState(false);
  const [itemVisibility, setItemVisibility] = useState("admin");
  const [itemFormKey, setItemFormKey] = useState(0);
  const schema = getBlockSchema(block.type);
  const [newItemData] = useState<Record<string, unknown>>(() => schemaTemplate(schema.items));

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
      <div className="mt-6">
        <h3 className="font-pixel text-lg text-accent">Items</h3>
        <div className="mt-2">
          {block.items.map((item) => (
            <ItemEditor key={item.id} blockType={block.type} item={item} onUpdate={onUpdateItem} onDelete={onDeleteItem} />
          ))}
        </div>
        {schema.items.length > 0 && editing && !addingItem && (
          <button type="button" className="pixel-button mt-3 border-accent px-3 py-2 text-accent" onClick={() => setAddingItem(true)}>Add item</button>
        )}
        {addingItem && editing && (
          <div className="mt-3 border-t-2 border-muted pt-3">
            <SchemaForm
              key={itemFormKey}
              fields={schema.items}
              initialValue={newItemData}
              submitLabel="Add item"
              onSubmit={async (data) => {
                const added = await onAddItem(block.id, { data, visibility: itemVisibility });
                if (added) {
                  setAddingItem(false);
                  setItemFormKey((current) => current + 1);
                }
                return added;
              }}
            >
              <label className="block text-sm text-muted">
                Visibility
                <select className="mt-1 w-full border-2 border-muted bg-bg p-2 text-text" value={itemVisibility} onChange={(event) => setItemVisibility(event.target.value)}>
                  <option value="admin">admin</option>
                  <option value="public">public</option>
                </select>
                <span className="mt-1 block text-xs text-muted">Admin = hidden on the public site</span>
              </label>
              <button type="button" className="pixel-button border-muted px-3 py-2 text-muted" onClick={() => setAddingItem(false)}>Cancel</button>
            </SchemaForm>
          </div>
        )}
      </div>
    </article>
  );
}
