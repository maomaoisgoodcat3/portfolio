"use client";

import { useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";
import { ApiError, chat, type ChatHistoryItem, type ChatSource } from "@/lib/api";
import { safeHref } from "@/lib/safe-url";
import type { Pet } from "./pet";

declare global {
  interface Window { turnstile?: { render: (element: HTMLElement, options: Record<string, unknown>) => string; execute: (id: string) => void; reset: (id: string) => void }; }
}

function inline(text: string): ReactNode[] {
  const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`|\[[^\]]+\]\([^)]+\))/g);
  return parts.map((part, index) => {
    if (part.startsWith("**") && part.endsWith("**")) return <strong key={index}>{part.slice(2, -2)}</strong>;
    if (part.startsWith("`") && part.endsWith("`")) return <code key={index}>{part.slice(1, -1)}</code>;
    const link = part.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
    if (link) {
      const href = safeHref(link[2]);
      return href ? <a key={index} href={href} target="_blank" rel="noreferrer">{link[1]}</a> : <span key={index}>{link[1]}</span>;
    }
    return <span key={index}>{part}</span>;
  });
}

function Markdown({ text }: { text: string }) {
  const lines = text.split(/\r?\n/); const nodes: ReactNode[] = []; let bullets: string[] = [];
  const flush = () => { if (bullets.length) { nodes.push(<ul key={`ul-${nodes.length}`}>{bullets.map((item, index) => <li key={index}>{inline(item)}</li>)}</ul>); bullets = []; } };
  lines.forEach((line, index) => {
    if (/^\s*[-*]\s+/.test(line)) { bullets.push(line.replace(/^\s*[-*]\s+/, "")); return; }
    flush();
    if (line.trim()) nodes.push(<p key={index}>{inline(line)}</p>);
  });
  flush();
  return <>{nodes}</>;
}

type Props = { open: boolean; onClose: () => void; pet: Pet | null };
export function ChatPanel({ open, onClose, pet }: Props) {
  const [message, setMessage] = useState(""); const [messages, setMessages] = useState<ChatHistoryItem[]>([]);
  const [rendered, setRendered] = useState<ChatHistoryItem[]>([]); const [sources, setSources] = useState<Record<number, ChatSource[]>>({});
  const [busy, setBusy] = useState(false); const [error, setError] = useState<string | null>(null);
  const turnstile = useRef<string | null>(null); const tokenWaiter = useRef<((token: string) => void) | null>(null); const host = useRef<HTMLDivElement>(null);
  const siteKey = process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY;

  useEffect(() => {
    if (!open || !host.current || !siteKey) return;
    let active = true;
    const render = () => { if (active && window.turnstile && host.current && !turnstile.current) turnstile.current = window.turnstile.render(host.current, { sitekey: siteKey, size: "normal", callback: (token: string) => tokenWaiter.current?.(token) }); };
    if (window.turnstile) render();
    else {
      const script = document.createElement("script"); script.src = "https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit"; script.async = true; script.onload = render; document.head.appendChild(script);
    }
    return () => { active = false; };
  }, [open, siteKey]);

  useEffect(() => {
    if (!open) return;
    const closeOnEscape = (event: KeyboardEvent) => { if (event.key === "Escape") onClose(); };
    document.addEventListener("keydown", closeOnEscape); return () => document.removeEventListener("keydown", closeOnEscape);
  }, [open, onClose]);

  async function send() {
    if (!message.trim() || busy || !turnstile.current) return;
    const question = message.trim(); setMessage(""); setError(null); setBusy(true); pet?.act("think");
    const token = await new Promise<string>((resolve) => {
      const id = turnstile.current; if (!id || !window.turnstile) return resolve("");
      tokenWaiter.current = resolve; window.turnstile.execute(id);
    });
    try {
      if (!token) throw new ApiError(403, "Verification failed");
      const result = await chat(question, messages.slice(-6), token);
      if (!result) throw new Error("No response");
      const user = { role: "user" as const, content: question }; const assistant = { role: "assistant" as const, content: result.answer };
      setMessages((current) => [...current, user, assistant].slice(-6)); setRendered((current) => [...current, user, { ...assistant, content: "" }].slice(-6));
      let count = 0;
      const timer = window.setInterval(() => {
        count = Math.min(assistant.content.length, count + 1);
        setRendered((current) => current.map((item, index) => index === current.length - 1 ? { ...item, content: assistant.content.slice(0, count) } : item));
        if (count === assistant.content.length) window.clearInterval(timer);
      }, 25);
      setSources((current) => ({ ...current, [rendered.length + 1]: result.sources })); pet?.act("happy");
    } catch (caught) {
      pet?.act("sad");
      setError(caught instanceof ApiError && caught.status === 429 ? "Please wait a little before asking again" : caught instanceof ApiError && caught.status === 503 ? "Chat is resting right now" : caught instanceof ApiError && caught.status === 403 ? "Please complete the verification to continue." : "Cazung could not answer right now.");
    } finally { setBusy(false); if (turnstile.current) window.turnstile?.reset(turnstile.current); }
  }

  if (!open) return null;
  return <section className="cazung-panel pixel-box" aria-label="Cazung chat">
    <header className="flex items-center justify-between border-b-2 border-current bg-accent px-2 py-2 text-bg"><h2 className="font-pixel text-lg">Cazung</h2><button type="button" onClick={onClose} aria-label="Close chat">×</button></header>
    <div className="cazung-messages" aria-live="polite">
      {rendered.map((item, index) => <div key={`${index}-${item.role}`} className={`cazung-message ${item.role === "user" ? "cazung-user" : "cazung-assistant"}`}><Markdown text={item.content} />{item.role === "assistant" && sources[index]?.length ? <div className="mt-2 text-xs">{sources[index].map((source) => source.access === "private" ? <div key={source.title}><span>{source.title} — Private, under review</span> <a href="#contact">Contact</a></div> : <div key={`${source.title}-${source.url}`}><a href={safeHref(source.url) ?? "#"}>{source.title}</a></div>)}</div> : null}</div>)}
      {error && <p className="cazung-error">{error}</p>}
    </div>
    <div ref={host} className="cazung-turnstile" />
    <p className="px-2 text-xs text-muted">Answers are generated by Google Gemini from Manh&apos;s public documents. Please do not share personal information.</p>
    <div className="cazung-composer"><textarea value={message} maxLength={500} onChange={(event) => { setMessage(event.target.value); pet?.act("talk"); }} aria-label="Message" /><span>{message.length}/500</span><button type="button" onClick={() => void send()} disabled={busy || !message.trim()}>Send</button></div>
  </section>;
}
