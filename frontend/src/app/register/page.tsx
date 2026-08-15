"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Community, Language, Place } from "@/lib/types";

function Chip({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-full border px-3 py-1 text-sm transition ${
        active
          ? "border-brand bg-brand text-white"
          : "border-stone-300 bg-white text-stone-600 hover:border-brand/50"
      }`}
    >
      {children}
    </button>
  );
}

export default function RegisterPage() {
  const { register } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [languageIds, setLanguageIds] = useState<string[]>([]);
  const [placeIds, setPlaceIds] = useState<string[]>([]);
  const [communityIds, setCommunityIds] = useState<string[]>([]);
  const [languages, setLanguages] = useState<Language[]>([]);
  const [places, setPlaces] = useState<Place[]>([]);
  const [communities, setCommunities] = useState<Community[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    void Promise.all([api.languages(), api.places(), api.communities()]).then(
      ([langs, plcs, comms]) => {
        setLanguages(langs);
        setPlaces(plcs);
        setCommunities(comms);
      }
    );
  }, []);

  function toggle(list: string[], set: (v: string[]) => void, id: string) {
    set(list.includes(id) ? list.filter((x) => x !== id) : [...list, id]);
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await register({
        email,
        password,
        display_name: displayName || undefined,
        language_ids: languageIds,
        place_ids: placeIds,
        community_ids: communityIds,
      });
      router.push("/account");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create your account.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-16">
      <h1 className="text-center font-serif text-3xl font-bold text-brand-dark">Join Mizizi</h1>
      <p className="mt-2 text-center text-sm text-stone-500">
        Create an account to record, review and manage cultural material. Membership keeps the
        archive accountable to the communities behind it.
      </p>

      <form onSubmit={onSubmit} className="mt-8 space-y-6 rounded-2xl border border-stone-200 bg-white p-6 shadow-sm">
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label htmlFor="display_name" className="mb-1 block text-sm font-medium text-stone-700">
              Name <span className="text-stone-400">(optional)</span>
            </label>
            <input
              id="display_name"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              className="w-full rounded-lg border border-stone-300 px-3 py-2 text-sm focus:border-brand focus:outline-none"
              placeholder="Your name"
            />
          </div>
          <div>
            <label htmlFor="email" className="mb-1 block text-sm font-medium text-stone-700">
              Email
            </label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-lg border border-stone-300 px-3 py-2 text-sm focus:border-brand focus:outline-none"
              placeholder="you@example.com"
            />
          </div>
        </div>
        <div>
          <label htmlFor="password" className="mb-1 block text-sm font-medium text-stone-700">
            Password <span className="text-stone-400">(at least 8 characters)</span>
          </label>
          <input
            id="password"
            type="password"
            required
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded-lg border border-stone-300 px-3 py-2 text-sm focus:border-brand focus:outline-none"
            placeholder="••••••••"
          />
        </div>

        <div className="rounded-xl bg-stone-50 p-4">
          <p className="text-sm font-semibold text-brand-dark">Your cultural background</p>
          <p className="mt-1 text-xs text-stone-500">
            These choices shape what you can record: you will only be able to use the languages,
            places and communities you select here.
          </p>

          <div className="mt-4">
            <p className="text-xs font-medium uppercase tracking-wide text-stone-500">
              Languages <span className="text-red-500">*</span>
            </p>
            <div className="mt-2 flex flex-wrap gap-2">
              {languages.map((l) => (
                <Chip
                  key={l.id}
                  active={languageIds.includes(l.id)}
                  onClick={() => toggle(languageIds, setLanguageIds, l.id)}
                >
                  {l.name}
                </Chip>
              ))}
            </div>
          </div>

          <div className="mt-4">
            <p className="text-xs font-medium uppercase tracking-wide text-stone-500">Places</p>
            <div className="mt-2 flex flex-wrap gap-2">
              {places.map((p) => (
                <Chip
                  key={p.id}
                  active={placeIds.includes(p.id)}
                  onClick={() => toggle(placeIds, setPlaceIds, p.id)}
                >
                  {p.name}
                </Chip>
              ))}
            </div>
          </div>

          <div className="mt-4">
            <p className="text-xs font-medium uppercase tracking-wide text-stone-500">Communities</p>
            <div className="mt-2 flex flex-wrap gap-2">
              {communities.map((c) => (
                <Chip
                  key={c.id}
                  active={communityIds.includes(c.id)}
                  onClick={() => toggle(communityIds, setCommunityIds, c.id)}
                >
                  {c.name}
                </Chip>
              ))}
            </div>
          </div>
        </div>

        {error && <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
        <button
          type="submit"
          disabled={busy || languageIds.length === 0}
          className="w-full rounded-lg bg-brand px-6 py-3 font-semibold text-white transition hover:bg-brand-dark disabled:opacity-50"
        >
          {busy ? "Creating account…" : "Create account"}
        </button>
      </form>

      <p className="mt-6 text-center text-sm text-stone-500">
        Already a member?{" "}
        <Link href="/login" className="font-semibold text-brand-dark underline">
          Sign in
        </Link>
      </p>
    </div>
  );
}