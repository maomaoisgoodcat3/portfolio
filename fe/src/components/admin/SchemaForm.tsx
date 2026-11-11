"use client";

import { FormEvent, useState, type ReactNode } from "react";
import { safeHref } from "@/lib/safe-url";
import type { SchemaField } from "@/lib/block-schemas";

type Props = {
  fields: SchemaField[];
  initialValue: Record<string, unknown>;
  submitLabel: string;
  onSubmit: (value: Record<string, unknown>) => Promise<boolean | void>;
  children?: ReactNode;
};

function tagsToText(value: unknown): string {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string").join(", ") : "";
}

function tagsFromText(value: string): string[] {
  return [...new Set(value.split(",").map((item) => item.trim()).filter(Boolean))];
}

function fieldValue(field: SchemaField, value: Record<string, unknown>): string {
  if (field.kind === "tags") return tagsToText(value[field.key]);
  const fieldValue = value[field.key];
  return typeof fieldValue === "string" ? fieldValue : "";
}

export function SchemaForm({ fields, initialValue, submitLabel, onSubmit, children }: Props) {
  const [values, setValues] = useState<Record<string, string>>(() =>
    Object.fromEntries(fields.map((field) => [field.key, fieldValue(field, initialValue)])),
  );
  const [advanced, setAdvanced] = useState(false);
  const [jsonText, setJsonText] = useState(() => JSON.stringify(initialValue, null, 2));
  const [error, setError] = useState<string | null>(() => null);

  function updateField(key: string, value: string) {
    setValues((current) => ({ ...current, [key]: value }));
  }

  function currentSchemaValue(): Record<string, unknown> {
    const next = { ...initialValue };
    for (const field of fields) {
      const raw = values[field.key] ?? "";
      if (field.kind === "select") {
        next[field.key] = raw || field.options?.[0] || "";
      } else if (!raw.trim()) {
        delete next[field.key];
      } else if (field.kind === "tags") {
        next[field.key] = tagsFromText(raw);
      } else {
        next[field.key] = raw.trim();
      }
    }
    return next;
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      if (advanced) {
        const parsed = JSON.parse(jsonText) as unknown;
        if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
          setError("Must be a JSON object");
          return;
        }
        setError(null);
        await onSubmit(parsed as Record<string, unknown>);
        return;
      }

      const next = { ...initialValue };
      for (const field of fields) {
        const raw = values[field.key] ?? "";
        if (field.required && !raw.trim()) {
          setError(`${field.label} is required`);
          return;
        }
        if (field.kind === "select") {
          next[field.key] = raw || field.options?.[0] || "";
          continue;
        }
        if (!raw.trim()) {
          delete next[field.key];
          continue;
        }
        if (field.kind === "tags") {
          next[field.key] = tagsFromText(raw);
          continue;
        }
        const href = field.kind === "url" || field.kind === "https_url" ? safeHref(raw.trim()) : null;
        if (field.kind === "url" && !href) {
          setError("Use a valid http:// or https:// URL");
          return;
        }
        if (field.kind === "https_url" && (!href || !href.startsWith("https://")) ) {
          setError("Use an https:// image URL");
          return;
        }
        next[field.key] = raw.trim();
      }
      setError(null);
      await onSubmit(next);
    } catch (caught) {
      setError(caught instanceof SyntaxError ? caught.message : "Unable to save.");
    }
  }

  return (
    <form className="space-y-3" onSubmit={submit}>
      {fields.map((field) => (
        <label className="block text-sm text-muted" key={field.key}>
          {field.label}
          {field.kind === "select" ? (
            <select
              className="mt-1 w-full border-2 border-muted bg-bg p-2 text-text"
              value={values[field.key] ?? field.options?.[0] ?? ""}
              onChange={(event) => updateField(field.key, event.target.value)}
            >
              {(field.options ?? []).map((option) => <option key={option} value={option}>{option}</option>)}
            </select>
          ) : field.kind === "textarea" ? (
            <textarea className="mt-1 min-h-24 w-full border-2 border-muted bg-bg p-2 text-text" value={values[field.key] ?? ""} onChange={(event) => updateField(field.key, event.target.value)} />
          ) : (
            <input
              className="mt-1 w-full border-2 border-muted bg-bg p-2 text-text"
              type={field.kind === "url" || field.kind === "https_url" ? "url" : "text"}
              required={field.required}
              value={values[field.key] ?? ""}
              onChange={(event) => updateField(field.key, event.target.value)}
            />
          )}
          {field.kind === "tags" && <span className="mt-1 block text-xs text-muted">Comma-separated values</span>}
        </label>
      ))}
      {children}
      <button type="button" className="text-sm text-accent underline" onClick={() => {
        if (!advanced) setJsonText(JSON.stringify(currentSchemaValue(), null, 2));
        setAdvanced((current) => !current);
      }}>
        {advanced ? "Use schema fields" : "Advanced: edit JSON"}
      </button>
      {advanced && (
        <label className="block text-sm text-muted">
          JSON
          <textarea className="mt-1 min-h-32 w-full border-2 border-muted bg-bg p-2 font-mono text-sm text-text" value={jsonText} onChange={(event) => setJsonText(event.target.value)} />
        </label>
      )}
      {error && <p className="text-sm text-danger">{error}</p>}
      <button className="pixel-button border-ok bg-ok px-3 py-2 text-bg">{submitLabel}</button>
    </form>
  );
}
