"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { CulturalObject, PublishCheck } from "@/lib/types";

const TYPE_LABELS: Record<string, string> = {
  story: "Story",
  song: "Song",
  riddle: "Riddle",
  proverb: "Proverb",
  poem: "Poem",
  oral_history: "Oral History",
  personal_memory: "Memory",
};

export default function ObjectPage({ params }: { params: Promise<{ id: string }> }) {
  const { user } = useAuth();
  const [obj, setObj] = useState<CulturalObject | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"transcript" | "translation" | "provenance">("transcript");
  const [publishCheck, setPublishCheck] = useState<PublishCheck | null>(null);
  const [publishing, setPublishing] = useState(false);
  const [publishMsg, setPublishMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [permBusy, setPermBusy] = useState(false);
  const [permMsg, setPermMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [keyInput, setKeyInput] = useState("");

  useEffect(() => {
    let alive = true;
    params.then(({ id }) =>
      api.getObject(id).then((o) => {
        if (!alive) return;
        setObj(o);
        if (user) {
          api.publishCheck(id).then((pc) => alive && setPublishCheck(pc)).catch(() => alive && setPublishCheck(null));
        }
      }).catch((e) => alive && setError(String(e)))
    );
    return () => {
      alive = false;
    };
  }, [params, user]);

  if (error) return <div className="mx-auto max-w-4xl px-4 py-16 text-center text-rose-600">{error}</div>;
  if (!obj) return <div className="mx-auto max-w-4xl px-4 py-16 text-center text-stone-500">Loading object...</div>;

  const original = obj.media_assets.find((m) => m.is_original) ?? obj.media_assets[0];
  const latestTranscript = obj.transcriptions[0];
  const latestTranslation = obj.translations[0];
  const publicPermission = obj.permissions.find((p) => p.public_access);
  const hasStoredKey = (() => {
    try {
      return !!localStorage.getItem(`mizizi:creator:${obj.id}`);
    } catch {
      return false;
    }
  })();

  async function doPublish() {
    if (!obj) return;
    setPublishing(true);
    setPublishMsg(null);
    try {
      const updated = await api.publish(obj.id);
      setObj(updated);
      const pc = await api.publishCheck(obj.id);
      setPublishCheck(pc);
      setPublishMsg({ ok: true, text: `${updated.object_code} is now live in the archive.` });
    } catch (err) {
      setPublishMsg({ ok: false, text: err instanceof Error ? err.message : "Publishing failed" });
    } finally {
      setPublishing(false);
    }
  }

  async function grantPublicAccess() {
    if (!obj) return;
    let stored: string | null = null;
    try {
      stored = localStorage.getItem(`mizizi:creator:${obj.id}`);
    } catch {
      /* ignore */
    }
    const key = (stored ?? keyInput).trim();
    setPermBusy(true);
    setPermMsg(null);
    try {
      await api.setPermissions(obj.id, { public_access: true }, key || undefined);
      const fresh = await api.getObject(obj.id);
      setObj(fresh);
      const pc = await api.publishCheck(obj.id);
      setPublishCheck(pc);
      setPermMsg({
        ok: true,
        text: "Public access granted by the creator. Recorded in the provenance trail.",
      });
    } catch (err) {
      setPermMsg({ ok: false, text: err instanceof Error ? err.message : "Failed to grant access" });
    } finally {
      setPermBusy(false);
    }
  }

  const allSatisfied = publishCheck?.requirements.every((r) => r.satisfied) ?? false;

  return (
    <div className="mx-auto max-w-4xl px-4 py-10">
      <Link href="/archive" className="text-sm font-medium text-accent hover:underline">
        ← Back to archive
      </Link>

      <header className="mt-4 flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="rounded-full bg-brand/10 px-2.5 py-0.5 text-xs font-semibold text-brand-dark">
              {TYPE_LABELS[obj.object_type] ?? obj.object_type}
            </span>
            <span className="font-mono text-xs text-stone-400">{obj.object_code}</span>
          </div>
          <h1 className="mt-3 font-serif text-3xl font-bold text-brand-dark sm:text-4xl">
            {obj.title ?? "Untitled"}
          </h1>
          <p className="mt-2 max-w-2xl text-stone-600">{obj.description}</p>
        </div>
        <div className="rounded-xl border border-stone-200 bg-white px-4 py-3 text-sm shadow-sm">
          <p><span className="text-stone-500">Status:</span> <span className="font-semibold capitalize">{obj.status}</span></p>
          <p><span className="text-stone-500">Verified:</span> <span className="capitalize">{obj.verification_status.replaceAll("_", " ")}</span></p>
          {publicPermission && <p className="text-emerald-700">✓ Public access granted</p>}
        </div>
      </header>

      {publishCheck && obj.status !== "published" && (
        <section className="mt-6 rounded-2xl border border-stone-200 bg-white p-5 shadow-sm">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-stone-500">
              Publication requirements
            </h2>
            <span
              className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                allSatisfied ? "bg-emerald-100 text-emerald-800" : "bg-amber-100 text-amber-800"
              }`}
            >
              {allSatisfied ? "Ready to publish" : `${publishCheck.requirements.filter((r) => !r.satisfied).length} requirement(s) missing`}
            </span>
          </div>
          <ul className="space-y-2">
            {publishCheck.requirements.map((r) => (
              <li key={r.requirement} className="flex items-start gap-2 text-sm">
                <span className={r.satisfied ? "mt-0.5 text-emerald-600" : "mt-0.5 text-amber-500"}>
                  {r.satisfied ? "✓" : "○"}
                </span>
                <span className={r.satisfied ? "text-stone-700" : "text-stone-500"}>{r.label}</span>
              </li>
            ))}
          </ul>
          {allSatisfied && obj.status === "verified" && (
            <>
              <button
                onClick={doPublish}
                disabled={publishing}
                className="mt-4 rounded-lg bg-emerald-700 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-emerald-800 disabled:opacity-50"
              >
                {publishing ? "Publishing..." : "Publish to archive"}
              </button>
              <p className="mt-2 text-xs text-stone-400">
                The object becomes publicly visible with its provenance and permissions intact.
              </p>
            </>
          )}
          {publishMsg && (
            <p className={`mt-3 rounded-lg px-4 py-2 text-sm ${publishMsg.ok ? "bg-emerald-50 text-emerald-800" : "bg-rose-50 text-rose-700"}`}>
              {publishMsg.text}
            </p>
          )}
        </section>
      )}

      {original && (
        <section className="mt-8 rounded-2xl border border-stone-200 bg-white p-5 shadow-sm">
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-stone-500">
            Original recording
          </h2>
          {original.media_type === "audio" ? (
            <audio
              controls
              preload="metadata"
              src={api.mediaUrl(obj.id, original.id)}
              className="w-full"
            />
          ) : (
            <video
              controls
              preload="metadata"
              src={api.mediaUrl(obj.id, original.id)}
              className="w-full rounded-lg"
            />
          )}
          <p className="mt-2 flex flex-wrap items-center gap-3 text-xs text-stone-500">
            <span className="font-mono">{original.sha256_checksum.slice(0, 16)}…</span>
            <span>{Math.round((original.file_size ?? 0) / 1024)} KB</span>
            {original.duration_seconds && <span>{Math.round(original.duration_seconds)}s</span>}
            <span className="text-emerald-600">SHA-256 verified original · immutable</span>
          </p>
        </section>
      )}

      <section className="mt-8">
        <div className="flex gap-1 border-b border-stone-200">
          {(["transcript", "translation", "provenance"] as const).map((t) => (
            <button
              key={t}
              onClick={() => setActiveTab(t)}
              className={`rounded-t-lg px-4 py-2 text-sm font-semibold capitalize transition ${
                activeTab === t ? "border-b-2 border-brand bg-white text-brand-dark" : "text-stone-500 hover:text-stone-700"
              }`}
            >
              {t}
            </button>
          ))}
        </div>

        {activeTab === "transcript" && (
          <div className="rounded-b-xl border border-t-0 border-stone-200 bg-white p-6">
            {latestTranscript ? (
              <>
                <p className="text-lg leading-relaxed text-stone-800">{latestTranscript.text}</p>
                <p className="mt-3 text-xs text-stone-500">
                  {latestTranscript.language?.name ?? "Original language"} · v{latestTranscript.version} ·{" "}
                  <span className="capitalize">{latestTranscript.verification_status.replaceAll("_", " ")}</span>
                  {latestTranscript.confidence != null && ` · ${Math.round(latestTranscript.confidence * 100)}% confidence`}
                </p>
              </>
            ) : (
              <p className="text-stone-500">No transcript yet — add one from Review, or request transcription.</p>
            )}
          </div>
        )}

        {activeTab === "translation" && (
          <div className="rounded-b-xl border border-t-0 border-stone-200 bg-white p-6">
            {latestTranslation ? (
              <>
                <p className="text-lg leading-relaxed text-stone-800">{latestTranslation.text}</p>
                <p className="mt-3 text-xs text-stone-500">
                  → {latestTranslation.target_language?.name ?? "English"} ·{" "}
                  <span className="capitalize">{latestTranslation.verification_status.replaceAll("_", " ")}</span>
                </p>
              </>
            ) : (
              <p className="text-stone-500">No translation yet.</p>
            )}
          </div>
        )}

        {activeTab === "provenance" && (
          <div className="rounded-b-xl border border-t-0 border-stone-200 bg-white p-6">
            <ol className="relative space-y-4 border-l border-stone-200 pl-6">
              {obj.provenance_events.map((ev) => (
                <li key={ev.id} className="relative">
                  <span className="absolute -left-[31px] h-3 w-3 rounded-full border-2 border-brand bg-white" />
                  <p className="text-sm font-semibold capitalize text-brand-dark">
                    {ev.event_type.replaceAll("_", " ")}
                  </p>
                  {ev.description && <p className="text-sm text-stone-600">{ev.description}</p>}
                  <p className="text-xs text-stone-400">
                    {ev.actor && `${ev.actor} · `}
                    {new Date(ev.created_at).toLocaleString()}
                  </p>
                </li>
              ))}
            </ol>
            {obj.provenance_events.length === 0 && (
              <p className="text-stone-500">Provenance trail is empty for this object.</p>
            )}
          </div>
        )}
      </section>

      <section className="mt-8 grid gap-5 sm:grid-cols-2">
        <div className="rounded-2xl border border-stone-200 bg-white p-5 shadow-sm">
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-stone-500">Permissions & consent</h2>
          {obj.permissions.map((p) => (
            <ul key={p.id} className="space-y-1.5 text-sm">
              {[
                ["Preservation", p.preservation],
                ["Public access", p.public_access],
                ["Educational use", p.educational_use],
                ["AI analysis", p.ai_analysis],
                ["AI training", p.ai_training],
                ["Derivative work", p.derivative_work],
                ["Commercial use", p.commercial_use],
              ].map(([label, on]) => (
                <li key={label as string} className="flex justify-between">
                  <span className="text-stone-600">{label}</span>
                  <span className={on ? "font-semibold text-emerald-700" : "text-stone-400"}>{on ? "✓ Granted" : "—"}</span>
                </li>
              ))}
            </ul>
          ))}
          <div className="mt-4 space-y-2 border-t border-stone-100 pt-3">
            {publicPermission ? (
              <p className="text-sm font-semibold text-emerald-700">
                ✓ Public access granted — this object may be published
              </p>
            ) : user ? (
              <>
                <p className="text-xs text-stone-500">
                  Public access can only be granted by the object&apos;s creator, using the
                  creator key returned when the object was created.
                </p>
                <div className="flex gap-2">
                  <input
                    value={keyInput}
                    onChange={(e) => setKeyInput(e.target.value)}
                    placeholder={hasStoredKey ? "Creator key (from this browser)" : "Paste your creator key"}
                    className="flex-1 rounded-lg border border-stone-300 px-3 py-2 text-sm"
                  />
                  <button
                    onClick={grantPublicAccess}
                    disabled={permBusy || (!hasStoredKey && !keyInput.trim())}
                    className="rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-dark disabled:opacity-50"
                  >
                    {permBusy ? "Granting..." : "Grant access"}
                  </button>
                </div>
              </>
            ) : (
              <p className="text-xs text-stone-500">
                <Link href="/login" className="font-semibold text-accent hover:underline">Sign in</Link>{" "}
                to manage permissions and publishing for your objects.
              </p>
            )}
            {permMsg && (
              <p className={`rounded-lg px-3 py-2 text-xs ${permMsg.ok ? "bg-emerald-50 text-emerald-800" : "bg-rose-50 text-rose-700"}`}>
                {permMsg.text}
              </p>
            )}
          </div>
          <div className="mt-4 space-y-1 border-t border-stone-100 pt-3 text-xs text-stone-500">
            {obj.consents.map((c) => (
              <p key={c.id}>Consent ({c.consent_type}) · {c.consenting_party}</p>
            ))}
          </div>
        </div>

        <div className="rounded-2xl border border-stone-200 bg-white p-5 shadow-sm">
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-stone-500">Context</h2>
          <dl className="space-y-2 text-sm">
            {obj.original_language && (
              <div className="flex justify-between"><dt className="text-stone-600">Language</dt><dd>{obj.original_language.name}</dd></div>
            )}
            {obj.community && (
              <div className="flex justify-between"><dt className="text-stone-600">Community</dt><dd>{obj.community.name}</dd></div>
            )}
            {obj.place && (
              <div className="flex justify-between"><dt className="text-stone-600">Place</dt><dd>{obj.place.name}</dd></div>
            )}
            {obj.contributor && (
              <div className="flex justify-between"><dt className="text-stone-600">Contributor</dt><dd>{obj.contributor.display_name ?? (obj.contributor.anonymous ? "Anonymous" : "Unknown")}</dd></div>
            )}
          </dl>
          {obj.cultural_context && (
            <div className="mt-4 border-t border-stone-100 pt-3 text-sm text-stone-600">
              {obj.cultural_context.genre && <p><span className="font-semibold">Genre:</span> {obj.cultural_context.genre}</p>}
              {obj.cultural_context.themes && <p><span className="font-semibold">Themes:</span> {obj.cultural_context.themes}</p>}
              {obj.cultural_context.audience && <p><span className="font-semibold">Audience:</span> {obj.cultural_context.audience}</p>}
            </div>
          )}
          {obj.derivatives.length > 0 && (
            <div className="mt-4 border-t border-stone-100 pt-3">
              <p className="text-sm font-semibold text-stone-700">Derivatives ({obj.derivatives.length})</p>
              {obj.derivatives.map((d) => (
                <p key={d.id} className="mt-1 text-xs text-stone-500">
                  <span className="capitalize">{d.derivative_type}</span>
                  {d.title && <> · {d.title}</>} · <span className={d.human_reviewed ? "text-emerald-600" : "text-amber-600"}>{d.human_reviewed ? "reviewed" : "pending review"}</span>
                </p>
              ))}
            </div>
          )}
        </div>
      </section>
    </div>
  );
}