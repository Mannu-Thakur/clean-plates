---
version: alpha
name: Binance
description: A confident financial-platform interface anchored on a deep near-black canvas, where Binance's iconic yellow (#FCD535) carries every primary CTA, brand accent, and value-claim moment. Type runs Binance's custom BinanceNova / BinancePlex stack at modest weights — the system trusts size and yellow voltage over bold weight. Marketing and product surfaces default to the dark theme; transactional surfaces (buy crypto, deposit, exchange) flip to a light theme that shares the same yellow CTAs and gray-blue hairlines. Trading green (up) and red (down) accents thread through both modes for price-direction signals.

colors:
  primary: "#fcd535"
  primary-active: "#f0b90b"
  primary-disabled: "#3a3a1f"
  ink: "#181a20"
  body: "#eaecef"
  body-on-light: "#181a20"
  muted: "#707a8a"
  muted-strong: "#929aa5"
  hairline-on-light: "#eaecef"
  hairline-on-dark: "#2b3139"
  border-strong: "#cdd1d6"
  canvas-light: "#ffffff"
  canvas-dark: "#0b0e11"
  surface-card-dark: "#1e2329"
  surface-elevated-dark: "#2b3139"
  surface-soft-light: "#fafafa"
  surface-strong-light: "#f5f5f5"
  on-primary: "#181a20"
  on-dark: "#ffffff"
  trading-up: "#0ecb81"
  trading-down: "#f6465d"
  accent-turquoise: "#2dbdb6"
  info: "#3b82f6"
  info-ring: "#3b82f6"

typography:
  hero-display:
    fontFamily: "BinanceNova, -apple-system, BlinkMacSystemFont, sans-serif"
    fontSize: 64px
    fontWeight: 700
    lineHeight: 1.1
    letterSpacing: -1px
  display-lg:
    fontFamily: "BinanceNova, sans-serif"
    fontSize: 48px
    fontWeight: 700
    lineHeight: 1.1
    letterSpacing: -0.5px
  display-md:
    fontFamily: "BinanceNova, sans-serif"
    fontSize: 40px
    fontWeight: 600
    lineHeight: 1.15
    letterSpacing: -0.3px
  display-sm:
    fontFamily: "BinanceNova, sans-serif"
    fontSize: 32px
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: 0
  title-lg:
    fontFamily: "BinanceNova, sans-serif"
    fontSize: 24px
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: 0
  title-md:
    fontFamily: "BinanceNova, sans-serif"
    fontSize: 20px
    fontWeight: 600
    lineHeight: 1.35
    letterSpacing: 0
  title-sm:
    fontFamily: "BinanceNova, sans-serif"
    fontSize: 16px
    fontWeight: 600
    lineHeight: 1.4
    letterSpacing: 0
  number-display:
    fontFamily: "BinancePlex, BinanceNova, sans-serif"
    fontSize: 40px
    fontWeight: 700
    lineHeight: 1.1
    letterSpacing: -0.3px
  number-md:
    fontFamily: "BinancePlex, BinanceNova, sans-serif"
    fontSize: 16px
    fontWeight: 500
    lineHeight: 1.4
    letterSpacing: 0
  number-sm:
    fontFamily: "BinancePlex, BinanceNova, sans-serif"
    fontSize: 14px
    fontWeight: 500
    lineHeight: 1.4
    letterSpacing: 0
  body-md:
    fontFamily: "BinanceNova, sans-serif"
    fontSize: 14px
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: 0
  body-sm:
    fontFamily: "BinanceNova, sans-serif"
    fontSize: 13px
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: 0
  caption:
    fontFamily: "BinanceNova, sans-serif"
    fontSize: 12px
    fontWeight: 500
    lineHeight: 1.4
    letterSpacing: 0
  button:
    fontFamily: "BinanceNova, sans-serif"
    fontSize: 14px
    fontWeight: 600
    lineHeight: 1
    letterSpacing: 0
  nav-link:
    fontFamily: "BinanceNova, sans-serif"
    fontSize: 14px
    fontWeight: 500
    lineHeight: 1.4
    letterSpacing: 0

