"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { PaginatedObjects } from "@/lib/types";
import ObjectCard from "@/components/object-card";

export default function HomePage() {
  const [archive, setArchive] = useState<PaginatedObjects | null>(null);

  useEffect(() => {
    api.listObjects({ limit: 6, status: "published" }).then(setArchive).catch(() => setArchive(null));
  }, []);

  return (
    <div>
      <section className="border-b border-stone-200 bg-gradient-to-b from-brand/10 to-background">
        <div className="mx-auto max-w-6xl px-4 py-20 text-center sm:py-28">
          <h1 className="mx-auto mt-4 max-w-3xl font-serif text-4xl font-bold leading-tight text-brand-dark sm:text-6xl">
            What did your grandmother tell you?
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg text-stone-600">
            Preserve the stories, songs, riddles and proverbs of African oral culture —
            the original recordings, never altered — so the next generation can still hear them.
          </p>
          <div className="mt-10 flex w-full flex-col items-stretch justify-center gap-3 sm:w-auto sm:flex-row sm:items-center">
            <Link
              href="/record"
              className="rounded-lg bg-brand px-6 py-3 text-center font-semibold text-white shadow transition hover:bg-brand-dark sm:w-64"
            >
              Tell us a story
            </Link>
            <Link
              href="/archive"
              className="rounded-lg border border-brand/30 bg-white px-6 py-3 text-center font-semibold text-brand-dark transition hover:bg-brand/10 sm:w-64"
            >
              Explore Uganda&apos;s stories
            </Link>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-14">
        <div className="mb-8 flex items-end justify-between">
          <div>
            <h2 className="font-serif text-2xl font-bold text-brand-dark">Recently preserved</h2>
            <p className="mt-1 text-sm text-stone-500">
              Authenticated cultural material from the archive.
            </p>
          </div>
          <Link href="/archive" className="text-sm font-semibold text-accent hover:underline">
            Browse the archive →
          </Link>
        </div>
        {archive ? (
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {archive.items.map((obj) => (
              <ObjectCard key={obj.id} obj={obj} />
            ))}
          </div>
        ) : (
          <p className="text-stone-500">
            {archive === null
              ? "The archive is still growing..."
              : "Loading..."}
          </p>
        )}
      </section>
    </div>
  );
}