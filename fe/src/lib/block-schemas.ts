export type FieldKind = "text" | "textarea" | "url" | "https_url" | "tags" | "select";

export type SchemaField = {
  key: string;
  label: string;
  kind: FieldKind;
  options?: string[];
};

export type BlockSchema = {
  props: SchemaField[];
  items: SchemaField[];
};

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

const profileProps: SchemaField[] = [
  { key: "name", label: "Name", kind: "text" },
  { key: "headline", label: "Headline", kind: "text" },
  { key: "location", label: "Location", kind: "text" },
  { key: "avatar_url", label: "Avatar URL", kind: "https_url" },
];

const entryItems: SchemaField[] = [
  { key: "title", label: "Title", kind: "text" },
  { key: "subtitle", label: "Subtitle", kind: "text" },
  { key: "period", label: "Period", kind: "text" },
  { key: "description", label: "Description", kind: "textarea" },
  { key: "url", label: "URL", kind: "url" },
  { key: "tags", label: "Tags", kind: "tags" },
];

export const blockSchemas: Record<string, BlockSchema> = {
  profile: { props: profileProps, items: [] },
  about: {
    props: [{ key: "text", label: "Text", kind: "textarea" }],
    items: [],
  },
  skills: {
    props: [],
    items: [
      { key: "name", label: "Name", kind: "text" },
      { key: "level", label: "Level", kind: "text" },
    ],
  },
  experience: { props: [], items: entryItems },
  projects: { props: [], items: entryItems },
  research: { props: [], items: entryItems },
  links: {
    props: [],
    items: [
      { key: "label", label: "Label", kind: "text" },
      { key: "url", label: "URL", kind: "url" },
    ],
  },
  stats: {
    props: [],
    items: [
      { key: "provider", label: "Provider", kind: "select", options: ["github"] },
      { key: "account", label: "Account", kind: "text" },
      { key: "show", label: "Show", kind: "tags" },
    ],
  },
  contact: {
    props: [{ key: "text", label: "Text", kind: "textarea" }],
    items: [
      { key: "label", label: "Label", kind: "text" },
      { key: "url", label: "URL", kind: "url" },
    ],
  },
};

export function getBlockSchema(type: string): BlockSchema {
  return blockSchemas[type] ?? { props: [], items: [] };
}

export function schemaTemplate(fields: SchemaField[]): Record<string, unknown> {
  return Object.fromEntries(fields.map((field) => [field.key, field.kind === "select" ? field.options?.[0] ?? "" : field.kind === "tags" ? [] : ""]));
}
