"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { CulturalObject } from "@/lib/types";

export default function ReviewPage() {
  const { user, isReviewer, loading: authLoading } = useAuth();
  const [queue, setQueue] = useState<CulturalObject[]>([]);
  const [selected, setSelected] = useState<CulturalObject | null>(null);
  const [detail, setDetail] = useState<CulturalObject | null>(null);
  const [loading, setLoading] = useState(false);
  const [text, setText] = useState("");
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [statement, setStatement] = useState("");
  const [applied, setApplied] = useState(false);

  async function loadQueue() {
    const res = await api.listObjects({ status: "review", limit: 100 });
    const res2 = await api.listObjects({ status: "processing", limit: 100 });
    const merged = [...res2.items, ...res.items];
    setQueue(merged);
    setSelected((prev) => (prev && merged.some((o) => o.id === prev.id) ? prev : null));
    setDetail(null);
  }

  useEffect(() => {
    let alive = true;
    api
      .listObjects({ status: "review", limit: 100 })
      .then((r1) =>
        api.listObjects({ status: "processing", limit: 100 }).then((r2) => {
          if (!alive) return;
          const merged = [...r2.items, ...r1.items];
          setQueue(merged);
          setSelected((prev) => (prev && merged.some((o) => o.id === prev.id) ? prev : null));
        })
      )
      .catch(() => {
        if (alive) setError("Unable to load the review queue.");
      });
    return () => {
      alive = false;
    };
  }, []);

  async function openObject(obj: CulturalObject) {
    setSelected(obj);
    setDetail(null);
    setText("");
    setNote("");
    setMessage(null);
    setError(null);
    setLoading(true);
    try {
      const full = await api.getObject(obj.id);
      setDetail(full);
      setText(full.transcriptions[0]?.text ?? "");
    } catch {
      setError("Failed to load object details.");
    } finally {
      setLoading(false);
    }
  }

  async function approve() {
    if (!detail) return;
    setBusy(true);
    setMessage(null);
    setError(null);
    try {
      await api.createTranscription(detail.id, {
        text,
        language_id: detail.original_language?.id,
        verification_status: "human_reviewed",
      });
      await api.setStatus(detail.id, "verified");
      setMessage(`"${detail.title ?? detail.object_code}" verified by a human.`);
      await loadQueue();
      setSelected(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Approval failed");
    } finally {
      setBusy(false);
    }
  }

  async function requestFix() {
    if (!detail) return;
    setBusy(true);
    setError(null);
    try {
      await api.setStatus(detail.id, "processing");
      setMessage("Sent back for reprocessing with your note.");
      await loadQueue();
      setSelected(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed");
    } finally {
      setBusy(false);
    }
  }

  async function apply() {
    setBusy(true);
    setError(null);
    try {
      await api.auth.applyReviewer(statement.trim());
      setApplied(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not submit your application.");
    } finally {
      setBusy(false);
    }
  }

  if (authLoading) {
    return <p className="py-32 text-center text-stone-400">Loading…</p>;
  }

  if (!user) {
    return (
      <div className="mx-auto max-w-xl px-4 py-24 text-center">
        <h1 className="font-serif text-3xl font-bold text-brand-dark">The review circle</h1>
        <p className="mt-3 text-stone-600">
          Human reviewers verify that AI transcriptions match the original recording before an
          object can be published. Reviewing is reserved for members who are accepted into the
          review circle.
        </p>
        <div className="mt-8 flex justify-center gap-3">
          <Link
            href="/register"
            className="rounded-lg bg-brand px-6 py-3 font-semibold text-white hover:bg-brand-dark"
          >
            Join Mizizi
          </Link>
          <Link
            href="/login"
            className="rounded-lg border border-brand/30 bg-white px-6 py-3 font-semibold text-brand-dark hover:bg-brand/10"
          >
            Sign in
          </Link>
        </div>
      </div>
    );
  }

  if (!isReviewer) {
    return (
      <div className="mx-auto max-w-xl px-4 py-16">
        <h1 className="text-center font-serif text-3xl font-bold text-brand-dark">
          Become a reviewer
        </h1>
        <p className="mt-3 text-center text-stone-600">
          Reviewers verify that transcripts and translations faithfully represent the original
          recordings before they are published. Members can apply; an administrator decides.
        </p>
        <div className="mt-8 rounded-2xl border border-stone-200 bg-white p-6 shadow-sm">
          {applied ? (
            <p className="rounded-lg bg-amber-50 px-4 py-3 text-sm text-amber-800">
              Your application has been submitted and is awaiting an administrator&apos;s decision.
              You will be able to review once accepted.
            </p>
          ) : (
            <>
              <label className="mb-1 block text-sm font-semibold text-stone-700">
                Why do you want to review?
              </label>
              <textarea
                value={statement}
                onChange={(e) => setStatement(e.target.value)}
                rows={5}
                placeholder="Tell us about your knowledge of the language, community or tradition…"
                className="w-full rounded-lg border border-stone-300 px-3 py-2.5 text-sm"
              />
              {error && (
                <p className="mt-3 rounded-lg bg-rose-50 px-4 py-2 text-sm text-rose-700">{error}</p>
              )}
              <button
                onClick={() => void apply()}
                disabled={busy || statement.trim().length < 10}
                className="mt-4 w-full rounded-lg bg-brand px-6 py-3 font-semibold text-white transition hover:bg-brand-dark disabled:opacity-50"
              >
                {busy ? "Submitting…" : "Apply to review"}
              </button>
            </>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl px-4 py-10">
      <header className="mb-8">
        <h1 className="font-serif text-3xl font-bold text-brand-dark sm:text-4xl">Review</h1>
        <p className="mt-2 max-w-2xl text-stone-600">
          Human-in-the-loop verification. AI transcribes; a person confirms. Only after a human
          review can an object be verified — and only verified objects can be published.
        </p>
      </header>

      {message && (
        <p className="mb-6 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
          {message}
        </p>
      )}

      <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
        <aside className="rounded-2xl border border-stone-200 bg-white p-4 shadow-sm">
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-stone-500">
            Queue ({queue.length})
          </h2>
          <div className="space-y-2">
            {queue.map((obj) => (
              <button
                key={obj.id}
                onClick={() => openObject(obj)}
                className={`w-full rounded-lg border p-3 text-left text-sm transition ${
                  selected?.id === obj.id
                    ? "border-brand bg-brand/10"
                    : "border-stone-200 hover:border-brand/40"
                }`}
              >
                <p className="font-semibold text-stone-800">{obj.title ?? "Untitled"}</p>
                <p className="mt-0.5 font-mono text-xs text-stone-400">{obj.object_code}</p>
                <p className="mt-1 text-xs capitalize text-stone-500">
                  {obj.object_type} · {obj.verification_status.replaceAll("_", " ")}
                </p>
              </button>
            ))}
            {queue.length === 0 && (
              <p className="p-4 text-center text-sm text-stone-400">
                Nothing awaiting review.{" "}
                <Link href="/archive" className="text-accent hover:underline">Browse the archive</Link>.
              </p>
            )}
          </div>
        </aside>

        <section className="rounded-2xl border border-stone-200 bg-white p-6 shadow-sm">
          {loading ? (
            <div className="flex h-full min-h-[300px] items-center justify-center p-8 text-center text-stone-400">
              Loading object…
            </div>
          ) : detail ? (
            <>
              <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
                <div>
                  <h2 className="font-serif text-xl font-bold text-brand-dark">
                    {detail.title ?? "Untitled"}
                  </h2>
                  <p className="font-mono text-xs text-stone-400">{detail.object_code}</p>
                </div>
                <Link href={`/object/${detail.id}`} className="text-sm font-semibold text-accent hover:underline">
                  Open object →
                </Link>
              </div>

              {detail.media_assets[0]?.media_type === "audio" && (
                <audio
                  controls
                  preload="metadata"
                  src={api.mediaUrl(detail.id, detail.media_assets[0].id)}
                  className="mb-5 w-full"
                />
              )}

              <label className="mb-1 block text-sm font-semibold text-stone-700">
                Transcript — verify or correct, then approve
              </label>
              <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                rows={8}
                className="w-full rounded-lg border border-stone-300 px-3 py-2.5 text-sm leading-relaxed"
              />
              <label className="mt-3 mb-1 block text-sm font-semibold text-stone-700">
                Note to the contributor / model (optional)
              </label>
              <textarea
                value={note}
                onChange={(e) => setNote(e.target.value)}
                rows={2}
                placeholder="e.g. 'Slight mis-transcription of the greeting in stanza 2'"
                className="w-full rounded-lg border border-stone-300 px-3 py-2.5 text-sm"
              />

              {error && <p className="mt-3 rounded-lg bg-rose-50 px-4 py-2 text-sm text-rose-700">{error}</p>}

              <div className="mt-4 flex flex-wrap gap-3">
                <button
                  onClick={approve}
                  disabled={busy}
                  className="rounded-lg bg-emerald-700 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-emerald-800 disabled:opacity-50"
                >
                  {busy ? "Verifying..." : "✓ Verify & approve"}
                </button>
                <button
                  onClick={requestFix}
                  disabled={busy}
                  className="rounded-lg border border-amber-400 bg-amber-50 px-5 py-2.5 text-sm font-semibold text-amber-800 transition hover:bg-amber-100 disabled:opacity-50"
                >
                  Send back for reprocessing
                </button>
              </div>
            </>
          ) : (
            <div className="flex h-full min-h-[300px] items-center justify-center p-8 text-center text-stone-400">
              {queue.length === 0
                ? "The review queue is empty — a healthy archive."
                : "Select an item from the queue to review it."}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}