"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import type { CulturalObject, SearchResponse } from "@/lib/types";

export default function AiPage() {
  const [q, setQ] = useState("");
  const [searching, setSearching] = useState(false);
  const [results, setResults] = useState<SearchResponse | null>(null);
  const [selected, setSelected] = useState<CulturalObject | null>(null);

  const [derivativeType, setDerivativeType] = useState("adaptation");
  const [derivativeTitle, setDerivativeTitle] = useState("");
  const [derivativeContent, setDerivativeContent] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);

  async function doSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!q.trim()) return;
    setSearching(true);
    setMessage(null);
    try {
      setResults(await api.search(q.trim()));
    } catch (err) {
      setMessage({ ok: false, text: String(err) });
    } finally {
      setSearching(false);
    }
  }

  const permission = selected?.permissions[0];
  const aiAllowed = !!permission?.ai_analysis;

  async function generateDerivative(e: React.FormEvent) {
    e.preventDefault();
    if (!selected) return;
    setBusy(true);
    setMessage(null);
    try {
      const d = await api.createDerivative(selected.id, {
        derivative_type: derivativeType,
        title: derivativeTitle || undefined,
        content: derivativeContent || undefined,
        model_name: "mizizi-adaptation-alpha",
      });
      setMessage({
        ok: true,
        text: `Derivative created (${d.derivative_type}). A human must review it before it can be shared.`,
      });
    } catch (err) {
      setMessage({
        ok: false,
        text: err instanceof Error ? err.message : "Generation blocked",
      });
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-6xl px-4 py-10">
      <header className="mb-8">
        <h1 className="font-serif text-3xl font-bold text-brand-dark sm:text-4xl">Ask Mizizi</h1>
        <p className="mt-2 max-w-2xl text-stone-600">
          Permission-aware AI. Mizizi never touches a story without consent: it can only adapt a
          Cultural Object if the community granted{" "}
          <span className="font-semibold">AI analysis</span> and{" "}
          <span className="font-semibold">derivative work</span>. Everything AI produces is
          tagged, reviewable, and never replaces the original.
        </p>
      </header>

      <form onSubmit={doSearch} className="mb-8 flex gap-2">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search for a story to adapt — e.g. 'the hare' or 'lullaby'"
          className="flex-1 rounded-lg border border-stone-300 bg-white px-4 py-2.5 text-sm outline-none focus:border-brand"
        />
        <button
          type="submit"
          disabled={searching}
          className="rounded-lg bg-brand px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-brand-dark disabled:opacity-50"
        >
          {searching ? "Searching..." : "Search"}
        </button>
      </form>

      <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
        <aside className="rounded-2xl border border-stone-200 bg-white p-4 shadow-sm">
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-stone-500">
            Results ({results?.total ?? 0})
          </h2>
          <div className="space-y-2">
            {(results?.results ?? []).map((obj) => {
              const p = obj.permissions[0];
              const can = !!p?.ai_analysis && !!p?.derivative_work;
              return (
                <button
                  key={obj.id}
                  onClick={() => {
                    setSelected(obj);
                    setMessage(null);
                    setDerivativeContent("");
                    setDerivativeTitle("");
                  }}
                  className={`w-full rounded-lg border p-3 text-left text-sm transition ${
                    selected?.id === obj.id
                      ? "border-brand bg-brand/10"
                      : "border-stone-200 hover:border-brand/40"
                  }`}
                >
                  <p className="font-semibold text-stone-800">{obj.title ?? "Untitled"}</p>
                  <p className="mt-0.5 font-mono text-xs text-stone-400">{obj.object_code}</p>
                  <p className="mt-1 text-xs">
                    {can ? (
                      <span className="font-medium text-emerald-700">✓ AI use permitted</span>
                    ) : (
                      <span className="text-stone-400">✗ AI use not granted</span>
                    )}
                  </p>
                </button>
              );
            })}
            {results && results.results.length === 0 && (
              <p className="p-4 text-center text-sm text-stone-400">No results.</p>
            )}
          </div>
        </aside>

        <section className="rounded-2xl border border-stone-200 bg-white p-6 shadow-sm">
          {selected ? (
            <>
              <h2 className="font-serif text-xl font-bold text-brand-dark">
                {selected.title ?? "Untitled"}
              </h2>
              <p className="mb-4 font-mono text-xs text-stone-400">{selected.object_code}</p>

              {aiAllowed ? (
                <form onSubmit={generateDerivative} className="space-y-4">
                  <p className="rounded-lg bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
                    This community granted AI analysis and derivative work. Mizizi may adapt this
                    story — the output will be recorded as a derivative and require human review.
                  </p>
                  <div className="grid gap-4 sm:grid-cols-2">
                    <div>
                      <label className="mb-1 block text-sm font-semibold text-stone-700">Type of adaptation</label>
                      <select value={derivativeType} onChange={(e) => setDerivativeType(e.target.value)}
                        className="w-full rounded-lg border border-stone-300 px-3 py-2.5 text-sm">
                        <option value="adaptation">Adaptation</option>
                        <option value="retelling">Retelling</option>
                        <option value="translation_expansion">Translation expansion</option>
                        <option value="childrens_version">Children&apos;s version</option>
                        <option value="study_notes">Study notes</option>
                      </select>
                    </div>
                    <div>
                      <label className="mb-1 block text-sm font-semibold text-stone-700">Title (optional)</label>
                      <input value={derivativeTitle} onChange={(e) => setDerivativeTitle(e.target.value)}
                        className="w-full rounded-lg border border-stone-300 px-3 py-2.5 text-sm" />
                    </div>
                  </div>
                  <div>
                    <label className="mb-1 block text-sm font-semibold text-stone-700">
                      AI output / draft
                    </label>
                    <textarea value={derivativeContent} onChange={(e) => setDerivativeContent(e.target.value)}
                      rows={6}
                      placeholder="The AI-generated adaptation lands here (LLM integration hooks into the derivative endpoint)."
                      className="w-full rounded-lg border border-stone-300 px-3 py-2.5 text-sm" />
                  </div>
                  {message && (
                    <p className={`rounded-lg px-4 py-3 text-sm ${message.ok ? "bg-emerald-50 text-emerald-800" : "bg-rose-50 text-rose-700"}`}>
                      {message.text}
                    </p>
                  )}
                  <button type="submit" disabled={busy}
                    className="rounded-lg bg-brand px-6 py-3 font-semibold text-white transition hover:bg-brand-dark disabled:opacity-50">
                    {busy ? "Generating..." : "Generate derivative"}
                  </button>
                </form>
              ) : (
                <div className="rounded-xl border border-dashed border-stone-300 p-8 text-center">
                  <p className="text-3xl">🔒</p>
                  <p className="mt-3 font-semibold text-stone-700">AI use was not granted for this story</p>
                  <p className="mx-auto mt-1 max-w-md text-sm text-stone-500">
                    The community has not consented to AI analysis or derivative work. Mizizi
                    respects that boundary — this object is protected from adaptation.
                  </p>
                </div>
              )}
            </>
          ) : (
            <div className="flex h-full min-h-[300px] items-center justify-center p-8 text-center text-stone-400">
              Search the archive and select a Cultural Object to work with.
            </div>
          )}
        </section>
      </div>
    </div>
  );
}