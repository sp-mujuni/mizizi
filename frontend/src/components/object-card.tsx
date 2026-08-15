import Link from "next/link";
import type { CulturalObject } from "@/lib/types";

const TYPE_LABELS: Record<string, string> = {
  story: "Story",
  song: "Song",
  riddle: "Riddle",
  proverb: "Proverb",
  poem: "Poem",
  oral_history: "Oral History",
  personal_memory: "Memory",
};

const STATUS_COLORS: Record<string, string> = {
  published: "bg-emerald-100 text-emerald-800",
  draft: "bg-stone-200 text-stone-700",
  processing: "bg-amber-100 text-amber-800",
  review: "bg-sky-100 text-sky-800",
  restricted: "bg-rose-100 text-rose-800",
  withdrawn: "bg-stone-100 text-stone-500",
};

export default function ObjectCard({ obj }: { obj: CulturalObject }) {
  return (
    <Link
      href={`/object/${obj.id}`}
      className="group flex flex-col gap-2 rounded-xl border border-stone-200 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:border-brand/40 hover:shadow-md"
    >
      <div className="flex items-start justify-between gap-2">
        <span className="rounded-full bg-brand/10 px-2.5 py-0.5 text-xs font-semibold text-brand-dark">
          {TYPE_LABELS[obj.object_type] ?? obj.object_type}
        </span>
        <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_COLORS[obj.status] ?? "bg-stone-100"}`}>
          {obj.status}
        </span>
      </div>
      <h3 className="font-serif text-lg font-semibold leading-snug text-stone-900 group-hover:text-brand-dark">
        {obj.title ?? "Untitled"}
      </h3>
      <p className="line-clamp-2 text-sm text-stone-500">{obj.description}</p>
      <div className="mt-auto flex items-center justify-between text-xs text-stone-500">
        <span className="font-mono">{obj.object_code}</span>
        <div className="flex items-center gap-2">
          {obj.original_language && <span>{obj.original_language.name}</span>}
          {obj.community && <span>· {obj.community.name}</span>}
        </div>
      </div>
    </Link>
  );
}