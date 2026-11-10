import { FormEvent, useEffect, useState } from "react";
import type { Block } from "@/lib/api";
import { ItemEditor } from "./ItemEditor";

type Props = {
  block: Block;
  onUpdate: (id: string, payload: { title?: string; visibility?: string; props?: Record<string, unknown> }) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
  onAddItem: (blockId: string, payload: { data: Record<string, unknown>; visibility: string }) => Promise<boolean>;
  onUpdateItem: (id: string, payload: { data?: Record<string, unknown>; visibility?: string }) => Promise<void>;
  onDeleteItem: (id: string) => Promise<void>;
};

export function BlockEditor({ block, onUpdate, onDelete, onAddItem, onUpdateItem, onDeleteItem }: Props) {
  const [title, setTitle] = useState(block.title);
  const [visibility, setVisibility] = useState(block.visibility);
  const [propsText, setPropsText] = useState(JSON.stringify(block.props, null, 2));
  const [itemData, setItemData] = useState("{}");
  const [itemVisibility, setItemVisibility] = useState("public");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setTitle(block.title);
    setVisibility(block.visibility);
    setPropsText(JSON.stringify(block.props, null, 2));
  }, [block]);

  async function saveBlock(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      const props = JSON.parse(propsText) as unknown;
      if (typeof props !== "object" || props === null || Array.isArray(props)) {
        setError("Must be a JSON object");
        return;
      }
      setError(null);
      await onUpdate(block.id, { title, visibility, props: props as Record<string, unknown> });
    } catch (caught) {
      setError(caught instanceof SyntaxError ? caught.message : "Unable to update block.");
    }
  }

  async function addItem(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      const data = JSON.parse(itemData) as unknown;
      if (typeof data !== "object" || data === null || Array.isArray(data)) {
        setError("Must be a JSON object");
        return;
      }
      setError(null);
      const added = await onAddItem(block.id, { data: data as Record<string, unknown>, visibility: itemVisibility });
      if (added) setItemData("{}");
    } catch (caught) {
      setError(caught instanceof SyntaxError ? caught.message : "Unable to add item.");
    }
  }

  return (
    <article className="rounded-lg border border-slate-200 bg-white p-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="font-semibold text-slate-950">{block.type}</h2>
          <p className="text-sm text-slate-500">Position {block.position}</p>
        </div>
        <button className="text-sm text-red-700" onClick={() => window.confirm("Delete this block?") && void onDelete(block.id)}>Delete block</button>
      </div>
      <form className="mt-4 space-y-3" onSubmit={saveBlock}>
        <input className="w-full rounded border border-slate-300 p-2" value={title} onChange={(event) => setTitle(event.target.value)} required />
        <select className="rounded border border-slate-300 p-2" value={visibility} onChange={(event) => setVisibility(event.target.value)}>
          <option value="public">public</option>
          <option value="admin">admin</option>
        </select>
        <textarea className="min-h-28 w-full rounded border border-slate-300 p-2 font-mono text-sm" value={propsText} onChange={(event) => setPropsText(event.target.value)} aria-label="Block props JSON" />
        <button className="rounded bg-slate-800 px-3 py-2 text-sm text-white">Save block</button>
      </form>
      {error && <p className="mt-2 text-sm text-red-700">{error}</p>}
      <div className="mt-6 space-y-3">
        <h3 className="font-medium">Items</h3>
        {block.items.map((item) => <ItemEditor key={item.id} item={item} onUpdate={onUpdateItem} onDelete={onDeleteItem} />)}
        <form className="space-y-2 border-t border-slate-200 pt-3" onSubmit={addItem}>
          <textarea className="min-h-20 w-full rounded border border-slate-300 p-2 font-mono text-sm" value={itemData} onChange={(event) => setItemData(event.target.value)} aria-label="New item data JSON" />
          <div className="flex gap-2">
            <select className="rounded border border-slate-300 p-2" value={itemVisibility} onChange={(event) => setItemVisibility(event.target.value)}>
              <option value="public">public</option>
              <option value="admin">admin</option>
            </select>
            <button className="rounded border border-slate-400 px-3 py-2 text-sm">Add item</button>
          </div>
        </form>
      </div>
    </article>
  );
}
