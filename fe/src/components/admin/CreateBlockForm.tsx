"use client";

import { useMemo, useState } from "react";
import { blockTypes, getBlockSchema, schemaTemplate } from "@/lib/block-schemas";
import { SchemaForm } from "./SchemaForm";

type Props = {
  existingTypes: readonly string[];
  onCreate: (payload: {
    type: (typeof blockTypes)[number];
    title: string;
    visibility: string;
    props: Record<string, unknown>;
  }) => Promise<boolean>;
};

export { blockTypes };

export function CreateBlockForm({ existingTypes, onCreate }: Props) {
  const visibleBlockTypes = useMemo(
    () => blockTypes.filter((option) => option !== "profile" || !existingTypes.includes(option)),
    [existingTypes],
  );
  const [type, setType] = useState<(typeof blockTypes)[number]>("profile");
  const [title, setTitle] = useState("");
  const [visibility, setVisibility] = useState("admin");
  const [props, setProps] = useState<Record<string, unknown>>(schemaTemplate(getBlockSchema("profile").props));
  const effectiveType = visibleBlockTypes.includes(type) ? type : visibleBlockTypes[0] ?? type;
  const effectiveProps = effectiveType === type
    ? props
    : schemaTemplate(getBlockSchema(effectiveType).props);

  function changeType(nextType: (typeof blockTypes)[number]) {
    setType(nextType);
    setProps(schemaTemplate(getBlockSchema(nextType).props));
  }

  return (
    <div className="pixel-box border-accent bg-surface p-4 text-text">
      <h2 className="font-pixel text-xl text-accent">Create block</h2>
      <div className="mt-4">
        <label className="block text-sm text-muted">
          Type
          <select className="mt-1 w-full border-2 border-muted bg-bg p-2 text-text" value={effectiveType} onChange={(event) => changeType(event.target.value as (typeof blockTypes)[number])}>
            {visibleBlockTypes.map((option) => <option key={option} value={option}>{option}</option>)}
          </select>
        </label>
      </div>
      <div className="mt-3">
        <label className="block text-sm text-muted">
          Title
          <input className="mt-1 w-full border-2 border-muted bg-bg p-2 text-text" value={title} onChange={(event) => setTitle(event.target.value)} required />
        </label>
      </div>
      <SchemaForm
        key={effectiveType}
        fields={getBlockSchema(effectiveType).props}
        initialValue={effectiveProps}
        submitLabel="Create"
        onSubmit={async (nextProps) => {
          const created = await onCreate({ type: effectiveType, title, visibility, props: nextProps });
          if (created) {
            setTitle("");
            setProps(schemaTemplate(getBlockSchema(effectiveType).props));
          }
          return created;
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
      </SchemaForm>
    </div>
  );
}
