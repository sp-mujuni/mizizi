import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Privacy Policy — Mizizi",
  description: "How Mizizi collects, stores and protects your data and the cultural material in the archive.",
};

export default function PrivacyPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-12">
      <p className="text-xs font-semibold uppercase tracking-widest text-accent">
        Legal
      </p>
      <h1 className="mt-2 font-serif text-4xl font-bold text-brand-dark">Privacy Policy</h1>
      <p className="mt-2 text-sm text-stone-500">
        Last updated: August 2026. Mizizi (“we”, “our”) protects the privacy of everyone who
        uses the archive — contributors, reviewers and visitors.
      </p>

      <div className="mt-8 space-y-8 text-sm leading-relaxed text-stone-700">
        <Section title="1. Information we collect">
          <h3 className="font-semibold text-stone-800">Account information</h3>
          <p>When you create an account we collect your email address, a password (stored as a one-way hash), an optional display name, and the cultural background you choose (languages, places and communities).</p>
          <h3 className="mt-3 font-semibold text-stone-800">Contributions</h3>
          <p>Recordings, transcripts, translations, descriptions, consents and permission choices that you add as Cultural Objects, together with the metadata required for provenance (who, what, when).</p>
          <h3 className="mt-3 font-semibold text-stone-800">Usage data</h3>
          <p>Basic technical data (such as request times and error logs) used to keep the archive reliable and secure. We do not sell this data and do not use it for advertising.</p>
        </Section>

        <Section title="2. Why we process your data">
          <ul className="list-disc space-y-1 pl-6">
            <li>To run your account and let you manage your Cultural Objects;</li>
            <li>To preserve cultural material immutably and record its provenance and consent;</li>
            <li>To run the human review pipeline and administer the archive;</li>
            <li>To communicate with you about your contributions and key requests;</li>
            <li>To comply with legal obligations.</li>
          </ul>
        </Section>

        <Section title="3. Creator keys and data recovery">
          <p>
            When you create a Cultural Object, a creator key is generated. The key is the
            credential that grants public access. A copy of the key is escrowed with the
            Mizizi Administrator so it can be recovered if you lose it. If you request your
            key, it is emailed to the address registered on your account. Only the
            Administrator can access the escrow ledger.
          </p>
        </Section>

        <Section title="4. How we store and protect data">
          <p>
            Passwords are hashed using a strong, slow key-derivation function; session tokens
            are stored only as hashes; original recordings are stored immutably with a SHA-256
            checksum. Access to accounts, escrowed keys and administrative tools is restricted
            by role. We use industry-standard measures to protect data at rest and in transit.
          </p>
        </Section>

        <Section title="5. Sharing of information">
          <p>
            We do not sell your personal information. Cultural material is shared according
            to the permissions and consents you set on each object. Reviewers see material
            only within the review pipeline. We may disclose information where the law
            requires us to do so.
          </p>
        </Section>

        <Section title="6. Your rights">
          <ul className="list-disc space-y-1 pl-6">
            <li><strong>Access and correction:</strong> view and update your profile from your account;</li>
            <li><strong>Deletion:</strong> permanently delete Cultural Objects you created, which removes them from the archive;</li>
            <li><strong>Key recovery:</strong> request your escrowed creator key via the administrator;</li>
            <li><strong>Withdrawal of consent:</strong> revoke public access or other permissions at any time from your account.</li>
          </ul>
          <p className="mt-3">
            To exercise any right, contact the Mizizi Administrator at{" "}
            <a href="mailto:admin@mizizi.org" className="font-medium text-accent hover:underline">
              admin@mizizi.org
            </a>
            .
          </p>
        </Section>

        <Section title="7. Data retention">
          <p>
            Account data is retained while your account is active. Cultural material is kept
            for the life of the archive, as it is a historical record protected by consent and
            provenance. When you permanently delete an object, its media, metadata and
            provenance trail are removed from the archive.
          </p>
        </Section>

        <Section title="8. Children">
          <p>
            Mizizi is intended for users aged 18 and over. We do not knowingly collect
            personal information from children. If you believe a child has provided us with
            personal information, please contact us and we will take steps to remove it.
          </p>
        </Section>

        <Section title="9. Changes to this policy">
          <p>
            We may update this policy as the archive grows. Material changes will be announced,
            and the “last updated” date above will reflect them.
          </p>
        </Section>

        <Section title="10. Contact">
          <p>
            Questions about this policy? Contact the Mizizi Administrator at{" "}
            <a href="mailto:admin@mizizi.org" className="font-medium text-accent hover:underline">
              admin@mizizi.org
            </a>
            . Our{" "}
            <Link href="/terms" className="font-medium text-accent hover:underline">
              Terms of Service
            </Link>{" "}
            also apply.
          </p>
        </Section>
      </div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section>
      <h2 className="mb-2 font-serif text-xl font-bold text-brand-dark">{title}</h2>
      <div className="space-y-3">{children}</div>
    </section>
  );
}
