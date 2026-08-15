"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { PaginatedObjects, Language, Community } from "@/lib/types";
import ObjectCard from "@/components/object-card";

const TYPE_FILTERS = [
  { value: "", label: "All types" },
  { value: "story", label: "Stories" },
  { value: "song", label: "Songs" },
  { value: "riddle", label: "Riddles" },
  { value: "proverb", label: "Proverbs" },
];

export default function ArchivePage() {
  const [objects, setObjects] = useState<PaginatedObjects | null>(null);
  const [languages, setLanguages] = useState<Language[]>([]);
  const [communities, setCommunities] = useState<Community[]>([]);
  const [type, setType] = useState("");
  const [language, setLanguage] = useState("");
  const [community, setCommunity] = useState("");
  const [q, setQ] = useState("");

  useEffect(() => {
    api.languages().then(setLanguages).catch(() => {});
    api.communities().then(setCommunities).catch(() => {});
  }, []);

  useEffect(() => {
    api
      .listObjects({
        object_type: type || undefined,
        language: language || undefined,
        community: community || undefined,
        limit: 50,
      })
      .then(setObjects)
      .catch(() => setObjects(null));
  }, [type, language, community]);

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!q.trim()) return;
    const res = await api.search(q.trim());
    setObjects({
      items: res.results,
      total: res.total,
      limit: 50,
      offset: 0,
    });
  }

  return (
    <div className="mx-auto max-w-6xl px-4 py-10">
      <header className="mb-8">
        <h1 className="font-serif text-3xl font-bold text-brand-dark sm:text-4xl">
          The Archive
        </h1>
        <p className="mt-2 max-w-2xl text-stone-600">
          Explore Uganda&apos;s cultural memory — preserved oral heritage from communities across
          the country, with provenance and permissions recorded for every object.
        </p>
      </header>

      <form onSubmit={handleSearch} className="mb-6 flex gap-2">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search stories, songs, riddles..."
          className="flex-1 rounded-lg border border-stone-300 bg-white px-4 py-2.5 text-sm outline-none focus:border-brand"
        />
        <button
          type="submit"
          className="rounded-lg bg-brand px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-brand-dark"
        >
          Search
        </button>
      </form>

      <div className="mb-8 flex flex-wrap gap-3">
        <select
          value={type}
          onChange={(e) => setType(e.target.value)}
          className="rounded-lg border border-stone-300 bg-white px-3 py-2 text-sm"
        >
          {TYPE_FILTERS.map((t) => (
            <option key={t.value} value={t.value}>
              {t.label}
            </option>
          ))}
        </select>
        <select
          value={language}
          onChange={(e) => setLanguage(e.target.value)}
          className="rounded-lg border border-stone-300 bg-white px-3 py-2 text-sm"
        >
          <option value="">All languages</option>
          {languages
            .filter((l) => l.iso_639_3 !== "eng" && l.iso_639_3 !== "swa")
            .map((l) => (
              <option key={l.id} value={l.iso_639_3}>
                {l.name}
              </option>
            ))}
        </select>
        <select
          value={community}
          onChange={(e) => setCommunity(e.target.value)}
          className="rounded-lg border border-stone-300 bg-white px-3 py-2 text-sm"
        >
          <option value="">All communities</option>
          {communities.map((c) => (
            <option key={c.id} value={c.name}>
              {c.name}
            </option>
          ))}
        </select>
      </div>

      {objects ? (
        <>
          <p className="mb-4 text-sm text-stone-500">{objects.total} cultural object(s)</p>
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {objects.items.map((obj) => (
              <ObjectCard key={obj.id} obj={obj} />
            ))}
          </div>
          {objects.items.length === 0 && (
            <p className="rounded-xl border border-dashed border-stone-300 p-10 text-center text-stone-500">
              No objects match these filters yet.
            </p>
          )}
        </>
      ) : (
        <p className="text-stone-500">Unable to reach the Mizizi API at 127.0.0.1:8000.</p>
      )}
    </div>
  );
}