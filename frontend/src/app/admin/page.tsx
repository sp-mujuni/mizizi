"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type {
  AdminObject,
  AdminUser,
  CreatorKey,
  CreatorKeyRequest,
} from "@/lib/types";

type Tab = "users" | "objects" | "keys" | "requests";

const STATUS_STYLES: Record<string, string> = {
  draft: "bg-stone-100 text-stone-600",
  processing: "bg-sky-50 text-sky-700",
  review: "bg-amber-50 text-amber-700",
  verified: "bg-emerald-50 text-emerald-700",
  published: "bg-emerald-100 text-emerald-800",
  restricted: "bg-stone-200 text-stone-700",
  withdrawn: "bg-red-50 text-red-700",
  archived: "bg-stone-200 text-stone-700",
};

export default function AdminPage() {
  const { user, isAdmin, loading } = useAuth();
  const [tab, setTab] = useState<Tab>("users");

  const [users, setUsers] = useState<AdminUser[]>([]);
  const [objects, setObjects] = useState<AdminObject[]>([]);
  const [keys, setKeys] = useState<CreatorKey[]>([]);
  const [requests, setRequests] = useState<CreatorKeyRequest[]>([]);

  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [search, setSearch] = useState("");
  const [expanded, setExpanded] = useState<string | null>(null);

  useEffect(() => {
    if (!isAdmin) return;
    let alive = true;
    api.admin
      .users()
      .then((res) => {
        if (alive) setUsers(res.items);
      })
      .catch((err) => {
        if (alive) setError(err instanceof Error ? err.message : "Could not load users.");
      });
    return () => {
      alive = false;
    };
  }, [isAdmin]);

  useEffect(() => {
    if (!isAdmin) return;
    let alive = true;
    if (tab === "objects") {
      api.admin
        .objects(search ? { q: search } : {})
        .then((res) => {
          if (alive) setObjects(res.items);
        })
        .catch((err) => {
          if (alive) setError(err instanceof Error ? err.message : "Could not load objects.");
        });
    }
    if (tab === "keys") {
      api.admin
        .creatorKeys()
        .then((res) => {
          if (alive) setKeys(res);
        })
        .catch((err) => {
          if (alive) setError(err instanceof Error ? err.message : "Could not load creator keys.");
        });
    }
    if (tab === "requests") {
      api.admin
        .keyRequests()
        .then((res) => {
          if (alive) setRequests(res);
        })
        .catch((err) => {
          if (alive) setError(err instanceof Error ? err.message : "Could not load key requests.");
        });
    }
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAdmin, tab]);

  async function searchObjects() {
    setBusy(true);
    setError("");
    try {
      const res = await api.admin.objects(search ? { q: search } : {});
      setObjects(res.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load objects.");
    } finally {
      setBusy(false);
    }
  }

  async function refreshUsers() {
    try {
      const res = await api.admin.users();
      setUsers(res.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load users.");
    }
  }

  async function refreshObjects() {
    try {
      const res = await api.admin.objects(search ? { q: search } : {});
      setObjects(res.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load objects.");
    }
  }

  async function deleteObject(obj: AdminObject) {
    setBusy(true);
    setError("");
    try {
      const res = await api.admin.deleteObject(obj.id);
      setNotice(res.detail);
      if (tab === "users") {
        await refreshUsers();
      } else {
        await refreshObjects();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not delete the object.");
    } finally {
      setBusy(false);
    }
  }

  async function issueKey(req: CreatorKeyRequest) {
    setBusy(true);
    setError("");
    try {
      await api.admin.issueKey(req.id);
      setNotice(`Creator key emailed to ${req.user_email}.`);
      const res = await api.admin.keyRequests();
      setRequests(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not issue the key.");
    } finally {
      setBusy(false);
    }
  }

  async function declineKey(req: CreatorKeyRequest) {
    setBusy(true);
    setError("");
    try {
      await api.admin.declineKey(req.id);
      setNotice(`Key request from ${req.user_email} declined.`);
      const res = await api.admin.keyRequests();
      setRequests(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not decline the request.");
    } finally {
      setBusy(false);
    }
  }

  if (loading) return <p className="py-32 text-center text-stone-400">Loading…</p>;

  if (!user) {
    return (
      <div className="mx-auto max-w-xl px-4 py-24 text-center">
        <h1 className="font-serif text-3xl font-bold text-brand-dark">Admin console</h1>
        <p className="mt-3 text-stone-600">Sign in to access the Mizizi administration console.</p>
        <Link
          href="/login"
          className="mt-6 inline-block rounded-lg bg-brand px-6 py-3 font-semibold text-white hover:bg-brand-dark"
        >
          Sign in
        </Link>
      </div>
    );
  }

  if (!isAdmin) {
    return (
      <div className="mx-auto max-w-xl px-4 py-24 text-center">
        <h1 className="font-serif text-3xl font-bold text-brand-dark">Admin only</h1>
        <p className="mt-3 text-stone-600">
          This console is reserved for the Mizizi Administrator. You do not have access.
        </p>
        <Link
          href="/"
          className="mt-6 inline-block rounded-lg bg-brand px-6 py-3 font-semibold text-white hover:bg-brand-dark"
        >
          Back home
        </Link>
      </div>
    );
  }

  const tabs: { id: Tab; label: string; count: number }[] = [
    { id: "users", label: "Users", count: users.length },
    { id: "objects", label: "Objects", count: objects.length },
    { id: "keys", label: "Creator keys", count: keys.length },
    { id: "requests", label: "Key requests", count: requests.length },
  ];

  return (
    <div className="mx-auto max-w-6xl px-4 py-10">
      <header className="mb-6">
        <h1 className="font-serif text-3xl font-bold text-brand-dark">Admin console</h1>
        <p className="mt-2 text-stone-600">
          Manage accounts, moderate the archive, and handle creator-key requests.
        </p>
      </header>

      {notice && (
        <p className="mb-6 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
          {notice}
        </p>
      )}
      {error && (
        <p className="mb-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </p>
      )}

      <div className="mb-6 grid w-full grid-cols-2 gap-1 rounded-xl border border-stone-200 bg-white p-1 md:flex">
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`rounded-lg px-3 py-2 text-sm font-semibold transition md:flex-1 ${
              tab === t.id ? "bg-brand text-white" : "text-stone-600 hover:bg-stone-100"
            }`}
          >
            {t.label}
            <span className="ml-1.5 rounded-full bg-black/10 px-1.5 py-0.5 text-xs">{t.count}</span>
          </button>
        ))}
      </div>

      {tab === "users" && (
        <section className="space-y-3">
          {users.map((u) => (
            <div key={u.id} className="rounded-2xl border border-stone-200 bg-white p-4 shadow-sm">
              <button
                onClick={() => setExpanded(expanded === u.id ? null : u.id)}
                className="flex w-full items-center justify-between gap-3 text-left"
              >
                <div>
                  <p className="font-semibold text-stone-800">
                    {u.display_name ?? u.email}{" "}
                    <span className="ml-1 font-mono text-xs text-stone-400">{u.email}</span>
                  </p>
                  <p className="mt-0.5 text-xs text-stone-500">
                    {u.role} · joined {new Date(u.created_at).toLocaleDateString()} ·{" "}
                    {u.object_count} object{u.object_count === 1 ? "" : "s"}
                  </p>
                </div>
                <span className="text-sm text-stone-400">{expanded === u.id ? "▲" : "▼"}</span>
              </button>

              {expanded === u.id && (
                <div className="mt-4 space-y-2">
                  {u.objects.length === 0 ? (
                    <p className="rounded-lg bg-stone-50 p-3 text-sm text-stone-400">
                      This user has no objects.
                    </p>
                  ) : (
                    u.objects.map((o) => <ObjectRow key={o.id} obj={o} onDelete={deleteObject} busy={busy} />)
                  )}
                </div>
              )}
            </div>
          ))}
          {users.length === 0 && <p className="text-center text-stone-400">No users yet.</p>}
        </section>
      )}

      {tab === "objects" && (
        <section>
          <div className="mb-4 flex gap-2">
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") void searchObjects();
              }}
              placeholder="Search by title or object code…"
              className="w-full rounded-lg border border-stone-300 px-3 py-2 text-sm"
            />
            <button
              onClick={() => void searchObjects()}
              className="shrink-0 rounded-lg bg-stone-800 px-4 py-2 text-sm font-semibold text-white hover:bg-stone-900"
            >
              Search
            </button>
          </div>
          <div className="space-y-2">
            {objects.map((o) => (
              <ObjectRow key={o.id} obj={o} onDelete={deleteObject} busy={busy} />
            ))}
            {objects.length === 0 && (
              <p className="text-center text-stone-400">No objects found.</p>
            )}
          </div>
        </section>
      )}

      {tab === "keys" && (
        <section>
          <p className="mb-4 rounded-lg bg-amber-50 px-4 py-3 text-sm text-amber-800">
            The escrow ledger — a copy of every creator key, held by the Mizizi Administrator so
            contributors can recover lost keys. Only administrators can see these.
          </p>
          <div className="overflow-x-auto rounded-2xl border border-stone-200 bg-white shadow-sm">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-stone-200 bg-stone-50 text-xs uppercase tracking-wide text-stone-500">
                  <th className="px-4 py-3">Object</th>
                  <th className="px-4 py-3">Creator</th>
                  <th className="px-4 py-3">Creator key</th>
                  <th className="px-4 py-3">Escrowed</th>
                </tr>
              </thead>
              <tbody>
                {keys.map((k) => (
                  <tr key={k.id} className="border-b border-stone-100">
                    <td className="px-4 py-3">
                      <p className="font-mono text-xs text-stone-400">{k.object_code}</p>
                      <p className="font-medium text-stone-700">{k.object_title ?? "Untitled"}</p>
                    </td>
                    <td className="px-4 py-3 text-stone-600">{k.user_email ?? "—"}</td>
                    <td className="px-4 py-3">
                      <code className="rounded bg-stone-100 px-2 py-1 font-mono text-xs text-brand-dark">
                        {k.key}
                      </code>
                    </td>
                    <td className="px-4 py-3 text-xs text-stone-400">
                      {new Date(k.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
                {keys.length === 0 && (
                  <tr>
                    <td colSpan={4} className="px-4 py-8 text-center text-stone-400">
                      No keys escrowed yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {tab === "requests" && (
        <section className="space-y-3">
          {requests.map((r) => (
            <div key={r.id} className="rounded-2xl border border-stone-200 bg-white p-4 shadow-sm">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <p className="font-semibold text-stone-800">
                    {r.user_email}{" "}
                    <span className="ml-1 rounded-full bg-amber-50 px-2 py-0.5 text-xs font-semibold capitalize text-amber-700">
                      {r.status}
                    </span>
                  </p>
                  <p className="mt-0.5 font-mono text-xs text-stone-400">
                    {r.object_code} · {r.object_title ?? "Untitled"}
                  </p>
                  <p className="mt-0.5 text-xs text-stone-500">
                    requested {new Date(r.created_at).toLocaleString()}
                  </p>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => void issueKey(r)}
                    disabled={busy}
                    className="rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-white hover:bg-brand-dark disabled:opacity-50"
                  >
                    Email key to {r.user_email}
                  </button>
                  <button
                    onClick={() => void declineKey(r)}
                    disabled={busy}
                    className="rounded-lg border border-red-300 bg-red-50 px-4 py-2 text-sm font-semibold text-red-700 hover:bg-red-100 disabled:opacity-50"
                  >
                    Decline
                  </button>
                </div>
              </div>
            </div>
          ))}
          {requests.length === 0 && (
            <p className="rounded-2xl border border-dashed border-stone-300 bg-white p-8 text-center text-sm text-stone-400">
              No pending creator-key requests.
            </p>
          )}
        </section>
      )}
    </div>
  );
}

function ObjectRow({
  obj,
  onDelete,
  busy,
}: {
  obj: AdminObject;
  onDelete: (obj: AdminObject) => void;
  busy: boolean;
}) {
  const [confirming, setConfirming] = useState(false);
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-stone-200 bg-stone-50/60 px-4 py-3">
      <div className="min-w-0">
        <Link href={`/object/${obj.id}`} className="font-medium text-brand-dark hover:underline">
          {obj.title ?? "Untitled"}
        </Link>
        <p className="font-mono text-xs text-stone-400">
          {obj.object_code} · {obj.object_type}
        </p>
        {obj.user_email && <p className="text-xs text-stone-500">by {obj.user_email}</p>}
      </div>
      <div className="flex items-center gap-2">
        <span
          className={`rounded-full px-2.5 py-0.5 text-xs font-semibold capitalize ${
            STATUS_STYLES[obj.status] ?? "bg-stone-100 text-stone-600"
          }`}
        >
          {obj.status}
        </span>
        {confirming ? (
          <span className="flex items-center gap-2 rounded-lg bg-red-50 px-3 py-1 text-xs">
            <span className="text-red-700">Delete permanently?</span>
            <button
              onClick={() => onDelete(obj)}
              disabled={busy}
              className="rounded bg-red-600 px-2 py-0.5 font-semibold text-white hover:bg-red-700 disabled:opacity-50"
            >
              Yes
            </button>
            <button
              onClick={() => setConfirming(false)}
              disabled={busy}
              className="rounded border border-stone-300 px-2 py-0.5 text-stone-600 hover:bg-stone-100"
            >
              No
            </button>
          </span>
        ) : (
          <button
            onClick={() => setConfirming(true)}
            disabled={busy}
            className="rounded-lg border border-red-200 px-3 py-1 text-sm font-medium text-red-600 hover:bg-red-50 disabled:opacity-50"
          >
            Delete
          </button>
        )}
      </div>
    </div>
  );
}
