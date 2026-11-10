export type FieldKind = "text" | "textarea" | "url" | "https_url" | "tags" | "select";

export type SchemaField = {
  key: string;
  label: string;
  kind: FieldKind;
  required?: boolean;
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

export const blockSchemas: Record<string, BlockSchema> = {
  profile: { props: profileProps, items: [] },
  about: {
    props: [{ key: "content", label: "Content", kind: "textarea" }],
    items: [],
  },
  skills: {
    props: [{ key: "tags", label: "Tags", kind: "tags" }],
    items: [],
  },
  experience: {
    props: [
      { key: "subtitle", label: "Subtitle", kind: "text" },
      { key: "period", label: "Period", kind: "text" },
      { key: "content", label: "Content", kind: "textarea" },
      { key: "url", label: "URL", kind: "url" },
    ],
    items: [],
  },
  projects: {
    props: [
      { key: "period", label: "Period", kind: "text" },
      { key: "content", label: "Content", kind: "textarea" },
      { key: "url", label: "URL", kind: "url" },
      { key: "tags", label: "Tags", kind: "tags" },
    ],
    items: [],
  },
  research: {
    props: [
      { key: "subtitle", label: "Subtitle", kind: "text" },
      { key: "period", label: "Period", kind: "text" },
      { key: "content", label: "Content", kind: "textarea" },
      { key: "url", label: "URL", kind: "url" },
    ],
    items: [],
  },
  links: {
    props: [{ key: "url", label: "URL", kind: "url", required: true }],
    items: [],
  },
  stats: {
    props: [
      { key: "provider", label: "Provider", kind: "select", options: ["github"] },
      { key: "account", label: "Account", kind: "text" },
    ],
    items: [],
  },
  contact: {
    props: [{ key: "content", label: "Content", kind: "textarea" }],
    items: [],
  },
};

export function getBlockSchema(type: string): BlockSchema {
  return blockSchemas[type] ?? { props: [], items: [] };
}

export function schemaTemplate(fields: SchemaField[]): Record<string, unknown> {
  return Object.fromEntries(fields.map((field) => [field.key, field.kind === "select" ? field.options?.[0] ?? "" : field.kind === "tags" ? [] : ""]));
}
