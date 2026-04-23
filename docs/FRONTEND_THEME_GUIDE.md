# Frontend Theme Guide

This guide captures the new visual foundation for the React frontend. The goal is not to redesign the product, only to align the existing screens to a more polished and scalable dark premium style.

## Core principles

- Keep structure and workflows intact. Styling should support existing functionality, not compete with it.
- Use dark surfaces with strong readability first, then add controlled accent color and glow.
- Reserve the strongest gradients for charts, active states, focused controls and KPI cards.
- Prefer spacing, hierarchy and contrast over heavy animation.

## Theme tokens

The main design tokens live in [frontend/src/styles/globals.css](C:\BizTracker\frontend\src\styles\globals.css).

- App background: `--app-bg`, `--app-bg-elevated`
- Panel surfaces: `--app-panel`, `--app-panel-strong`, `--gradient-surface`
- Primary accents: `--accent-primary`, `--accent-secondary`
- Highlight accents: `--accent-pink`, `--accent-blue`
- Text: `--text-primary`, `--text-secondary`, `--text-muted`
- Borders and separators: `--border-soft`, `--border-strong`, `--separator`
- Effects: `--shadow-panel`, `--shadow-glow`, `--gradient-button`, `--gradient-rainbow`

## Component guidelines

### Sidebar

- Keep the sidebar deep navy and slightly darker than content panels.
- Use glow only for the active item.
- Use small supporting labels, not large iconography or oversized contrast blocks.

### Cards and panels

- All main content containers should use the shared `panel` surface or the reusable `Card` component.
- Rounded corners should stay consistent and fairly generous.
- Hover states should lift slightly and brighten the border, but never become flashy.

### Buttons and filters

- Primary buttons use the purple-to-blue gradient.
- Secondary controls stay darker and flatter, with focus glow only when selected or active.
- Inputs and selects should keep subtle contrast and a clear focus ring.

### Tables

- Use soft row separators and calm hover states.
- Avoid bright white table headers or heavy cell borders.
- Keep sticky headers dark so long tables remain readable.

### Dialogs

- Reuse the same panel surface, border glow and spacing system as cards.
- Keep the content stack simple: title, short supporting copy, form/body, actions.
- Strong accent color should stay on the confirm action only.

## Chart styling recommendations

- Use purple, pink and blue gradients on the main series only.
- Keep the grid dark and low-contrast so data remains dominant.
- Tooltip background should be almost opaque dark navy with a subtle accent border.
- Secondary series should use softer blue or muted dashed lines.
- Legends should be compact and understated.

## Accessibility notes

- Maintain strong text contrast against all panel backgrounds.
- Glow should never replace focus visibility.
- Avoid low-contrast small labels on chart surfaces.
- Keep interactive targets large enough for internal desktop use and future tablet adaptation.

## Reference implementation

- Sample dashboard layout: [frontend/src/modules/analytics/pages/DashboardPage.tsx](C:\BizTracker\frontend\src\modules\analytics\pages\DashboardPage.tsx)
- Reusable primitives: [frontend/src/shared/components/ui/Card.tsx](C:\BizTracker\frontend\src\shared\components\ui\Card.tsx), [frontend/src/shared/components/ui/Button.tsx](C:\BizTracker\frontend\src\shared\components\ui\Button.tsx)
- Layout styling: [frontend/src/shared/components/layout/Sidebar.tsx](C:\BizTracker\frontend\src\shared\components\layout\Sidebar.tsx), [frontend/src/shared/components/layout/Topbar.tsx](C:\BizTracker\frontend\src\shared\components\layout\Topbar.tsx)
