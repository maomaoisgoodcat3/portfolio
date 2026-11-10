"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ApiError, apiGet, apiSend, type Block, type BlockItem } from "@/lib/api";
import { BlockList } from "@/components/admin/BlockList";
import { blockTypes, CreateBlockForm } from "@/components/admin/CreateBlockForm";

type Me = { email: string; csrf_token: string };
type BlockType = (typeof blockTypes)[number];
type BlockPayload = { title?: string; visibility?: string; props?: Record<string, unknown> };
type ItemPayload = { data?: Record<string, unknown>; visibility?: string };

export default function AdminPage() {
  const router = useRouter();
  const [csrfToken, setCsrfToken] = useState<string | null>(null);
  const [blocks, setBlocks] = useState<Block[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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
        setError("Unable to load the admin session.");
      }
      return null;
    }
  }, [redirectToLogin]);

  const showError = useCallback((caught: unknown) => {
    if (caught instanceof ApiError && caught.status === 401) {
      redirectToLogin();
    } else if (caught instanceof ApiError && (caught.status === 404 || caught.status === 422)) {
      setError(caught.detail);
    } else {
      setError("Unable to complete that action.");
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
          if (active) setBlocks(result ?? []);
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
  }, [loadMe, showError]);

  async function createBlock(payload: { type: BlockType; title: string; visibility: string; props: Record<string, unknown> }) {
    const result = await write((token) => apiSend<Block>("POST", "/api/admin/blocks", payload, token));
    if (!result) return false;
    setBlocks((current) => [...current, result]);
    return true;
  }

  async function updateBlock(id: string, payload: BlockPayload) {
    const result = await write((token) => apiSend<Block>("PATCH", `/api/admin/blocks/${id}`, payload, token));
    if (result) setBlocks((current) => current.map((block) => block.id === id ? result : block));
  }

  async function deleteBlock(id: string) {
    let succeeded = false;
    await write(async (token) => {
      const result = await apiSend<undefined>("DELETE", `/api/admin/blocks/${id}`, undefined, token);
      succeeded = true;
      return result;
    });
    if (succeeded) setBlocks((current) => current.filter((block) => block.id !== id));
  }

  async function moveBlock(id: string, direction: -1 | 1) {
    const index = blocks.findIndex((block) => block.id === id);
    const target = index + direction;
    if (index < 0 || target < 0 || target >= blocks.length) return;
    const ids = blocks.map((block) => block.id);
    [ids[index], ids[target]] = [ids[target], ids[index]];
    const result = await write((token) => apiSend<Block[]>("PUT", "/api/admin/blocks/order", ids, token));
    if (result) setBlocks(result);
  }

  async function addItem(blockId: string, payload: { data: Record<string, unknown>; visibility: string }) {
    const result = await write((token) => apiSend<BlockItem>("POST", `/api/admin/blocks/${blockId}/items`, payload, token));
    if (!result) return false;
    setBlocks((current) => current.map((block) => block.id === blockId ? { ...block, items: [...block.items, result] } : block));
    return true;
  }

  async function updateItem(id: string, payload: ItemPayload) {
    const result = await write((token) => apiSend<BlockItem>("PATCH", `/api/admin/items/${id}`, payload, token));
    if (result) setBlocks((current) => current.map((block) => ({ ...block, items: block.items.map((item) => item.id === id ? result : item) })));
  }

  async function deleteItem(id: string) {
    let succeeded = false;
    await write(async (token) => {
      const result = await apiSend<undefined>("DELETE", `/api/admin/items/${id}`, undefined, token);
      succeeded = true;
      return result;
    });
    if (succeeded) setBlocks((current) => current.map((block) => ({ ...block, items: block.items.filter((item) => item.id !== id) })));
  }

  async function logout() {
    await write((token) => apiSend<undefined>("POST", "/api/auth/logout", undefined, token));
    setCsrfToken(null);
    setBlocks([]);
    setError(null);
    router.replace("/admin/login");
  }

  if (loading) return <main className="mx-auto max-w-5xl px-6 py-12 text-slate-500">Loading admin...</main>;

  return (
    <main className="mx-auto w-full max-w-5xl space-y-6 px-6 py-12">
      <header className="flex items-center justify-between gap-4">
        <h1 className="text-3xl font-bold text-slate-950">Admin</h1>
        <button className="rounded border border-slate-300 px-3 py-2" onClick={() => void logout()}>Log out</button>
      </header>
      {error && <p className="rounded-lg bg-red-50 p-3 text-red-800">{error}</p>}
      <CreateBlockForm onCreate={createBlock} />
      <BlockList blocks={blocks} onUpdate={updateBlock} onDelete={deleteBlock} onAddItem={addItem} onUpdateItem={updateItem} onDeleteItem={deleteItem} onMove={moveBlock} />
      <button className="text-sm text-slate-500 underline" onClick={() => void loadBlocks()}>Refresh blocks</button>
    </main>
  );
}
