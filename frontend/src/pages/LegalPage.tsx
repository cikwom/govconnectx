import { Link, useLocation } from "react-router-dom";

type LegalSection = { id: string; title: string; paragraphs?: string[]; bullets?: string[] };

const terms: LegalSection[] = [
  { id: "about", title: "1. About GovConnect Nigeria", paragraphs: [
    "GovConnect Nigeria (also referred to as “GovConnectX”, “GovConnect”, “we”, “us” or “the platform”) provides a digital channel through which people can submit civic and public-service reports and, where the relevant workflow is available, follow their progress.",
    "GovConnect is not an emergency-response service. It is not a government ministry, department, agency, or elected office, and it must not be understood as speaking for or acting on behalf of any public institution unless a specific partnership or authorisation is formally announced. The platform does not guarantee that a report will be accepted, investigated, resolved, or acted upon by a public authority."
  ]},
  { id: "eligibility", title: "2. Eligibility and your account", paragraphs: [
    "You must provide accurate registration information, keep your sign-in credentials confidential, and use only an account that belongs to you. You are responsible for activity carried out through your account. Tell us promptly if you believe your account has been accessed without permission.",
    "Public registration creates a citizen account. Access to official, departmental, supervisory, and administrator functions is restricted and must be granted by an authorised platform administrator. Do not claim an official role you have not been assigned."
  ]},
  { id: "acceptable-use", title: "3. Acceptable use and reporting standards", paragraphs: [
    "Use GovConnect lawfully, respectfully, and for genuine civic or public-service concerns. Submit information honestly and, as far as reasonably possible, distinguish what you personally observed from what another person told you."
  ], bullets: [
    "Do not knowingly submit false, fabricated, misleading, malicious, or deliberately duplicated reports.",
    "Do not threaten, harass, defame, impersonate, discriminate against, or unlawfully expose another person.",
    "Do not upload unlawful, abusive, sexually exploitative, violent, or otherwise prohibited material.",
    "Do not publish another person’s personal information unless it is genuinely necessary for the report and you have a lawful basis to provide it.",
    "Do not attempt to access another user’s account, bypass access controls, interfere with the service, introduce malware, scrape restricted information, or disrupt platform operations.",
    "Do not use the platform to make threats, incite violence, or carry out fraud or other unlawful activity."
  ]},
  { id: "reports", title: "4. Reports, evidence and public officials", paragraphs: [
    "You retain any rights you have in material you submit. By submitting a report or attachment, you give GovConnect permission to host, reproduce, review, and share that material only as reasonably necessary to operate the reporting workflow, investigate the concern, maintain platform records, and route the report to an appropriate authorised department or official.",
    "A report may contain allegations about people, organisations, or public bodies. Submission does not establish that an allegation is true. Reports should be reviewed fairly and handled by authorised personnel. Do not use GovConnect as a substitute for contacting emergency services or law enforcement where immediate intervention is needed.",
    "Only upload evidence you are entitled to share. Avoid uploading identity documents, bank details, passwords, medical records, or other highly sensitive information unless the platform specifically requests it through a secure and appropriate process."
  ]},
  { id: "review", title: "5. Review, moderation and account restrictions", paragraphs: [
    "We may review reports and account activity to protect users, maintain service integrity, and address suspected misuse. Where appropriate, reports may be corrected, restricted, referred, or removed, and accounts may be limited or suspended. We aim to consider relevant context and provide a reasonable explanation where doing so is lawful and safe.",
    "A platform status, automated flag, or administrative review indicator is not by itself proof that a person has acted improperly or that a report is false."
  ]},
  { id: "availability", title: "6. Service availability and changes", paragraphs: [
    "We may update, suspend, or discontinue parts of GovConnect for maintenance, security, legal, operational, or funding reasons. We do not promise uninterrupted availability, permanent storage, or a particular response time. Until durable production storage and backup arrangements are confirmed, do not treat the platform as the sole or permanent repository for important evidence or records."
  ]},
  { id: "privacy", title: "7. Privacy and personal information", paragraphs: [
    "Our Privacy Notice explains the categories of information the platform handles, why it is used, how reports and attachments may be shared within the reporting workflow, and the rights available under applicable Nigerian data-protection law. Please read it before creating an account or submitting a report."
  ]},
  { id: "liability", title: "8. Disclaimers and liability", paragraphs: [
    "To the extent permitted by applicable law, GovConnect is provided on an “as available” basis. We do not warrant that user-submitted information is accurate, that a public institution will respond, or that a report will produce a particular outcome. Nothing in these Terms excludes a right or liability that cannot lawfully be excluded under Nigerian law.",
    "You remain responsible for the content you submit and for using appropriate official channels when a matter is urgent, legally sensitive, or requires immediate assistance."
  ]},
  { id: "law", title: "9. Governing law and disputes", paragraphs: [
    "These Terms are intended to be interpreted in accordance with the laws of the Federal Republic of Nigeria. We encourage users to raise concerns with the platform team first so that they can be reviewed. This does not prevent a user from approaching a competent regulator or court where the law allows."
  ]},
  { id: "changes", title: "10. Changes to these Terms", paragraphs: [
    "We may revise these Terms as the service, its safeguards, or applicable law changes. The “Last updated” date on this page will show when the current version was published. Material changes should be brought to users’ attention through an appropriate platform notice."
  ]},
];

