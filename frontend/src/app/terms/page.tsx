import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Terms of Service — Mizizi",
  description: "The terms that govern the use of the Mizizi living archive of African oral culture.",
};

export default function TermsPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-12">
      <p className="text-xs font-semibold uppercase tracking-widest text-accent">
        Legal
      </p>
      <h1 className="mt-2 font-serif text-4xl font-bold text-brand-dark">Terms of Service</h1>
      <p className="mt-2 text-sm text-stone-500">
        Last updated: August 2026. These terms govern your use of the Mizizi Archive
        (“Mizizi”, “we”, “our”). By creating an account or contributing material, you agree
        to them.
      </p>

      <div className="mt-8 space-y-8 text-sm leading-relaxed text-stone-700">
        <Section title="1. The Archive and its mission">
          <p>
            Mizizi is a living archive that preserves original recordings of stories, songs,
            riddles and proverbs of African oral culture. The original recording is never
            altered. Everything an AI produces is a derivative layer on top of an immutable
            source. Cultural material remains owned and custodied by the communities that
            contributed it.
          </p>
        </Section>

        <Section title="2. Eligibility and accounts">
          <p>
            You must be at least 18 years old to create an account. You are responsible for
            keeping your credentials confidential and for everything that happens under your
            account. One account may be held by one person or cultural organization.
          </p>
        </Section>

        <Section title="3. Contributing material">
          <p>
            By submitting a recording, transcript, translation or description you confirm
            that you have the right to contribute it and that, where required, you have
            obtained the consent of the community, storytellers, performers and any other
            rights-holders. You agree to record consents truthfully and to keep evidence of
            those consents.
          </p>
          <p className="mt-3">
            Each contribution becomes a Cultural Object with a permanent identity, an
            immutable provenance trail and a creator key. The creator key is the credential
            that grants public access; a copy is escrowed with the Mizizi Administrator and
            can be recovered on request. Keep your key safe — it is the only credential that
            unlocks public access.
          </p>
        </Section>

        <Section title="4. Creator key and permissions">
          <p>
            Only the holder of the creator key (or the contributor account that created the
            object) may grant public access or otherwise change permissions. The creator key
            is stored with the Mizizi Administrator for safekeeping. If you lose it, you may
            request it and it will be emailed to your registered address after the
            Administrator confirms the request.
          </p>
        </Section>

        <Section title="5. Deleting your objects">
          <p>
            You may permanently delete Cultural Objects you created from your account. Because
            the archive is built for permanence, deletion removes the object, its media and
            its provenance trail from the archive entirely and cannot be undone. Administrators
            may also remove objects that violate these terms or archive policy.
          </p>
        </Section>

        <Section title="6. Prohibited conduct">
          <p>You agree not to use Mizizi to:</p>
          <ul className="mt-2 list-disc space-y-1 pl-6">
            <li>Upload material you do not have the right to share;</li>
            <li>Misrepresent who you are, the community, or the origin of material;</li>
            <li>Record consents falsely or without the informed agreement of rights-holders;</li>
            <li>Post hateful, unlawful or deceptive content, or material that endangers any person or community;</li>
            <li>Attempt to access accounts, keys or objects you do not own, or interfere with the archive.</li>
          </ul>
          <p className="mt-3">
            Violations may result in removal of content, suspension or termination of your
            account, and referral to relevant authorities where the law requires it.
          </p>
        </Section>

        <Section title="7. Administrator role">
          <p>
            The Mizizi Administrator administers the archive: they review applications to
            join the review circle, hold escrowed creator keys, and remove material that
            violates these terms or community policy. Administrators can view accounts and
            the objects attached to them in order to uphold the archive’s standards.
          </p>
        </Section>

        <Section title="8. Intellectual property">
          <p>
            Mizizi does not claim ownership of cultural material. Your account, and any
            material you contribute, remains yours — cultural material belongs to the
            communities that created it, per the consent records in the archive. By
            contributing you grant Mizizi the non-exclusive rights needed to preserve,
            display and make the material discoverable within the consent and permissions
            you set.
          </p>
        </Section>

        <Section title="9. Disclaimer and liability">
          <p>
            Mizizi is provided “as is”. We work to keep the archive accurate and available,
            but we do not warrant that it will be uninterrupted or error-free. To the extent
            permitted by law, we are not liable for indirect or consequential losses arising
            from your use of the archive.
          </p>
        </Section>

        <Section title="10. Changes to these terms">
          <p>
            We may update these terms from time to time. Material changes will be announced
            on the archive. Continued use of Mizizi after changes take effect constitutes
            acceptance.
          </p>
        </Section>

        <Section title="11. Contact">
          <p>
            Questions about these terms? Contact the Mizizi Administrator at{" "}
            <a href="mailto:admin@mizizi.org" className="font-medium text-accent hover:underline">
              admin@mizizi.org
            </a>
            . You can also read our{" "}
            <Link href="/privacy" className="font-medium text-accent hover:underline">
              Privacy Policy
            </Link>
            .
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
