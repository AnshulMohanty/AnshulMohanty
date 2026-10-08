<p>
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./assets/hero-dark.svg">
  <img alt="Anshul Mohanty. Builds retrieval that cites chapter and verse; ships full-stack TypeScript; second dan black belt who breaks boards, never builds; plays badminton for the state; watches every genre. An orbit of his builds and pursuits." src="./assets/hero-light.svg">
</picture>
</p>

<p>
<a href="https://www.linkedin.com/in/anshul-mohanty-aa0361313/"><picture><source media="(prefers-color-scheme: dark)" srcset="./assets/btn-linkedin-dark.svg"><img alt="LinkedIn" src="./assets/btn-linkedin-light.svg"></picture></a>&nbsp;
<a href="https://x.com/Anshul_Som"><picture><source media="(prefers-color-scheme: dark)" srcset="./assets/btn-x-dark.svg"><img alt="Follow on X" src="./assets/btn-x-light.svg"></picture></a>&nbsp;
<a href="https://github.com/AnshulMohanty?tab=repositories"><picture><source media="(prefers-color-scheme: dark)" srcset="./assets/btn-repos-dark.svg"><img alt="All repositories" src="./assets/btn-repos-light.svg"></picture></a>
</p>

<br>

<p>
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./assets/contributions-dark.svg">
  <img alt="Contribution activity over the last twelve months: totals, and a calendar whose active days are joined in the order they happened." src="./assets/contributions-light.svg">
</picture>
</p>

<sub>Redrawn every morning by a GitHub Action in this repository.</sub>

<br>

<p>
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./assets/stack-dark.svg">
  <img alt="What I work on: AI retrieval and RAG, full-stack TypeScript, systems and data; and the languages across my repositories." src="./assets/stack-light.svg">
</picture>
</p>

<br>

**House rules.** The number I report is the number I measured, with the command printed beside it. A model may phrase the sentence; it may not touch the digits. Where the evidence is wanting, the system declines, and says precisely which check it failed.

<br>

<p>
<a href="https://github.com/AnshulMohanty/HH_Goa">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="./assets/voice-rag-dark.svg">
    <img alt="Voice RAG. Ask out loud. Get a quote, not a vibe." src="./assets/voice-rag-light.svg">
  </picture>
</a>
</p>

- The retrieval core (embed, search, confidence gate, extractive answer) measures **3.4 ms P50** against a 200 ms budget, with the benchmark command printed next to the number.
- Speech to text takes about 99% of the wall clock, so it is reported on its own line instead of being folded into the headline.
- The default answer is a verbatim span with its passage id. An opt-in Gemini pass writes prose and is discarded if it isn't grounded.

Node (ESM), Express, MiniLM on transformers.js, hnswlib, Zod, Gemini and Sarvam speech to text. [Read the write-up](https://github.com/AnshulMohanty/HH_Goa#readme)

<br>

<p>
<a href="https://github.com/AnshulMohanty/Saakshi">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="./assets/saakshi-dark.svg">
    <img alt="Saakshi. Proof, not just photos." src="./assets/saakshi-light.svg">
  </picture>
</a>
</p>

- A rule-based Trust Engine flags reused, stock, off-site and drawn-on photos, each with the reason it was flagged.
- Before and after change is measured from segmentation masks on the same frame, not estimated by a model.
- Report totals are database aggregates, so every number links back to the photos it counted. Public images are signed and face-blurred.

Built for Code Cubicle 6.0 (Cloudinary track) with Next.js, TypeScript, Cloudinary, Drizzle, PGlite with pgvector, Inngest and Leaflet. [Read the write-up](https://github.com/AnshulMohanty/Saakshi#readme)

<br>

<p>
<a href="https://github.com/AnshulMohanty/Code_Flow">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="./assets/codeflow-dark.svg">
    <img alt="CodeFlow. Maps how a codebase fits together." src="./assets/codeflow-light.svg">
  </picture>
</a>
</p>

- Eight stages, from ingest to a Q&A index, stream to the browser over server-sent events. The first six are deterministic and need no API key.
- An answer can only name a chunk id. The file path and line range come from the chunk that was actually retrieved, so a made-up line number can't be expressed.
- Import and call graphs, centrality, cycles, blast radius and Louvain communities, all computed from tree-sitter parses.

A pnpm and TypeScript monorepo: React with Vite, Express, BullMQ, Postgres with pgvector, MongoDB, Redis, and an MCP server for coding agents. [Read the write-up](https://github.com/AnshulMohanty/Code_Flow#readme)

<br>

<br>

<p>
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./assets/index-dark.svg">
  <img alt="Index of work: the pinned repositories." src="./assets/index-light.svg">
</picture>
</p>

<p>
<a href="https://github.com/AnshulMohanty/HH_Goa"><picture><source media="(prefers-color-scheme: dark)" srcset="./assets/index-01-dark.svg"><img alt="01. Voice RAG" src="./assets/index-01-light.svg"></picture></a><br>
<a href="https://github.com/AnshulMohanty/Saakshi"><picture><source media="(prefers-color-scheme: dark)" srcset="./assets/index-02-dark.svg"><img alt="02. Saakshi" src="./assets/index-02-light.svg"></picture></a><br>
<a href="https://github.com/AnshulMohanty/Code_Flow"><picture><source media="(prefers-color-scheme: dark)" srcset="./assets/index-03-dark.svg"><img alt="03. CodeFlow" src="./assets/index-03-light.svg"></picture></a><br>
<a href="https://github.com/AnshulMohanty/GradeSense"><picture><source media="(prefers-color-scheme: dark)" srcset="./assets/index-04-dark.svg"><img alt="04. GradeSense" src="./assets/index-04-light.svg"></picture></a><br>
<a href="https://github.com/AnshulMohanty/TypeAhead"><picture><source media="(prefers-color-scheme: dark)" srcset="./assets/index-05-dark.svg"><img alt="05. TypeAhead" src="./assets/index-05-light.svg"></picture></a><br>
<a href="https://github.com/AnshulMohanty/RISC-V-Instruction-Set-Explorer"><picture><source media="(prefers-color-scheme: dark)" srcset="./assets/index-06-dark.svg"><img alt="06. RISC-V Instruction Set Explorer" src="./assets/index-06-light.svg"></picture></a><br>
</p>

<br>

<p>
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./assets/karate-dark.svg">
  <img alt="Motion study of a flying side kick, yoko tobi geri: ghosted frames, three boards broken. Anshul Mohanty, black belt, 2nd dan. Breaks boards, not builds." src="./assets/karate-light.svg">
</picture>
</p>

<p>
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./assets/off-the-keyboard-dark.svg">
  <img alt="Off the keyboard: badminton, played for the state; films, every genre." src="./assets/off-the-keyboard-light.svg">
</picture>
</p>

<p>
<a href="https://github.com/AnshulMohanty?tab=repositories"><picture><source media="(prefers-color-scheme: dark)" srcset="./assets/btn-repos-dark.svg"><img alt="All repositories" src="./assets/btn-repos-light.svg"></picture></a>
</p>

<sub>Figures drawn in the style of <a href="https://hairline.lucasmarkes.com">Hairline</a> by Lucas Marques (MIT). Type: Mona Sans and Monaspace by GitHub, under the SIL Open Font License.</sub>