const privacy: LegalSection[] = [
  { id: "controller", title: "1. Who is responsible", paragraphs: [
    "This notice applies to GovConnect Nigeria (GovConnectX). The legal name and address of the person or organisation operating the platform, and a dedicated privacy contact, must be confirmed and published before the service is opened for unrestricted public use. GovConnect must not be represented as a Nigerian government institution without documented authority to do so."
  ]},
  { id: "information", title: "2. Information the platform handles", paragraphs: [
    "Depending on how you use the service, the application is designed to handle the following information:"
  ], bullets: [
    "Account information: your name, email address, password hash, account role, account status, and account creation details. The application stores a password hash rather than your readable password.",
    "Report information: report title, description, category, location coordinates, optional address, status, timestamps, and the account associated with the report.",
    "Evidence and attachments: file name, file type, file size, file checksum, upload time, and the file itself.",
    "Workflow information: department assignment, assigned official, report status history, comments, and notifications where those features are used.",
    "Technical and security information: information needed to authenticate requests, protect accounts, diagnose errors, and maintain the service. The browser client currently keeps its short-lived sign-in token in local storage."
  ]},
  { id: "purposes", title: "3. Why information is used", paragraphs: [
    "Information is used to create and secure accounts, receive and manage civic reports, identify relevant locations, route reports to authorised personnel, communicate report progress within the application, investigate misuse, maintain service security, and meet applicable legal obligations.",
    "We aim to collect only information that is relevant and reasonably necessary for these purposes. Do not include sensitive personal details about yourself or another person unless they are necessary for the report."
  ]},
  { id: "lawful-basis", title: "4. Legal basis for processing", paragraphs: [
    "The Nigeria Data Protection Act 2023 requires a valid lawful basis for each processing purpose. Depending on the actual service arrangement and the facts of a particular report, a lawful basis may include steps requested by the user, a legitimate interest that does not override the person’s rights, consent where genuinely appropriate, a legal obligation, vital interests, or a task carried out in the public interest by an entity legally authorised to do so.",
    "GovConnect must identify and document the specific lawful basis for each purpose before public launch. The platform must not assume that every report is automatically processed on a public-interest or government-authority basis."
  ]},
  { id: "sharing", title: "5. When information may be shared", paragraphs: [
    "A report and relevant evidence may be made available to authorised platform administrators and, where the workflow supports it, the department or official assigned to review that report. Information may also be processed by infrastructure or service providers that help host, secure, or operate the platform, subject to appropriate safeguards and contractual controls.",
    "We do not sell personal information. We do not publish private account credentials. Any disclosure required by law, court order, or a valid request from a competent authority must be assessed and handled in accordance with applicable law.",
    "Before public launch, the operator must document the actual hosting, file-storage, email, analytics (if any), and other service providers, including relevant processing locations and any cross-border transfer safeguards."
  ]},
  { id: "retention", title: "6. Storage, security and retention", paragraphs: [
    "The application uses a configured backend database for account and report records and a separate file-storage location for attachments. The current code can fall back to a local SQLite database when no DATABASE_URL is configured, and attachments use local filesystem storage. On hosting services with an ephemeral filesystem, local files may not survive a restart or redeployment.",
    "Durable production database hosting, private persistent attachment storage, tested backups, a documented retention schedule, and a tested recovery process must be completed before relying on GovConnect for important public records. We do not publish a fixed retention period until the operator has approved a records-retention schedule.",
    "We use password hashing, role-based access checks, and authenticated access controls in the application. These measures do not mean that every form of data is encrypted at rest or that the platform has completed an independent security audit. Do not submit information that would create an unacceptable risk if exposed."
  ]},
  { id: "rights", title: "7. Your data-protection rights", paragraphs: [
    "Subject to the conditions and exceptions in the Nigeria Data Protection Act 2023, you may have rights to be informed, request access to personal data, seek correction, request erasure, restrict or object to certain processing, request data portability, and withdraw consent where consent is the basis relied upon. You may also lodge a complaint with the Nigeria Data Protection Commission.",
    "A dedicated privacy-request email address and process must be published by the platform operator before public launch. Until then, this notice does not provide a verified channel for submitting a formal data-subject request."
  ]},
  { id: "children", title: "8. Children and vulnerable people", paragraphs: [
    "The platform is intended for people who can lawfully create and manage their own account. Do not create an account for another person or submit a child’s personal information unless you are legally authorised and the information is necessary for a legitimate reporting purpose. Reports involving children or vulnerable people require particular care and should avoid unnecessary identifying details."
  ]},
  { id: "cookies", title: "9. Cookies and browser storage", paragraphs: [
    "The current frontend uses browser local storage to remember the sign-in token and the selected display theme. The sign-in token is sensitive: use a trusted device, protect your device account, and sign out when using a shared computer. The platform should disclose any additional analytics, tracking, or cookie technologies before they are introduced."
  ]},
  { id: "updates", title: "10. Updates and contact", paragraphs: [
    "We may update this notice when the platform or its data practices change. The “Last updated” date identifies the current version. Before unrestricted public launch, the platform operator must publish its legal identity, service address, privacy contact, retention schedule, and the actual list or categories of service providers and processing locations."
  ]},
];

