# Launch Quality Reference

Use this after the normal Pagecraft gates when an HTML artifact, portal route,
dashboard, or public page is about to be shared, handed off, or published.

This reference adapts the useful operating ideas from
`thedaviddias/Front-End-Checklist`: category coverage, priority labels,
rule-level metadata, and evidence-first audit workflow. Do not copy the full
external corpus into Pagecraft. Pagecraft stays the local mechanics layer:
brand, layout, tables, numbers, diagrams, wrapping, and artifact verification.

## Priority Model

- **P0 blocker**: broken rendering, inaccessible core content,
  security-sensitive exposure, or compliance-sensitive failure. Fix before
  sharing.
- **P1 fix now**: major accessibility, performance, discoverability, or trust
  issue with direct evidence on the page.
- **P2 normal hardening**: good practice that should be part of the next edit
  cycle, but does not block a private/internal artifact.
- **P3 optional**: situational polish. Mention only when it is relevant to the
  page's real audience or launch surface.

Lead with P0/P1 findings. Prefer fewer, stronger findings over a long generic
list.

## Workflow

1. Classify the surface: local one-off artifact, private internal page, client
   handoff, public marketing/content page, authenticated portal, or app route.
2. Run the existing repo/design gates first: brand lint when available, then
   Pagecraft keystone and browser wrap probes, then table/number checks when
   the page contains exhibits.
3. Sweep only the launch lanes that apply. A local one-off HTML brief does not
   need SEO social cards; a public page does.
4. For every finding, record the route/file, selector or visible region, lane,
   priority, evidence, fix, and verification method.
5. If evidence is not visible in the artifact, do not invent it. Mark the gap
   `TBU` or ask for the runtime context.

## Launch Lanes

### Document Shell

- HTML5 doctype, UTF-8 charset early in the head, responsive viewport, and
  `html[lang]` are present on full documents.
- Full documents have a meaningful title. Public pages also need a meta
  description, canonical behavior, favicon path, and share-preview metadata when
  the route will be linked externally.
- IDs are unique. Navigation landmarks, `main`, sections, and headings reflect
  the actual page structure.
- Framework component snippets are not full documents; do not flag missing head
  tags unless that file owns metadata.

### Accessibility

- Heading order is navigable, visible focus states survive keyboard use, and
  interactive controls expose names and states.
- Forms have labels, useful input types, autocomplete where appropriate, and
  accessible validation messages.
- Data tables use real table semantics, header scopes or associations, captions
  or nearby context, and no table-as-layout patterns.
- Images and icons use accurate semantics: meaningful images get useful alt
  text; decorative images/icons are hidden from assistive tech.
- Contrast is checked for text, controls, icons with meaning, and focus rings.
- Persistent motion respects reduced-motion preferences.

### Layout And Performance

- Images, embeds, ads, charts, and dynamic panels reserve stable space with
  dimensions, aspect ratio, or explicit layout containers.
- Non-critical images lazy-load; critical images are prioritized deliberately.
- Scripts use `defer`, `async`, or modules unless blocking is required.
- Heavy animation sticks to transform/opacity when possible and avoids
  layout-thrashing read/write loops.
- Print/export behavior is acceptable when the artifact is likely to become a
  PDF, board packet, or offline handoff.

### Security And Privacy

- Public routes use HTTPS and do not mix insecure subresources.
- External scripts/styles are avoided when local assets are practical; CDN
  dependencies need an explicit reason and integrity or provenance review.
- `target="_blank"` links include `rel="noopener noreferrer"`.
- Debug comments, placeholder secrets, private paths, raw emails, tokens, and
  internal-only notes are absent from handoff/public HTML.
- Analytics, embeds, cookies, and forms match the privacy boundary for the
  surface. If consent or policy text is required, mark it `TBU` instead of
  inventing legal copy.

### Images And Media

- Content images have width/height or stable aspect-ratio wrappers.
- Responsive image sources are used when the same large asset would otherwise
  ship to mobile.
- Videos have posters, captions or transcript paths, and no surprise autoplay.
- Image compression and formats are appropriate for the page; do not chase
  micro-optimizations on tiny decorative assets without evidence.

### SEO And Linkability

Use this lane only for public or externally linked pages.

- One clear H1 maps to the page purpose. Link text is meaningful without only
  reading the surrounding paragraph.
- Canonical URL, robots/crawl behavior, sitemap inclusion, and redirects match
  the intended publishing state.
- Open Graph/Twitter preview metadata exists for pages likely to be shared.
- Structured data is used only when the content actually fits a known schema.
- Broken internal/external links are either fixed or called out before launch.

### Testing And Evidence

- Prefer deterministic checks first, then browser checks, then manual scans.
- Useful probes include HTML validation, axe or DevTools accessibility checks,
  Lighthouse/Web Vitals for public routes, link checking, keyboard walkthroughs,
  mobile screenshots, and Pagecraft's viewport matrix.
- Record what was actually run. "Looks good" is not verification.

## Pagecraft Rule Card Pattern

When adding a new Pagecraft rule or verifier inspired by an external checklist,
use this compact shape:

- **Title**: action-oriented, e.g. "Reserve stable space for content images".
- **Lane**: document shell, accessibility, layout/performance, security/privacy,
  images/media, SEO/linkability, or testing/evidence.
- **Priority**: P0, P1, P2, or P3 using the model above.
- **Trigger**: the concrete page pattern that activates the rule.
- **Check**: exact evidence to inspect or command/tool to run.
- **Fix**: the preferred local Pagecraft or repo-native remediation.
- **Verify**: the proof that the fix worked.
- **Exceptions**: legitimate cases that should not become findings.

Keep rule depth proportional. A simple shell rule can be five lines; a table,
form, modal, or media rule may deserve a dedicated reference or verifier.

## Conservative Audit Stance

- Do not infer business intent from a snippet alone.
- Do not treat decorative images with empty alt text as defects by default.
- Do not require public SEO metadata for private local artifacts.
- Do not demand framework head tags from a component that does not own metadata.
- Do not raise generic preference tweaks when a stronger Pagecraft issue is
  already present. Fix the root cause first.
