<!-- BEGIN:project-rules -->

## AGENTS.md Design Rules

## 1. Ban "AI-Slop" Anti-Patterns

Never implement the following outdated design defaults:

- **Ban emoji use:** Do NOT use emojis ANYWHERE in the project. Use SVG icons when necessary.
- **Icon Overuse:** Do not use icons where they are not necessary.
- **Pure Black & White:** Never use `#000000` or `#FFFFFF` for primary backgrounds or text.
- **Default Saturated Colors:** Ban raw, highly saturated default browser colors. Rely on desaturated scales (e.g., slate, zinc, neutral).
- **Heavy Drop Shadows:** Ban generic, high-opacity, single-layer drop shadows (e.g., `box-shadow: 0 4px 8px rgba(0,0,0,0.3)`), use flat cards and panels with no shadows, do not apply shadows on hover as well, keep them flat.
- **Inconsistent Spacing:** Ban arbitrary padding values. Everything must map to a strict 8px (or 4px micro) baseline grid.
- **Inverted Layout Hierarchy:** Never place secondary elements (like feature cards) above primary hero typography.
- **Colored Left-Border Indicators:** Never use thick, colored left-borders (e.g., ::before { width: 3px; background: var(--color); }) on cards to indicate status, categories, or branding. This is a dated dashboard pattern. Drive status/branding through subtle badge backgrounds, minimal 6px status dots, or isolated icon colors instead.
- **Pastel Sidebar Slop:** Never use saturated or pastel background blocks for active sidebar menu items. Use subtle, neutral off-fills (e.g., rgba(0,0,0, 0.04)) and font-weight changes.
- **Cluttered List Dividers:** Ban harsh, full-width borders between list items. Rely on tight spacing and subtle hover backgrounds instead.

## 2. Color, Surface, and Border Architecture

Drive hierarchy through subtle color steps, opacity, and structural borders—not size alone.

- **Backgrounds:** Use rich off-blacks for dark mode (e.g., `#0A0A0A`, `#111111`) and off-whites for light mode (e.g., `#FAFAFA`, `#F7F7F8`).
- **Structural Borders:** Separate layout regions using 1px solid borders with low opacity: `rgba(255, 255, 255, 0.08)` (dark) and `rgba(0, 0, 0, 0.06)` (light).
- **Surface Treatments (Blurs):** Sticky top navbars, floating command palettes, or fixed bottom bars must enforce a glassmorphism effect using `backdrop-filter: blur(12px) saturate(150%)` combined with a translucent background (e.g., `rgba(10, 10, 10, 0.65)`). They must never float in a void without this structural anchor.

## 3. Typographic Mechanics

Implement a strict, `rem`-based scale. Rely on font-weight, color contrast, and negative tracking for hierarchy.

| Element           | Size (`rem`)          | Size (`px` eq)  | Font Weight   | Tracking  | Contrast |
| ----------------- | --------------------- | --------------- | ------------- | --------- | -------- |
| Display Hero      | `3.00rem` - `4.00rem` | `48px` - `64px` | 500 / Medium  | `-0.04em` | 100%     |
| Section Heading   | `1.50rem` - `2.00rem` | `24px` - `32px` | 500 / Medium  | `-0.02em` | 90%      |
| UI Body / Data    | `0.875rem`            | `14px`          | 400 / Regular | `0em`     | 70%      |
| UI Micro / Labels | `0.750rem`            | `12px`          | 500 / Medium  | `0.02em`  | 50%      |

## 4. Component Geometry, CTAs & Form Architecture

Form elements must feel tactile, precise, and structurally integrated.

- **Border Radii:** Enforce nesting-aware border radii. Outer container = `12px`, inner element = `8px`. Use `6px` for small form inputs and interactive badges.
- **High-Contrast CTAs:** Primary Call-to-Action buttons must drive user action, not camouflage into the background. In dark mode, primary buttons must be high-contrast (e.g., solid `#EDEDED` background with `#111111` text).
- **Card Padding Balance:** Vertical and horizontal padding inside cards must be mathematically balanced (e.g., uniformly `24px` or `padding: 24px 20px`). Do not leave awkward vertical dead space at the bottom of containers.
- **Input Borders:** Default inputs must use a subtle border `1px solid rgba(255, 255, 255, 0.12)` with a solid structural background (e.g., `rgba(255, 255, 255, 0.03)`).
- **Custom Focus Rings:** Ban default browser outlines. Implement crisp, offset focus rings using box-shadow: `box-shadow: 0 0 0 2px var(--bg-color), 0 0 0 4px rgba(139, 92, 246, 0.6);`.

## 5. Micro-Interactions & Animation

Animations must feel snappy, mechanical, and intentional. Never use slow or linear fades for interactivity.

- **Hover States:** Fast and immediate. `transition: all 100ms ease-out;`
- **State Changes (Modals, Popovers, Drawers):** Smooth, spring-like decelerations. `transition: all 250ms cubic-bezier(0.16, 1, 0.3, 1);`
- **Transforms:** Scale interactive cards or buttons down slightly on click (`transform: scale(0.98)`), never scale them up on hover.

## 6. SaaS Data Density

Information-heavy views (tables, lists, logs) must prioritize scannability over padding.

- **Row Height:** Cap table rows and list items at a dense `32px` to `40px` height.
- **Hover States:** Do not use borders for row hovers. Use a subtle, full-bleed background fill: `background: rgba(255, 255, 255, 0.04);` with a `border-radius: 6px`.
- **Data Alignment:** Always right-align numeric data and monospaced values. Left-align text. Use `tabular-nums` for all dynamic metrics.
- **List Separators:** Do not use internal borders (border-bottom) between standard list items or alerts. Separate items using strict 8px/12px grid spacing.

## 7. Macro-Architecture & Layout Composition

The top-level arrangement of elements must follow logical user acquisition flows.

- **Above the Fold Priority:** The primary value proposition (Display Hero typography) and primary CTA must sit above the fold. Secondary layouts, like feature card grids, must follow below the hero section.
- **Structural Anchors:** Elements like sidebars and top navbars must span flush to their respective viewport edges.

## 8. Viewport & Responsive Mechanics

UIs must seamlessly adapt physical geometry between viewports, shifting drastically to accommodate touch ergonomics.

| Mechanic              | Desktop State (`> 768px`)                        | Mobile State (`< 768px`)                                        |
| --------------------- | ------------------------------------------------ | --------------------------------------------------------------- |
| **Touch Targets**     | Standard `32px` minimum height                   | Strict `44x44px` minimum for all interactive elements           |
| **Grid/Flex Layout**  | Horizontal rows (`flex-row`), multi-column grids | Stacked columns (`flex-col`), 1-column grids                    |
| **Button Sizing**     | Auto-width based on text content                 | `100%` width for all primary actions                            |
| **Container Padding** | `32px` to `64px` inline padding                  | `16px` strict inline padding to screen edge                     |
| **Modals**            | Centered dialog boxes with backdrop              | Bottom-anchored sliding sheets (`border-radius: 16px 16px 0 0`) |

<!-- END:project-rules -->
