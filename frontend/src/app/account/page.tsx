"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { CulturalObject, Permission, ReviewerApplication, User } from "@/lib/types";

type PermissionField = Exclude<keyof Permission, "id">;

const PERM_FIELDS: { key: PermissionField; label: string }[] = [
  { key: "preservation", label: "Preservation (archival)" },
  { key: "public_access", label: "Public access", },
  { key: "educational_use", label: "Educational use" },
  { key: "ai_analysis", label: "AI analysis" },
  { key: "ai_training", label: "AI training" },
  { key: "derivative_work", label: "Derivative work" },
  { key: "commercial_use", label: "Commercial use" },
  { key: "voice_cloning", label: "Voice cloning" },
];

const CONSENT_TYPES = [
  "preservation",
  "public_access",
  "educational_use",
  "research",
  "ai_analysis",
  "ai_training",
  "derivative_work",
  "commercial_use",
  "voice_cloning",
];

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

export default function AccountPage() {
  const { user, isAdmin, loading } = useAuth();
  const [objects, setObjects] = useState<CulturalObject[]>([]);
  const [applications, setApplications] = useState<ReviewerApplication[]>([]);
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    try {
      const mine = await api.auth.myObjects();
      setObjects(mine);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load your contributions.");
    }
    if (isAdmin) {
      try {
        setApplications(await api.auth.listApplications());
      } catch {
        /* ignore */
      }
    }
  }

  useEffect(() => {
    if (!user) return;
    let alive = true;
    api.auth
      .myObjects()
      .then((mine) => {
        if (alive) setObjects(mine);
      })
      .catch((err) => {
        if (alive) setError(err instanceof Error ? err.message : "Could not load your contributions.");
      });
    if (isAdmin) {
      api.auth.listApplications().then((apps) => {
        if (alive) setApplications(apps);
      }).catch(() => {});
    }
    return () => {
      alive = false;
    };
  }, [user, isAdmin]);

  if (loading) return <p className="py-32 text-center text-stone-400">Loading…</p>;

  if (!user) {
    return (
      <div className="mx-auto max-w-xl px-4 py-24 text-center">
        <h1 className="font-serif text-3xl font-bold text-brand-dark">Your account</h1>
        <p className="mt-3 text-stone-600">
          Sign in to see your contributions, manage permissions and consent, and track your
          objects through the review pipeline.
        </p>
        <div className="mt-8 flex justify-center gap-3">
          <Link
            href="/login"
            className="rounded-lg bg-brand px-6 py-3 font-semibold text-white hover:bg-brand-dark"
          >
            Sign in
          </Link>
          <Link
            href="/register"
            className="rounded-lg border border-brand/30 bg-white px-6 py-3 font-semibold text-brand-dark hover:bg-brand/10"
          >
            Join Mizizi
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-10">
      <header className="mb-8">
        <h1 className="font-serif text-3xl font-bold text-brand-dark">Your account</h1>
        <div className="mt-3 flex flex-wrap items-center gap-3 text-sm">
          <span className="font-medium text-stone-700">{user.display_name ?? user.email}</span>
          <span className="rounded-full bg-brand/10 px-2.5 py-0.5 font-semibold capitalize text-brand-dark">
            {user.role.replaceAll("_", " ")}
          </span>
        </div>
        <p className="mt-2 text-sm text-stone-500">
          Cultural background:{" "}
          {[
            user.languages.map((l) => l.name).join(", ") && `Languages: ${user.languages.map((l) => l.name).join(", ")}`,
            user.places.map((p) => p.name).join(", ") && `Places: ${user.places.map((p) => p.name).join(", ")}`,
            user.communities.map((c) => c.name).join(", ") && `Communities: ${user.communities.map((c) => c.name).join(", ")}`,
          ]
            .filter(Boolean)
            .join(" · ")}
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

      <section className="mb-10">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-stone-500">
            My contributions ({objects.length})
          </h2>
          <Link
            href="/record"
            className="rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-white hover:bg-brand-dark"
          >
            + Record new
          </Link>
        </div>

        {objects.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-stone-300 bg-white p-10 text-center text-stone-500">
            You have not recorded anything yet. Your drafts and submissions will appear here.
          </div>
        ) : (
          <div className="space-y-4">
            {objects.map((obj) => (
              <ObjectCard
                key={obj.id}
                obj={obj}
                background={user}
                onNotice={setNotice}
                onError={setError}
                onChanged={load}
              />
            ))}
          </div>
        )}
      </section>

      {isAdmin && (
        <section>
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-stone-500">
            Reviewer applications ({applications.length})
          </h2>
          <div className="space-y-3">
            {applications.map((app) => (
              <div
                key={app.id}
                className="rounded-2xl border border-stone-200 bg-white p-4 shadow-sm"
              >
                <div className="flex items-center justify-between">
                  <p className="font-semibold text-stone-800">
                    {app.user_display_name ?? app.user_email}{" "}
                    <span className="ml-1 font-mono text-xs text-stone-400">{app.user_email}</span>
                  </p>
                  <span className="rounded-full bg-amber-50 px-2.5 py-0.5 text-xs font-semibold capitalize text-amber-700">
                    {app.status}
                  </span>
                </div>
                <p className="mt-2 text-sm text-stone-600">{app.statement}</p>
                {app.status === "pending" && (
                  <div className="mt-3 flex gap-2">
                    <button
                      onClick={() =>
                        void api.auth
                          .decideApplication(app.id, true)
                          .then(() => {
                            setNotice(`${app.user_email} is now a reviewer.`);
                            void load();
                          })
                          .catch((err) =>
                            setError(err instanceof Error ? err.message : "Decision failed")
                          )
                      }
                      className="rounded-lg bg-emerald-700 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-800"
                    >
                      Approve
                    </button>
                    <button
                      onClick={() =>
                        void api.auth
                          .decideApplication(app.id, false)
                          .then(() => {
                            setNotice(`Application from ${app.user_email} rejected.`);
                            void load();
                          })
                          .catch((err) =>
                            setError(err instanceof Error ? err.message : "Decision failed")
                          )
                      }
                      className="rounded-lg border border-red-300 bg-red-50 px-4 py-2 text-sm font-semibold text-red-700 hover:bg-red-100"
                    >
                      Reject
                    </button>
                  </div>
                )}
              </div>
            ))}
            {applications.length === 0 && (
              <p className="rounded-2xl border border-dashed border-stone-300 bg-white p-6 text-center text-sm text-stone-400">
                No reviewer applications yet.
              </p>
            )}
          </div>
        </section>
      )}
    </div>
  );
}