export default function LegalPage() {
  const location = useLocation();
  const isPrivacy = location.pathname === "/privacy";
  const sections = isPrivacy ? privacy : terms;
  const title = isPrivacy ? "Privacy Notice" : "Terms of Use";
  const intro = isPrivacy
    ? "A clear explanation of how GovConnect handles account details, civic reports and supporting evidence."
    : "The rules for using GovConnect responsibly, safely and respectfully.";
  return (
    <main className="legal-page">
      <header className="legal-topbar">
        <Link className="brand" to="/"><span className="brand-mark">G</span><span>GovConnect<span className="brand-light"> Nigeria</span></span></Link>
        <nav aria-label="Legal navigation"><Link to="/terms" aria-current={!isPrivacy ? "page" : undefined}>Terms of Use</Link><Link to="/privacy" aria-current={isPrivacy ? "page" : undefined}>Privacy Notice</Link><Link className="legal-home-link" to="/">Back to home</Link></nav>
      </header>
      <section className="legal-hero">
        <p className="eyebrow">GOVCONNECT NIGERIA · PLATFORM INFORMATION</p>
        <h1>{title}</h1>
        <p>{intro}</p>
        <div className="legal-meta"><span>Last updated: 9 November 2026</span><span>Applies to GovConnect Nigeria (GovConnectX)</span></div>
      </section>
      <div className="legal-layout">
        <aside className="legal-toc"><p>ON THIS PAGE</p>{sections.map((section) => <a key={section.id} href={`#${section.id}`}>{section.title}</a>)}<div className="legal-switch"><span>Also read</span><Link to={isPrivacy ? "/terms" : "/privacy"}>{isPrivacy ? "Terms of Use →" : "Privacy Notice →"}</Link></div></aside>
        <article className="legal-content">
          {sections.map((section) => <section id={section.id} key={section.id}><h2>{section.title}</h2>{section.paragraphs?.map((paragraph) => <p key={paragraph}>{paragraph}</p>)}{section.bullets && <ul>{section.bullets.map((bullet) => <li key={bullet}>{bullet}</li>)}</ul>}</section>)}
          <div className="legal-review-note"><strong>Important launch note</strong><p>These pages are a product and compliance starting point, not a legal opinion or proof of regulatory compliance. The platform operator’s legal identity, privacy contact, retention schedule, hosting and transfer details, and any public-sector authorisations must be verified and completed with qualified Nigerian legal and data-protection advice before unrestricted public launch.</p></div>
        </article>
      </div>
      <footer className="legal-footer"><Link className="brand" to="/"><span className="brand-mark">G</span><span>GovConnect<span className="brand-light"> Nigeria</span></span></Link><span>Citizen reporting. Clear information. Responsible use.</span><span>© {new Date().getFullYear()} GovConnect Nigeria</span></footer>
    </main>
  );
}
