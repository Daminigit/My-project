---
name: Crimson Neural Aesthetic
colors:
  surface: '#131313'
  surface-dim: '#131313'
  surface-bright: '#393939'
  surface-container-lowest: '#0e0e0e'
  surface-container-low: '#1c1b1b'
  surface-container: '#201f1f'
  surface-container-high: '#2a2a2a'
  surface-container-highest: '#353534'
  on-surface: '#e5e2e1'
  on-surface-variant: '#e4bebc'
  inverse-surface: '#e5e2e1'
  inverse-on-surface: '#313030'
  outline: '#ab8987'
  outline-variant: '#5b403f'
  surface-tint: '#ffb3b1'
  primary: '#ffb3b1'
  on-primary: '#680011'
  primary-container: '#ff535a'
  on-primary-container: '#5b000e'
  inverse-primary: '#bb162c'
  secondary: '#fff9ef'
  on-secondary: '#3a3000'
  secondary-container: '#ffdb3c'
  on-secondary-container: '#725f00'
  tertiary: '#c8c6c5'
  on-tertiary: '#303030'
  tertiary-container: '#929090'
  on-tertiary-container: '#2a2a2a'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#ffdad8'
  primary-fixed-dim: '#ffb3b1'
  on-primary-fixed: '#410007'
  on-primary-fixed-variant: '#92001c'
  secondary-fixed: '#ffe16d'
  secondary-fixed-dim: '#e9c400'
  on-secondary-fixed: '#221b00'
  on-secondary-fixed-variant: '#544600'
  tertiary-fixed: '#e5e2e1'
  tertiary-fixed-dim: '#c8c6c5'
  on-tertiary-fixed: '#1b1b1c'
  on-tertiary-fixed-variant: '#474746'
  background: '#131313'
  on-background: '#e5e2e1'
  surface-variant: '#353534'
typography:
  display-lg:
    fontFamily: Outfit
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Outfit
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Outfit
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 36px
  title-md:
    fontFamily: Outfit
    fontSize: 20px
    fontWeight: '500'
    lineHeight: 28px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-caps:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '700'
    lineHeight: 16px
    letterSpacing: 0.05em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  container-max: 1280px
  gutter: 24px
  margin-mobile: 16px
  stack-sm: 8px
  stack-md: 16px
  stack-lg: 32px
---

## Brand & Style

This design system is engineered for a premium, AI-driven culinary discovery experience. The brand personality is sophisticated, intelligent, and appetizing, blending the urgency of hunger with the precision of machine learning. 

The aesthetic direction is **Glassmorphic-Modern**, characterized by deep obsidian surfaces, vibrant crimson accents, and translucent layers. It leverages high-contrast typography and subtle light-leak effects to evoke a high-end "nightlife" or "exclusive club" atmosphere. The user interface prioritizes depth and luminosity, using glow effects to signify AI-driven insights and premium restaurant rankings.

## Colors

The palette centers on a "Deep Dark" foundation to allow the food imagery and AI recommendations to pop. 

- **Primary (Zomato Red):** Used for primary actions, branding, and highlighting "AI Recommended" states.
- **Secondary (Gold):** Specifically reserved for high-tier restaurant rankings, Michelin stars, and "Top Choice" badges.
- **Surface Strategy:** Backgrounds utilize `#121212`, while elevated containers use `#1E1E1E`. 
- **Glassmorphism:** Interactive cards and overlays use a semi-transparent surface with a 12px backdrop-blur to maintain context and depth.

## Typography

The system utilizes **Outfit** for headlines to provide a modern, geometric feel with high character. **Inter** is used for body text and technical data to ensure maximum legibility and a systematic appearance.

- **Contrast:** Maintain high contrast for primary information (White) and lower contrast for metadata (Soft Gray).
- **Hierarchy:** Use the `label-caps` style for category tags (e.g., "CUISINE", "DISTANCE") to create a clear structural distinction from content.

## Layout & Spacing

This design system uses a **Fluid Grid** model with a 12-column structure for desktop and a single-column stack for mobile. 

- **Grid:** 12 columns with 24px gutters.
- **Margins:** 24px on desktop; 16px on mobile devices.
- **Rhythm:** An 8px linear scale drives all padding and margin decisions. 
- **AI Feed:** Restaurant recommendation cards should span 4 columns on desktop (3-up) and full width on mobile. Use asymmetrical layouts for "Feature Stories" or "Chef's Picks" to break the grid and add editorial flair.

## Elevation & Depth

Depth is achieved through **Glassmorphism** and **Tonal Layering** rather than traditional heavy shadows.

- **Base Level:** `#121212` background.
- **Surface Level:** `#1E1E1E` for cards, with a 1px solid `rgba(255,255,255,0.1)` border to define edges against the dark background.
- **Floating Level:** Glassmorphic containers with a 12px backdrop-blur and a subtle `0px 8px 32px rgba(0,0,0,0.4)` shadow.
- **AI Glow:** Critical AI components or selected states feature a soft outer glow using the primary crimson color (`rgba(226, 55, 68, 0.2)`) with a 20px spread.

## Shapes

The design uses a generous **Rounded** (16px) corner radius to soften the high-tech aesthetic and make the food-centric UI feel more approachable.

- **Standard Components:** 16px (`rounded-lg`) for cards, input fields, and modal containers.
- **Small Elements:** 8px (`rounded-sm`) for chips and small tags.
- **Buttons:** 12px or fully pill-shaped (for CTA "Order Now" buttons).

## Components

### Buttons
- **Primary:** Solid `#E23744` with white text. On hover, apply a `0px 0px 15px rgba(226, 55, 68, 0.5)` glow.
- **Secondary:** Transparent with a 1px `rgba(255,255,255,0.2)` border. Glass background on hover.

### Restaurant Cards
- Glassmorphic footer area for text content.
- High-quality imagery with a subtle dark-to-transparent gradient overlay at the bottom to ensure text readability.
- Gold rank indicator in the top-right corner with a soft blur backdrop.

### Chips & Tags
- Used for cuisine types and "AI Keywords" (e.g., "Quiet," "Romantic").
- Style: Semi-transparent background with a subtle border.

### Inputs
- Background: `#1E1E1E`.
- Focus State: 1px solid primary crimson border with a soft inner glow.

### AI Suggestion Tooltip
- Intense glassmorphic effect (20px blur).
- Gradient border using a transition from Primary Red to a darker shade.
- Animated "Neural Pulse" icon to indicate the AI is processing recommendations.