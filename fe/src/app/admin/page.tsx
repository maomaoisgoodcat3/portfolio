"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ApiError, apiGet, apiSend, type Block } from "@/lib/api";
import { BlockList } from "@/components/admin/BlockList";
import { blockTypes, CreateBlockForm } from "@/components/admin/CreateBlockForm";

type Me = { email: string; csrf_token: string };
type BlockType = (typeof blockTypes)[number];
type BlockPayload = { title?: string; visibility?: string; props?: Record<string, unknown> };
type ChatSettings = { chat_enabled: boolean };
type ChatLog = { id: number; created_at: string; lang: string; question: string; answer_chars: number; refused: boolean; error: string | null };
type ChatStats = { today: number; chat_daily_limit: number; logs: ChatLog[] };
export default function AdminPage() {
  const router = useRouter();
  const [csrfToken, setCsrfToken] = useState<string | null>(null);
  const [blocks, setBlocks] = useState<Block[]>([]);
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState("Loading...");
  const [chatSettings, setChatSettings] = useState<ChatSettings | null>(null);
  const [chatStats, setChatStats] = useState<ChatStats | null>(null);

  const redirectToLogin = useCallback(() => router.replace("/admin/login"), [router]);

  const loadMe = useCallback(async () => {
    try {
      const me = await apiGet<Me>("/api/auth/me");
      if (!me) throw new Error("Missing session.");
      setCsrfToken(me.csrf_token);
      return me;
    } catch (caught) {
      if (caught instanceof ApiError && caught.status === 401) {
        redirectToLogin();
      } else {
        setStatus("Unable to load the admin session.");
      }
      return null;
    }
  }, [redirectToLogin]);

  const showError = useCallback((caught: unknown) => {
    if (caught instanceof ApiError && caught.status === 401) {
      redirectToLogin();
    } else if (caught instanceof ApiError && (caught.status === 404 || caught.status === 422)) {
      setStatus(caught.detail);
    } else {
      setStatus("Unable to complete that action.");
    }
  }, [redirectToLogin]);

  const write = useCallback(async <T,>(operation: (token: string) => Promise<T | undefined>) => {
    if (!csrfToken) return undefined;
    try {
      return await operation(csrfToken);
    } catch (caught) {
      if (!(caught instanceof ApiError) || caught.status !== 403) {
        showError(caught);
        return undefined;
      }
      const me = await loadMe();
      if (!me) return undefined;
      try {
        return await operation(me.csrf_token);
      } catch (retryError) {
        showError(retryError);
        return undefined;
      }
    }
  }, [csrfToken, loadMe, showError]);

  const loadBlocks = useCallback(async () => {
    try {
      const result = await apiGet<Block[]>("/api/admin/blocks");
      setBlocks(result ?? []);
      setStatus("Saved");
    } catch (caught) {
      showError(caught);
    }
  }, [showError]);

  const loadChat = useCallback(async () => {
    try {
      const [settingsResult, statsResult] = await Promise.all([
        apiGet<ChatSettings>("/api/admin/chat/settings"),
        apiGet<ChatStats>("/api/admin/chat/stats"),
      ]);
      setChatSettings(settingsResult ?? null);
      setChatStats(statsResult ?? null);
    } catch (caught) {
      showError(caught);
    }
  }, [showError]);

  useEffect(() => {
    let active = true;
    (async () => {
      const me = await loadMe();
      if (me && active) {
        try {
          const result = await apiGet<Block[]>("/api/admin/blocks");
          if (active) {
            setBlocks(result ?? []);
            setStatus("Saved");
          }
          await loadChat();
        } catch (caught) {
          if (active) showError(caught);
        } finally {
          if (active) setLoading(false);
        }
      } else if (active) {
        setLoading(false);
      }
    })();
    return () => { active = false; };
  }, [loadChat, loadMe, showError]);

  async function updateChatEnabled(enabled: boolean) {
    const result = await write((token) => apiSend<ChatSettings>("PUT", "/api/admin/chat/settings", { chat_enabled: enabled }, token));
    if (result) {
      setChatSettings(result);
      setStatus("Saved");
    }
  }

  async function createBlock(payload: { type: BlockType; title: string; visibility: string; props: Record<string, unknown> }) {
    const result = await write((token) => apiSend<Block>("POST", "/api/admin/blocks", payload, token));
    if (!result) return false;
    setBlocks((current) => [...current, result]);
    setStatus("Saved");
    return true;
  }

  async function updateBlock(id: string, payload: BlockPayload) {
    const result = await write((token) => apiSend<Block>("PATCH", `/api/admin/blocks/${id}`, payload, token));
    if (result) {
      setBlocks((current) => current.map((block) => block.id === id ? result : block));
      setStatus("Saved");
    }
  }

  async function deleteBlock(id: string) {
    let succeeded = false;
    await write(async (token) => {
      const result = await apiSend<undefined>("DELETE", `/api/admin/blocks/${id}`, undefined, token);
      succeeded = true;
      return result;
    });
    if (succeeded) {
      setBlocks((current) => current.filter((block) => block.id !== id));
      setStatus("Deleted");
    }
  }

  async function moveBlock(id: string, direction: -1 | 1) {
    const index = blocks.findIndex((block) => block.id === id);
    const target = index + direction;
    if (index < 0 || target < 0 || target >= blocks.length) return;
    const ids = blocks.map((block) => block.id);
    [ids[index], ids[target]] = [ids[target], ids[index]];
    const result = await write((token) => apiSend<Block[]>("PUT", "/api/admin/blocks/order", ids, token));
    if (result) {
      setBlocks(result);
      setStatus("Saved");
    }
  }

  async function logout() {
    await write((token) => apiSend<undefined>("POST", "/api/auth/logout", undefined, token));
    setCsrfToken(null);
    setBlocks([]);
    setStatus("");
    router.replace("/admin/login");
  }

  if (loading) return <main className="mx-auto max-w-5xl px-6 py-12 text-muted">Loading admin...</main>;

  return (
    <main className="mx-auto w-full max-w-5xl space-y-6 px-6 py-12">
      <header className="flex items-center justify-between gap-4">
        <h1 className="font-pixel text-3xl text-accent">Admin</h1>
        <button className="pixel-button border-danger px-3 py-2 text-danger" onClick={() => void logout()}>Log out</button>
      </header>
      <p className="pixel-box border-muted bg-surface px-3 py-2 text-sm text-muted" role="status">{status}</p>
      <CreateBlockForm existingTypes={blocks.map((block) => block.type)} onCreate={createBlock} />
      <BlockList blocks={blocks} onUpdate={updateBlock} onDelete={deleteBlock} onMove={moveBlock} />
      <button className="pixel-button border-muted px-3 py-2 text-sm text-muted" onClick={() => void loadBlocks()}>Refresh blocks</button>
      <section className="pixel-box space-y-4 bg-surface p-4 text-text" aria-labelledby="chatbot-heading">
        <div className="flex items-center justify-between gap-4">
          <h2 id="chatbot-heading" className="font-pixel text-2xl text-accent">Chatbot</h2>
          <label className="flex items-center gap-2">
            <input type="checkbox" checked={chatSettings?.chat_enabled ?? false} onChange={(event) => void updateChatEnabled(event.target.checked)} />
            Enabled
          </label>
        </div>
        {chatStats && <p className="text-sm text-muted">Today: {chatStats.today} / {chatStats.chat_daily_limit}</p>}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead><tr><th>Time</th><th>Lang</th><th>Question</th><th>Chars</th><th>Refused</th><th>Error</th></tr></thead>
            <tbody>{chatStats?.logs.slice(0, 10).map((log) => <tr key={log.id} className="border-t border-muted"><td>{new Date(log.created_at).toLocaleString()}</td><td>{log.lang}</td><td className="max-w-56 overflow-wrap-anywhere">{log.question}</td><td>{log.answer_chars}</td><td>{log.refused ? "Yes" : "No"}</td><td>{log.error ?? ""}</td></tr>)}</tbody>
          </table>
        </div>
      </section>
    </main>
  );
}
