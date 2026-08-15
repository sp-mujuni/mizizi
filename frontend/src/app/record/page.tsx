"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Recorder from "@/components/recorder";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Language, Community, Place, ObjectType } from "@/lib/types";

const TYPES: { value: ObjectType; label: string }[] = [
  { value: "story", label: "Story" },
  { value: "song", label: "Song" },
  { value: "riddle", label: "Riddle" },
  { value: "proverb", label: "Proverb" },
  { value: "poem", label: "Poem" },
  { value: "oral_history", label: "Oral history" },
  { value: "personal_memory", label: "Personal memory" },
  { value: "other", label: "Other" },
];

export default function RecordPage() {
  const { user, loading } = useAuth();
  const [languages, setLanguages] = useState<Language[]>([]);
  const [communities, setCommunities] = useState<Community[]>([]);
  const [places, setPlaces] = useState<Place[]>([]);

  const [type, setType] = useState<ObjectType>("story");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [languageId, setLanguageId] = useState("");
  const [communityId, setCommunityId] = useState("");
  const [placeId, setPlaceId] = useState("");
  const [source, setSource] = useState<"record" | "upload">("upload");
  const [file, setFile] = useState<File | null>(null);
  const [transcript, setTranscript] = useState("");
  const [translation, setTranslation] = useState("");

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<{
    objectCode: string;
    objectId: string;
    creatorKey: string;
  } | null>(null);

  useEffect(() => {
    api.languages().then(setLanguages).catch(() => {});
    api.communities().then(setCommunities).catch(() => {});
    api.places().then(setPlaces).catch(() => {});
  }, []);

  const backgroundLanguageIds = new Set(user?.languages.map((l) => l.id) ?? []);
  const backgroundPlaceIds = new Set(user?.places.map((p) => p.id) ?? []);
  const backgroundCommunityIds = new Set(user?.communities.map((c) => c.id) ?? []);
  const visibleLanguages = languages.filter(
    (l) => backgroundLanguageIds.has(l.id) && l.iso_639_3 !== "eng" && l.iso_639_3 !== "swa"
  );
  const visibleCommunities = communities.filter((c) => backgroundCommunityIds.has(c.id));
  const visiblePlaces = places.filter((p) => backgroundPlaceIds.has(p.id));

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const obj = await api.createObject({
        object_type: type,
        title: title || undefined,
        description: description || undefined,
        original_language_id: languageId || undefined,
        community_id: communityId || undefined,
        place_id: placeId || undefined,
      });

      if (file) {
        await api.uploadMedia(obj.id, file);
      }
      if (transcript.trim()) {
        await api.createTranscription(obj.id, {
          text: transcript.trim(),
          language_id: languageId || undefined,
          verification_status: "ai_processed",
        });
      }
      if (translation.trim()) {
        const eng = languages.find((l) => l.iso_639_3 === "eng");
        await api.createTranslation(obj.id, {
          text: translation.trim(),
          source_language_id: languageId || undefined,
          target_language_id: eng?.id,
        });
      }
      // Default consent + permissions for a community contribution.
      await api.createConsent(obj.id, {
        consenting_party: "Community contributor",
        consent_type: "preservation",
      });

      // Move the submission into the review pipeline (media upload already
      // advances draft → processing; this covers text-only contributions too).
      await api.setStatus(obj.id, "processing");

      // The creator key is returned exactly once. Persist it locally so this
      // browser remains the creator — only it can later grant public access.
      try {
        localStorage.setItem(`mizizi:creator:${obj.id}`, obj.creator_key);
      } catch {
        /* storage unavailable — the key is still shown on screen */
      }

      setResult({
        objectCode: obj.object_code,
        objectId: obj.id,
        creatorKey: obj.creator_key,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Submission failed");
    } finally {
      setBusy(false);
    }
  }

  if (loading) {
    return <p className="py-32 text-center text-stone-400">Loading…</p>;
  }

  if (!user) {
    return (
      <div className="mx-auto max-w-xl px-4 py-24 text-center">
        <h1 className="font-serif text-3xl font-bold text-brand-dark">Sign in to record</h1>
        <p className="mt-3 text-stone-600">
          Recording a story creates a permanent Cultural Object with provenance and consent. To
          keep the archive accountable, only signed-in members can record or submit material.
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

  if (result) {
    return (
      <div className="mx-auto max-w-xl px-4 py-20 text-center">
        <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-10">
          <p className="text-5xl">🌱</p>
          <h1 className="mt-4 font-serif text-3xl font-bold text-emerald-900">Preserved.</h1>
          <p className="mt-2 text-stone-600">
            Your contribution entered the archive with a permanent identity:
          </p>
          <p className="mt-4 rounded-lg bg-white px-4 py-3 font-mono text-lg text-brand-dark shadow-sm">
            {result.objectCode}
          </p>
          <div className="mt-4 rounded-xl border border-amber-300 bg-amber-50 p-4 text-left">
            <p className="text-sm font-bold text-amber-900">🔑 Your creator key — save this</p>
            <p className="mt-1 break-all rounded bg-white px-3 py-2 font-mono text-sm text-stone-700">
              {result.creatorKey}
            </p>
            <p className="mt-2 text-xs text-amber-800">
              Only the holder of this key can grant public access to this story. It is shown
              once and stored in this browser — copy it somewhere safe.
            </p>
          </div>
          <p className="mt-3 text-sm text-stone-500">
            The original recording is never altered. You can now add transcription, translation
            and permissions from the object page.
          </p>
          <Link
            href={`/object/${result.objectId}`}
            className="mt-6 inline-block rounded-lg bg-brand px-6 py-3 font-semibold text-white hover:bg-brand-dark"
          >
            Open the Cultural Object
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-10">
      <header className="mb-8 text-center">
        <h1 className="font-serif text-3xl font-bold text-brand-dark sm:text-4xl">
          Tell us what you remember
        </h1>
        <p className="mt-2 text-stone-600">
          Every contribution is preserved as a Cultural Object with provenance and consent
          recorded from the very first step.
        </p>
      </header>

      <form onSubmit={handleSubmit} className="space-y-6 rounded-2xl border border-stone-200 bg-white p-6 shadow-sm">
        <div>
          <label className="mb-1 block text-sm font-semibold text-stone-700">What are you recording?</label>
          <select value={type} onChange={(e) => setType(e.target.value as ObjectType)}
            className="w-full rounded-lg border border-stone-300 px-3 py-2.5 text-sm">
            {TYPES.map((t) => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="mb-1 block text-sm font-semibold text-stone-700">Title</label>
          <input value={title} onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g. The Hare and the Lion"
            className="w-full rounded-lg border border-stone-300 px-3 py-2.5 text-sm" />
        </div>

        <div className="grid gap-4 sm:grid-cols-3">
          <div>
            <label className="mb-1 block text-sm font-semibold text-stone-700">Language</label>
            <select value={languageId} onChange={(e) => setLanguageId(e.target.value)}
              className="w-full rounded-lg border border-stone-300 px-3 py-2.5 text-sm">
              <option value="">Select...</option>
              {visibleLanguages.map((l) => (
                <option key={l.id} value={l.id}>{l.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-sm font-semibold text-stone-700">Community</label>
            <select value={communityId} onChange={(e) => setCommunityId(e.target.value)}
              className="w-full rounded-lg border border-stone-300 px-3 py-2.5 text-sm">
              <option value="">Select...</option>
              {visibleCommunities.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-sm font-semibold text-stone-700">Place</label>
            <select value={placeId} onChange={(e) => setPlaceId(e.target.value)}
              className="w-full rounded-lg border border-stone-300 px-3 py-2.5 text-sm">
              <option value="">Select...</option>
              {visiblePlaces.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>
        </div>

        <div>
          <label className="mb-1 block text-sm font-semibold text-stone-700">
            Recording — speak naturally, or upload an audio/video file
          </label>
          <div className="mb-3 flex gap-1 rounded-lg border border-stone-200 bg-stone-50 p-1">
            {(
              [
                { value: "upload", label: "Upload file" },
                { value: "record", label: "Record live" },
              ] as const
            ).map((s) => (
              <button
                key={s.value}
                type="button"
                onClick={() => {
                  setSource(s.value);
                  setFile(null);
                }}
                className={`flex-1 rounded-md px-3 py-1.5 text-sm font-semibold transition ${
                  source === s.value ? "bg-white text-brand-dark shadow-sm" : "text-stone-500 hover:text-stone-700"
                }`}
              >
                {s.label}
              </button>
            ))}
          </div>
          {source === "record" ? (
            <Recorder onRecorded={setFile} />
          ) : (
            <input type="file" accept="audio/*,video/*"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              className="w-full rounded-lg border border-stone-300 bg-white px-3 py-2.5 text-sm" />
          )}
          {file && source === "upload" && (
            <p className="mt-1.5 text-xs text-stone-500">Selected: {file.name}</p>
          )}
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-1 block text-sm font-semibold text-stone-700">
              Transcript (original language)
            </label>
            <textarea value={transcript} onChange={(e) => setTranscript(e.target.value)}
              rows={3} placeholder="Paste or type the original-language text"
              className="w-full rounded-lg border border-stone-300 px-3 py-2.5 text-sm" />
          </div>
          <div>
            <label className="mb-1 block text-sm font-semibold text-stone-700">Translation</label>
            <textarea value={translation} onChange={(e) => setTranslation(e.target.value)}
              rows={3} placeholder="English translation"
              className="w-full rounded-lg border border-stone-300 px-3 py-2.5 text-sm" />
          </div>
        </div>

        <div>
          <label className="mb-1 block text-sm font-semibold text-stone-700">About it</label>
          <textarea value={description} onChange={(e) => setDescription(e.target.value)}
            rows={2} placeholder="When did you first hear it? From whom?"
            className="w-full rounded-lg border border-stone-300 px-3 py-2.5 text-sm" />
        </div>

        {error && <p className="rounded-lg bg-rose-50 px-4 py-2 text-sm text-rose-700">{error}</p>}

        <button type="submit" disabled={busy}
          className="w-full rounded-lg bg-brand px-6 py-3 font-semibold text-white transition hover:bg-brand-dark disabled:opacity-50">
          {busy ? "Preserving..." : "Submit to archive"}
        </button>
        <p className="text-center text-xs text-stone-400">
          By submitting you consent to preservation. Further permissions (public access, AI use)
          can be configured on the object page.
        </p>
      </form>
    </div>
  );
}