import { FormEvent, useState } from "react";

export const blockTypes = [
  "profile",
  "about",
  "skills",
  "experience",
  "projects",
  "research",
  "links",
  "stats",
  "contact",
] as const;

type Props = {
  onCreate: (payload: { type: (typeof blockTypes)[number]; title: string; visibility: string; props: Record<string, unknown> }) => Promise<boolean>;
};

export function CreateBlockForm({ onCreate }: Props) {
  const [type, setType] = useState<(typeof blockTypes)[number]>("profile");
  const [title, setTitle] = useState("");
  const [visibility, setVisibility] = useState("public");
  const [propsText, setPropsText] = useState("{}");
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      const props = JSON.parse(propsText) as unknown;
      if (typeof props !== "object" || props === null || Array.isArray(props)) {
        setError("Must be a JSON object");
        return;
      }
      setError(null);
      const created = await onCreate({ type, title, visibility, props: props as Record<string, unknown> });
      if (created) {
        setTitle("");
        setPropsText("{}");
      }
    } catch (caught) {
      setError(caught instanceof SyntaxError ? caught.message : "Unable to create block.");
    }
  }

  return (
    <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-4" onSubmit={submit}>
      <h2 className="text-lg font-semibold">Create block</h2>
      <div className="grid gap-3 sm:grid-cols-3">
        <select className="rounded border border-slate-300 p-2" value={type} onChange={(event) => setType(event.target.value as (typeof blockTypes)[number])}>
          {blockTypes.map((option) => <option key={option}>{option}</option>)}
        </select>
        <input className="rounded border border-slate-300 p-2" placeholder="Title" value={title} onChange={(event) => setTitle(event.target.value)} required />
        <select className="rounded border border-slate-300 p-2" value={visibility} onChange={(event) => setVisibility(event.target.value)}>
          <option value="public">public</option>
          <option value="admin">admin</option>
        </select>
      </div>
      <textarea className="min-h-24 w-full rounded border border-slate-300 p-2 font-mono text-sm" value={propsText} onChange={(event) => setPropsText(event.target.value)} aria-label="Block props JSON" />
      {error && <p className="text-sm text-red-700">{error}</p>}
      <button className="rounded bg-slate-900 px-3 py-2 text-white">Create</button>
    </form>
  );
}