function ObjectCard({
  obj,
  background,
  onNotice,
  onError,
  onChanged,
}: {
  obj: CulturalObject;
  background: User;
  onNotice: (m: string) => void;
  onError: (m: string) => void;
  onChanged: () => void;
}) {
  const [perms, setPerms] = useState<Permission | null>(obj.permissions[0] ?? null);
  const [pubKey, setPubKey] = useState("");
  const [party, setParty] = useState("");
  const [consentType, setConsentType] = useState("public_access");
  const [check, setCheck] = useState<{ requirement: string; label: string; satisfied: boolean }[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [editing, setEditing] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [confirmRestrict, setConfirmRestrict] = useState(false);
  const [draft, setDraft] = useState({
    title: obj.title ?? "",
    description: obj.description ?? "",
    original_language_id: obj.original_language?.id ?? "",
    community_id: obj.community?.id ?? "",
    place_id: obj.place?.id ?? "",
  });

  async function saveEdit() {
    setBusy(true);
    onError("");
    try {
      const payload: {
        title?: string;
        description?: string;
        original_language_id?: string;
        community_id?: string;
        place_id?: string;
      } = {};
      if (draft.title.trim() && draft.title !== obj.title) payload.title = draft.title.trim();
      if (draft.description !== (obj.description ?? "")) payload.description = draft.description;
      if (draft.original_language_id && draft.original_language_id !== (obj.original_language?.id ?? ""))
        payload.original_language_id = draft.original_language_id;
      if (draft.community_id && draft.community_id !== (obj.community?.id ?? ""))
        payload.community_id = draft.community_id;
      if (draft.place_id && draft.place_id !== (obj.place?.id ?? "")) payload.place_id = draft.place_id;
      if (Object.keys(payload).length > 0) {
        await api.updateObject(obj.id, payload);
        onNotice("Object updated.");
      }
      setEditing(false);
      onChanged();
    } catch (err) {
      onError(err instanceof Error ? err.message : "Could not save changes.");
    } finally {
      setBusy(false);
    }
  }

  async function deleteObject() {
    setBusy(true);
    onError("");
    try {
      await api.withdraw(obj.id);
      setConfirmDelete(false);
      onNotice(`"${obj.title ?? "Untitled"}" withdrawn. It is no longer listed in the archive.`);
      onChanged();
    } catch (err) {
      onError(err instanceof Error ? err.message : "Could not withdraw this object.");
    } finally {
      setBusy(false);
    }
  }

  async function submitForReview() {
    setBusy(true);
    onError("");
    try {
      await api.setStatus(obj.id, "processing");
      onNotice("Submitted for review. Reviewers can now verify it.");
      onChanged();
    } catch (err) {
      onError(err instanceof Error ? err.message : "Could not submit for review.");
    } finally {
      setBusy(false);
    }
  }

  async function publishToArchive() {
    setBusy(true);
    onError("");
    try {
      await api.publish(obj.id);
      onNotice("Published to the public archive.");
      onChanged();
    } catch (err) {
      onError(err instanceof Error ? err.message : "Could not publish.");
    } finally {
      setBusy(false);
    }
  }

  async function restrictFromArchive() {
    setBusy(true);
    onError("");
    try {
      await api.setStatus(obj.id, "restricted");
      setConfirmRestrict(false);
      onNotice("Removed from the public archive (restricted). You can publish again any time.");
      onChanged();
    } catch (err) {
      onError(err instanceof Error ? err.message : "Could not restrict this object.");
    } finally {
      setBusy(false);
    }
  }

  async function toggle(field: PermissionField) {
    if (!perms) return;
    if (field === "public_access" && !perms.public_access) {
      onError("Granting public access needs the creator key — use the key box below.");
      return;
    }
    setBusy(true);
    onError("");
    try {
      const next = await api.setPermissions(obj.id, { [field]: !perms[field] });
      setPerms(next);
      onNotice(field === "public_access" ? "Public access revoked." : `${field.replaceAll("_", " ")} updated.`);
    } catch (err) {
      onError(err instanceof Error ? err.message : "Permission update failed");
    } finally {
      setBusy(false);
    }
  }

  async function grantPublic() {
    if (!pubKey.trim()) {
      onError("Enter the creator key to grant public access.");
      return;
    }
    setBusy(true);
    onError("");
    try {
      const next = await api.setPermissions(obj.id, { public_access: true }, pubKey.trim());
      setPerms(next);
      setPubKey("");
      onNotice("Public access granted. The community is now visible in the archive.");
    } catch (err) {
      onError(err instanceof Error ? err.message : "Could not grant public access.");
    } finally {
      setBusy(false);
    }
  }

  async function addConsent() {
    if (!party.trim()) return;
    setBusy(true);
    onError("");
    try {
      await api.createConsent(obj.id, { consenting_party: party.trim(), consent_type: consentType });
      setParty("");
      onNotice("Consent recorded.");
      onChanged();
    } catch (err) {
      onError(err instanceof Error ? err.message : "Could not record consent.");
    } finally {
      setBusy(false);
    }
  }

  async function showCheck() {
    setBusy(true);
    onError("");
    try {
      const res = await api.publishCheck(obj.id);
      setCheck(res.requirements);
    } catch (err) {
      onError(err instanceof Error ? err.message : "Could not load the checklist.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="rounded-2xl border border-stone-200 bg-white p-5 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <Link href={`/object/${obj.id}`} className="font-serif text-lg font-bold text-brand-dark hover:underline">
            {obj.title ?? "Untitled"}
          </Link>
          <p className="font-mono text-xs text-stone-400">
            {obj.object_code} · {obj.object_type}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span
            className={`rounded-full px-2.5 py-0.5 text-xs font-semibold capitalize ${STATUS_STYLES[obj.status] ?? "bg-stone-100 text-stone-600"}`}
          >
            {obj.status}
          </span>
          {obj.status !== "withdrawn" && (
            <>
              <button
                onClick={() => setEditing((v) => !v)}
                className="rounded-lg border border-stone-300 px-3 py-1 text-sm font-medium text-stone-700 hover:bg-stone-100"
              >
                {editing ? "Cancel" : "Edit"}
              </button>
              {confirmDelete ? (
                <span className="flex items-center gap-2 rounded-lg bg-red-50 px-3 py-1 text-sm">
                  <span className="text-red-700">Withdraw this object?</span>
                  <button
                    onClick={() => void deleteObject()}
                    disabled={busy}
                    className="rounded bg-red-600 px-2 py-0.5 text-xs font-semibold text-white hover:bg-red-700 disabled:opacity-50"
                  >
                    Yes
                  </button>
                  <button
                    onClick={() => setConfirmDelete(false)}
                    disabled={busy}
                    className="rounded border border-stone-300 px-2 py-0.5 text-xs text-stone-600 hover:bg-stone-100"
                  >
                    No
                  </button>
                </span>
              ) : (
                <button
                  onClick={() => setConfirmDelete(true)}
                  className="rounded-lg border border-red-200 px-3 py-1 text-sm font-medium text-red-600 hover:bg-red-50"
                >
                  Delete
                </button>
              )}
            </>
          )}
        </div>
      </div>

      {editing && (
        <div className="mt-4 rounded-xl border border-brand-light bg-brand-cream/40 p-4">
          <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-stone-500">Edit object</p>
          <div className="grid gap-3 md:grid-cols-2">
            <label className="block text-sm text-stone-700 md:col-span-2">
              Title
              <input
                value={draft.title}
                onChange={(e) => setDraft((d) => ({ ...d, title: e.target.value }))}
                className="mt-1 w-full rounded-lg border border-stone-300 px-3 py-2"
              />
            </label>
            <label className="block text-sm text-stone-700 md:col-span-2">
              Description
              <textarea
                value={draft.description}
                onChange={(e) => setDraft((d) => ({ ...d, description: e.target.value }))}
                rows={3}
                className="mt-1 w-full rounded-lg border border-stone-300 px-3 py-2"
              />
            </label>
            <label className="block text-sm text-stone-700">
              Language
              <select
                value={draft.original_language_id}
                onChange={(e) => setDraft((d) => ({ ...d, original_language_id: e.target.value }))}
                className="mt-1 w-full rounded-lg border border-stone-300 px-3 py-2"
              >
                {background.languages.map((l) => (
                  <option key={l.id} value={l.id}>
                    {l.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="block text-sm text-stone-700">
              Place
              <select
                value={draft.place_id}
                onChange={(e) => setDraft((d) => ({ ...d, place_id: e.target.value }))}
                className="mt-1 w-full rounded-lg border border-stone-300 px-3 py-2"
              >
                {background.places.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="block text-sm text-stone-700 md:col-span-2">
              Community
              <select
                value={draft.community_id}
                onChange={(e) => setDraft((d) => ({ ...d, community_id: e.target.value }))}
                className="mt-1 w-full rounded-lg border border-stone-300 px-3 py-2"
              >
                {background.communities.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <div className="mt-4 flex gap-2">
            <button
              onClick={() => void saveEdit()}
              disabled={busy}
              className="rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-white hover:bg-brand-dark disabled:opacity-50"
            >
              Save changes
            </button>
            <button
              onClick={() => setEditing(false)}
              disabled={busy}
              className="rounded-lg border border-stone-300 px-4 py-2 text-sm text-stone-600 hover:bg-stone-100"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      <div className="mt-4 grid gap-6 lg:grid-cols-2">
        <div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-stone-500">
            Permissions
          </p>
          <div className="space-y-1.5">
            {PERM_FIELDS.map(({ key, label }) => (
              <label key={key} className="flex items-center gap-2 text-sm text-stone-700">
                <input
                  type="checkbox"
                  checked={perms?.[key] ?? false}
                  disabled={busy}
                  onChange={() => void toggle(key)}
                  className="h-4 w-4 rounded accent-brand"
                />
                {label}
                {key === "public_access" && !perms?.public_access && (
                  <span className="text-xs text-amber-600">needs creator key to grant</span>
                )}
              </label>
            ))}
          </div>
          {!perms?.public_access && (
            <div className="mt-3 flex gap-2">
              <input
                value={pubKey}
                onChange={(e) => setPubKey(e.target.value)}
                placeholder="Creator key"
                className="w-full rounded-lg border border-stone-300 px-3 py-2 font-mono text-sm"
              />
              <button
                onClick={() => void grantPublic()}
                disabled={busy}
                className="shrink-0 rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-white hover:bg-brand-dark disabled:opacity-50"
              >
                Grant public
              </button>
            </div>
          )}
        </div>

        <div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-stone-500">
            Consents ({obj.consents.length})
          </p>
          <ul className="mb-3 space-y-1 text-sm text-stone-600">
            {obj.consents.map((c) => (
              <li key={c.id} className="flex justify-between gap-2 rounded-lg bg-stone-50 px-3 py-1.5">
                <span className="truncate">{c.consenting_party}</span>
                <span className="shrink-0 font-mono text-xs text-stone-400">{c.consent_type}</span>
              </li>
            ))}
            {obj.consents.length === 0 && (
              <li className="text-xs text-stone-400">No consents recorded yet.</li>
            )}
          </ul>
          <div className="flex gap-2">
            <input
              value={party}
              onChange={(e) => setParty(e.target.value)}
              placeholder="Consenting party"
              className="w-full rounded-lg border border-stone-300 px-3 py-2 text-sm"
            />
            <select
              value={consentType}
              onChange={(e) => setConsentType(e.target.value)}
              className="rounded-lg border border-stone-300 px-2 py-2 text-sm"
            >
              {CONSENT_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t.replaceAll("_", " ")}
                </option>
              ))}
            </select>
            <button
              onClick={() => void addConsent()}
              disabled={busy || !party.trim()}
              className="shrink-0 rounded-lg bg-stone-800 px-4 py-2 text-sm font-semibold text-white hover:bg-stone-900 disabled:opacity-50"
            >
              Add
            </button>
          </div>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-3 border-t border-stone-100 pt-3">
        <button
          onClick={() => void showCheck()}
          disabled={busy}
          className="text-sm font-semibold text-accent hover:underline disabled:opacity-50"
        >
          Publication checklist
        </button>
        {obj.status === "draft" && (
          <button
            onClick={() => void submitForReview()}
            disabled={busy}
            className="rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-white hover:bg-brand-dark disabled:opacity-50"
          >
            Submit for review
          </button>
        )}
        {(obj.status === "processing" || obj.status === "review") && (
          <span className="rounded-full bg-amber-50 px-3 py-1 text-xs font-medium text-amber-700">
            In the review queue
          </span>
        )}
        {obj.status === "verified" && (
          <button
            onClick={() => void publishToArchive()}
            disabled={busy}
            className="rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-white hover:bg-brand-dark disabled:opacity-50"
          >
            Publish to public archive
          </button>
        )}
        {obj.status === "published" &&
          (confirmRestrict ? (
            <span className="flex items-center gap-2 rounded-lg bg-amber-50 px-3 py-1 text-sm">
              <span className="text-amber-700">Remove from the public archive?</span>
              <button
                onClick={() => void restrictFromArchive()}
                disabled={busy}
                className="rounded bg-amber-600 px-2 py-0.5 text-xs font-semibold text-white hover:bg-amber-700 disabled:opacity-50"
              >
                Yes
              </button>
              <button
                onClick={() => setConfirmRestrict(false)}
                disabled={busy}
                className="rounded border border-stone-300 px-2 py-0.5 text-xs text-stone-600 hover:bg-stone-100"
              >
                No
              </button>
            </span>
          ) : (
            <button
              onClick={() => setConfirmRestrict(true)}
              className="rounded-lg border border-amber-300 px-4 py-2 text-sm font-medium text-amber-700 hover:bg-amber-50"
            >
              Remove from archive
            </button>
          ))}
        {check && (
          <div className="w-full rounded-xl bg-stone-50 p-3">
            {check.map((r) => (
              <p key={r.requirement} className="flex items-center gap-2 py-0.5 text-sm">
                <span className={r.satisfied ? "text-emerald-600" : "text-amber-600"}>
                  {r.satisfied ? "✓" : "•"}
                </span>
                <span className={r.satisfied ? "text-stone-600" : "text-stone-500"}>{r.label}</span>
              </p>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}