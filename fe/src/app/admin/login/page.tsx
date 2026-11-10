"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { ApiError, apiSend } from "@/lib/api";

function messageFor(error: unknown, expired = false): string {
  if (error instanceof ApiError && error.status === 429) {
    return "Too many attempts. Try again in 15 minutes.";
  }
  if (expired) {
    return "Session expired, please sign in again.";
  }
  return "Invalid credentials";
}

export default function AdminLoginPage() {
  const router = useRouter();
  const [step, setStep] = useState<1 | 2>(1);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function submitPassword(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await apiSend("POST", "/api/auth/login", { email, password });
      setPassword("");
      setStep(2);
    } catch (caught) {
      setError(messageFor(caught));
      setPassword("");
    } finally {
      setSubmitting(false);
    }
  }

  async function submitCode(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    const submittedCode = code;
    setCode("");
    try {
      await apiSend("POST", "/api/auth/totp", { code: submittedCode });
      router.replace("/admin");
    } catch (caught) {
      if (caught instanceof ApiError && caught.status === 401) {
        setStep(1);
        setError(messageFor(caught, true));
      } else {
        setError(messageFor(caught));
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="mx-auto flex w-full max-w-md flex-1 flex-col justify-center px-6 py-12">
      <h1 className="text-3xl font-bold text-slate-950">Admin sign in</h1>
      {error && <p className="mt-4 rounded-lg bg-red-50 p-3 text-red-800">{error}</p>}
      {step === 1 ? (
        <form className="mt-6 space-y-4" onSubmit={submitPassword}>
          <label className="block text-sm font-medium text-slate-700">
            Email
            <input
              className="mt-1 w-full rounded border border-slate-300 p-2"
              type="email"
              autoComplete="username"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />
          </label>
          <label className="block text-sm font-medium text-slate-700">
            Password
            <input
              className="mt-1 w-full rounded border border-slate-300 p-2"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
          </label>
          <button className="rounded bg-slate-900 px-4 py-2 text-white disabled:opacity-50" disabled={submitting}>
            Continue
          </button>
        </form>
      ) : (
        <form className="mt-6 space-y-4" onSubmit={submitCode}>
          <label className="block text-sm font-medium text-slate-700">
            TOTP or recovery code
            <input
              className="mt-1 w-full rounded border border-slate-300 p-2"
              type="text"
              autoComplete="one-time-code"
              value={code}
              onChange={(event) => setCode(event.target.value)}
              required
            />
          </label>
          <button className="rounded bg-slate-900 px-4 py-2 text-white disabled:opacity-50" disabled={submitting}>
            Verify
          </button>
        </form>
      )}
    </main>
  );
}
