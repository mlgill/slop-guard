---
icon: lucide/shield-check
title: Substantial Prose Style
description: Check substantial prose and request contextual review.
---

<div class="sg-rule-page" markdown>

<header class="sg-rule-page__header sg-rule-page__header--passage">
  <div class="sg-rule-page__eyebrow">PASSAGE</div>
  <div class="sg-rule-page__titlebar">
    <h1 class="sg-rule-page__title">Substantial Prose Style</h1>
    <a class="sg-source-chip" href="https://github.com/eric-tramel/slop-guard/blob/main/src/slop_guard/rules/passage/substantial_prose_style.py"><svg class="sg-source-chip__icon" viewBox="0 0 24 24" width="14" height="14" aria-hidden="true" focusable="false"><path fill="currentColor" d="M12 .5C5.73.5.5 5.73.5 12c0 5.08 3.29 9.39 7.86 10.91.58.11.79-.25.79-.56v-2.02c-3.2.7-3.87-1.54-3.87-1.54-.52-1.32-1.28-1.67-1.28-1.67-1.05-.72.08-.7.08-.7 1.16.08 1.77 1.19 1.77 1.19 1.03 1.76 2.7 1.25 3.36.96.1-.75.4-1.25.73-1.54-2.55-.29-5.24-1.28-5.24-5.7 0-1.26.45-2.29 1.19-3.1-.12-.29-.52-1.47.11-3.06 0 0 .97-.31 3.18 1.18.92-.26 1.9-.39 2.88-.4.98.01 1.96.14 2.88.4 2.2-1.49 3.17-1.18 3.17-1.18.64 1.59.24 2.77.12 3.06.74.81 1.19 1.84 1.19 3.1 0 4.43-2.69 5.4-5.26 5.68.41.36.78 1.06.78 2.15v3.19c0 .31.21.68.8.56 4.57-1.52 7.85-5.83 7.85-10.91C23.5 5.73 18.27.5 12 .5Z"/></svg><span>source</span></a>
  </div>
  <p class="sg-rule-page__lede" markdown>Check substantial prose and request contextual review.</p>
</header>

<dl class="sg-rule-meta">
  <div class="sg-rule-meta__item"><dt>Class</dt><dd><code>SubstantialProseStyleRule</code></dd></div>
  <div class="sg-rule-meta__item"><dt>Rule name</dt><dd><code>substantial_prose_style</code></dd></div>
  <div class="sg-rule-meta__item"><dt>Count key</dt><dd><code>substantial_prose_style</code></dd></div>
</dl>

## Behavior

<table class="sg-behavior">
  <thead>
    <tr><th class="sg-behavior__th-result">Result</th><th>Input text</th><th>Why</th></tr>
  </thead>
  <tbody>
    <tr class="sg-behavior__row sg-behavior__row--flag"><td class="sg-behavior__result"><span class="sg-status sg-status--flag"><span class="sg-status__dot" aria-hidden="true"></span>Flag</span></td><td><code class="sg-behavior__input">"Bottom line: this is a game-changing solution."</code></td><td class="sg-behavior__why">Announces the conclusion and praises the work without evidence.</td></tr>
    <tr class="sg-behavior__row sg-behavior__row--pass"><td class="sg-behavior__result"><span class="sg-status sg-status--pass"><span class="sg-status__dot" aria-hidden="true"></span>Pass</span></td><td><code class="sg-behavior__input">"The report that I sent today includes the artifact provenance."</code></td><td class="sg-behavior__why">Uses ordinary grammar and contextually useful technical terms.</td></tr>
  </tbody>
</table>

## Severity

Configurable per phrase. Semantic review does not change the score. Adapted from Eric Tramel's MIT-licensed substantial prose rule in PR 125; see THIRD_PARTY_NOTICES.md for the source revision and scope of adaptation.

## Default configuration

<div class="sg-defaults">
  <div class="sg-defaults__item"><span class="sg-defaults__label">context_window_chars</span><span class="sg-defaults__value">80</span></div>
  <div class="sg-defaults__item"><span class="sg-defaults__label">min_words</span><span class="sg-defaults__value">50</span></div>
  <div class="sg-defaults__item"><span class="sg-defaults__label">penalty</span><span class="sg-defaults__value">-1</span></div>
  <div class="sg-defaults__item"><span class="sg-defaults__label">phrase_min_words</span><span class="sg-defaults__value">10</span></div>
  <div class="sg-defaults__item"><span class="sg-defaults__label">phrases</span><span class="sg-defaults__value">[&#x27;bottom line:&#x27;, &#x27;in short:&#x27;, &quot;here&#x27;s the thing&quot;, &#x27;here is the thing&#x27;, &quot;it&#x27;s worth noting&quot;, &#x27;it is worth noting&#x27;, &#x27;the simplest mental model is&#x27;, &#x27;game-changing&#x27;, &#x27;the fundamental insight&#x27;, &#x27;what you actually care about is&#x27;, &#x27;delve into&#x27;, &#x27;utilize&#x27;]</span></div>
  <div class="sg-defaults__item"><span class="sg-defaults__label">record_cap</span><span class="sg-defaults__value">8</span></div>
  <div class="sg-defaults__item"><span class="sg-defaults__label">semantic_criteria</span><span class="sg-defaults__value">[{&#x27;instruction&#x27;: &#x27;Use familiar, precise language and natural sentences. Keep technical terms when they help the reader; avoid hype, canned signposting, needless qualifiers, invented labels, and decorative rhetoric.&#x27;, &#x27;key&#x27;: &#x27;plain_language&#x27;}, {&#x27;instruction&#x27;: &#x27;Lead with the useful point or requested action. Connect evidence, reasoning, and consequences in a readable order. Remove repeated conclusions, staged questions, and unprompted contrastive framing; retain real comparisons and genuine questions when useful.&#x27;, &#x27;key&#x27;: &#x27;direct_and_connected&#x27;}, {&#x27;instruction&#x27;: &#x27;Preserve source facts, numbers, links, citations, and uncertainty. Distinguish observed results from inference and untested claims. Do not invent evidence, deadlines, commitments, or a call to action.&#x27;, &#x27;key&#x27;: &#x27;facts_and_uncertainty&#x27;}, {&#x27;instruction&#x27;: &#x27;Use paragraphs, headings, lists, and ordinary punctuation when they clarify the content. Preserve natural contractions, relative clauses, first-person updates, and meaningful dates. Prefer varied rhythm; do not rewrite grammar or technical vocabulary merely to satisfy a pattern score.&#x27;, &#x27;key&#x27;: &#x27;natural_structure&#x27;}, {&#x27;instruction&#x27;: &#x27;Judge findings in context. Rewrite from the intended meaning when useful, preserving detail needed by the reader. A clean numeric score does not complete this semantic review.&#x27;, &#x27;key&#x27;: &#x27;revision&#x27;}, {&#x27;instruction&#x27;: &#x27;Write briefly, warmly, and directly in a natural personal voice. Use contractions and first-person updates when they fit. Avoid forced enthusiasm, ritual apologies, and unnecessary formality; keep enough detail to answer the actual request.&#x27;, &#x27;key&#x27;: &#x27;audience&#x27;}]</span></div>
</div>

</div>
