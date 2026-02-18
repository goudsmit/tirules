# Twilight Imperium 4 — Rules Reference

A searchable online rules reference for [Twilight Imperium: Fourth Edition](https://www.fantasyflightgames.com/en/products/twilight-imperium-fourth-edition/), built with [Astro](https://astro.build/) and [Starlight](https://starlight.astro.build/).

Covers the base game, the *Prophecy of Kings* expansion, the *Thunder's Edge* expansion, and the *Codex* supplements.

## Tech Stack

- **[Astro 5](https://astro.build/)** — static site generator
- **[Starlight](https://starlight.astro.build/)** — documentation theme with built-in search
- **Markdown** — all rules content is authored in plain Markdown for easy editing
- **GitHub Pages** — automated deployment via GitHub Actions

## Local Development

```bash
cd astro-site
npm install
npm run dev
```

The site will be available at `http://localhost:4321`.

### Other Commands

| Command | Description |
|---|---|
| `npm run build` | Build the production site to `./dist/` |
| `npm run preview` | Preview the production build locally |

## Project Structure

```
tirules/
├── astro-site/          # The Astro/Starlight site
│   ├── src/
│   │   └── content/
│   │       └── docs/
│   │           ├── rules/        # Rules pages (Markdown)
│   │           ├── factions/     # Faction pages (Markdown)
│   │           └── components/   # Component pages (Markdown)
│   ├── astro.config.mjs
│   └── package.json
├── archive-site/        # Original PHP site (preserved for reference)
├── .github/workflows/   # GitHub Actions deployment
├── LICENSE
└── README.md
```

## Community

Have a rules question, found an inaccuracy, or want to suggest an improvement? Head over to [GitHub Discussions](https://github.com/yjmrobert/tirules/discussions) — the community forum for this project.

- **❓ Rules Questions** — Ask about specific rules interactions and edge cases
- **🎖️ Faction Interactions** — Faction-specific ability questions
- **📜 Official Rulings** — Confirmed designer rulings and errata
- **🐛 Corrections** — Report inaccuracies or outdated content
- **💡 Suggestions** — Propose improvements to the site
- **📣 Announcements** — Project updates and new content
- **💬 General** — Everything else

## Credits

This project is a fork of [tirules](https://github.com/bradleysigma/tirules) by [bradleysigma](https://github.com/bradleysigma). Huge thanks to them for doing all of the hard work of compiling, formatting, and maintaining a comprehensive rules reference for Twilight Imperium 4. Their original PHP site at [tirules.com](https://tirules.com) has been an invaluable resource for the TI4 community.

This fork rebuilds the site using Astro and Starlight to add full-text search, improve maintainability with Markdown content, and modernize the deployment pipeline.

## Archive

The original PHP site is preserved in the [`archive-site/`](archive-site/) directory for reference. It includes all of the original PHP pages, stylesheets, fonts, and the migration scripts used to convert the content to Markdown.

You can also view the source code on the `archive-tirules` branch [here](https://github.com/yjmrobert/tirules/tree/archive-tirules)

## License

This project is licensed under the [GNU General Public License v3.0](LICENSE).
