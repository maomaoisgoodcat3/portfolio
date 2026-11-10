import { FormEvent, useEffect, useState } from "react";
import type { BlockItem } from "@/lib/api";

type Props = {
  item: BlockItem;
  onUpdate: (id: string, payload: { data?: Record<string, unknown>; visibility?: string }) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
};

export function ItemEditor({ item, onUpdate, onDelete }: Props) {
  const [dataText, setDataText] = useState(JSON.stringify(item.data, null, 2));
  const [visibility, setVisibility] = useState(item.visibility);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setDataText(JSON.stringify(item.data, null, 2));
    setVisibility(item.visibility);
  }, [item]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      const data = JSON.parse(dataText) as unknown;
      if (typeof data !== "object" || data === null || Array.isArray(data)) {
        setError("Must be a JSON object");
        return;
      }
      setError(null);
      await onUpdate(item.id, { data: data as Record<string, unknown>, visibility });
    } catch (caught) {
      setError(caught instanceof SyntaxError ? caught.message : "Unable to update item.");
    }
  }

  return (
    <form className="space-y-2 border-t border-slate-200 pt-3" onSubmit={submit}>
      <textarea className="min-h-20 w-full rounded border border-slate-300 p-2 font-mono text-sm" value={dataText} onChange={(event) => setDataText(event.target.value)} aria-label="Item data JSON" />
      <div className="flex flex-wrap gap-2">
        <select className="rounded border border-slate-300 p-2" value={visibility} onChange={(event) => setVisibility(event.target.value)}>
          <option value="public">public</option>
          <option value="admin">admin</option>
        </select>
        <button className="rounded bg-slate-800 px-3 py-2 text-sm text-white">Save item</button>
        <button type="button" className="rounded border border-red-300 px-3 py-2 text-sm text-red-700" onClick={() => window.confirm("Delete this item?") && void onDelete(item.id)}>Delete</button>
      </div>
      {error && <p className="text-sm text-red-700">{error}</p>}
    </form>
  );
}