rounded:
  xs: 2px
  sm: 4px
  md: 6px
  lg: 8px
  xl: 12px
  pill: 9999px
  full: 9999px

spacing:
  xxs: 4px
  xs: 8px
  sm: 12px
  md: 16px
  lg: 24px
  xl: 32px
  xxl: 48px
  section: 80px

components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.button}"
    rounded: "{rounded.md}"
    padding: 12px 24px
    height: 40px
  button-primary-active:
    backgroundColor: "{colors.primary-active}"
    textColor: "{colors.on-primary}"
    rounded: "{rounded.md}"
  button-primary-disabled:
    backgroundColor: "{colors.primary-disabled}"
    textColor: "{colors.muted}"
    rounded: "{rounded.md}"
  button-primary-pill:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.button}"
    rounded: "{rounded.pill}"
    padding: 14px 32px
  button-secondary-on-dark:
    backgroundColor: "{colors.surface-card-dark}"
    textColor: "{colors.on-dark}"
    typography: "{typography.button}"
    rounded: "{rounded.md}"
    padding: 12px 24px
  button-secondary-on-light:
    backgroundColor: "{colors.canvas-light}"
    textColor: "{colors.ink}"
    typography: "{typography.button}"
    rounded: "{rounded.md}"
    padding: 12px 24px
  button-tertiary-text:
    backgroundColor: transparent
    textColor: "{colors.body}"
    typography: "{typography.button}"
  button-trading-up:
    backgroundColor: "{colors.trading-up}"
    textColor: "{colors.on-dark}"
    typography: "{typography.button}"
    rounded: "{rounded.sm}"
    padding: 8px 20px
  button-trading-down:
    backgroundColor: "{colors.trading-down}"
    textColor: "{colors.on-dark}"
    typography: "{typography.button}"
    rounded: "{rounded.sm}"
    padding: 8px 20px
---

> **Source:** https://github.com/VoltAgent/awesome-design-md/tree/main/design-md/binance
> This is the unmodified Binance DESIGN.md from the awesome-design-md repository.
> See `DESIGN.md` in this folder for the CleanPlates-adapted version.

Binance reads like a financial trading platform that wants to feel both authoritative and energetic. The base atmosphere is **deep near-black canvas** (`{colors.canvas-dark}` — #0b0e11) holding white type and a single, ubiquitous accent: **Binance Yellow** (`{colors.primary}` — #FCD535). That yellow does almost all of the brand's heavy lifting — it carries every primary CTA, every value-claim headline ("FUNDS ARE SAFU"), every "Sign Up" pill, every featured tier indicator, and the wordmark itself. There is no secondary brand color. The system trusts the yellow voltage to do the brand work, and it carries it.

Type runs Binance's custom **BinanceNova** (display + body) and **BinancePlex** (numerical / financial display) stack. BinanceNova carries display headlines, section titles, and body copy. BinancePlex appears on price tickers, large stat numbers (transaction volumes, user counts, prize pools) — anywhere a number wants to feel "tabular and reliable." Both run at modest weights — display sizes use weight 600-700 (bolder than typical marketing because trading platforms need numbers to read at a glance), body stays at 400.

The product is **multi-theme**: marketing surfaces (homepage, smart-money, futures arena) default to dark, while transactional surfaces (buy crypto, deposit, withdraw) flip to a light theme. The same yellow CTAs and gray-blue hairlines (`{colors.hairline-on-light}` — #eaecef) thread through both — only canvas, surface, and text tones flip. Trading **green** (`{colors.trading-up}` — #0ecb81) and **red** (`{colors.trading-down}` — #f6465d) signal price direction in tables, charts, and price tickers across both modes.
