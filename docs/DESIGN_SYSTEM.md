# GrailRoster presentation system

Obsidian is a presentation layer. It does not change card IDs, catalogue data,
storage keys, authentication, collection persistence, or Supabase policies.

## Where to change the appearance

- `theme.css`: semantic colours, type scale, spacing, corners, shadows and set-cover palettes.
- `styles.css`: responsive layout and shared components. Colours reference theme tokens.
- `ui.js`: shared icons, set covers and card placeholders; no persistence or network calls.
- `index.html`: screen shell, navigation and forms.
- `app.js`: existing application behaviour, plus renderers that use the shared presentation helpers.

To change mint to another accent, edit `--accent`, `--accent-hover`,
`--accent-soft` and `--on-accent` together and check text contrast.
To create another theme, provide the same semantic tokens in another stylesheet.
Keep component selectors and DOM IDs stable so existing behaviour keeps working.
The theme colour is also mirrored in `index.html` and `manifest.json` for browser chrome.

## Components

`setCard` renders the same set tile in overview and library. `cardRow` renders
both gallery and list views; `data-layout` selects their layout. `imageMarkup`
accepts an approved image and a shared no-image treatment. `GrailUI.setCover`
and `GrailUI.cardPlaceholder` use catalogue labels, not invented product art.
All set records remain available. The two Cactus Jack releases retain separate IDs.
The home-screen recent rail shows at most eight cards. Cards from the same set
updated within thirty minutes are presented as one batch tile; the underlying
collection records remain independent and unchanged.

## Interaction and responsive rules

Desktop uses a navigation rail; mobile uses Collection, Sets, Wanted and Profile.
Profile opens the account/navigation drawer. Collection has overview and owned-card
views; Sets leads to the existing catalogue filters and checklist. Grid/list switches
are presentation-only. Ownership controls operate on the same records in both layouts.
Mobile layouts support 320px and above, safe-area insets and reduced-motion preferences.

The illustrative wrestler art, sample quantities, variant picker and share button in
the design mockups are not shipped. Variants remain a separate planned feature.
Only approved image-manifest entries are displayed. Missing images have explicit
Image pending labels. Account actions retain the established verification flows.

## Release checklist

Run `tests/smoke.cjs` against a local HTTP server using Playwright. Test mobile and
desktop layouts, searches, owned/wanted state, reload persistence, card details,
backup, auth UI, and all set tiles. Test accounts in an isolated browser context.
Never use production collection records as disposable fixtures.
Update the service worker cache version and asset list when publishing assets.
