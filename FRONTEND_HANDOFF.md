# NJM OS — Frontend Handoff Document

> **Generado**: 2026-04-15  
> **Proyecto**: NJM Agents Workspace ("NJM OS")  
> **Origen**: Lovable (React + Vite)  
> **Destino**: Next.js App Router + Claude Code  

---

## Tabla de Contenidos

1. [Vision del Proyecto](#1-vision-del-proyecto)
2. [Tech Stack & Dependencies](#2-tech-stack--dependencies)
3. [Design System & Styling](#3-design-system--styling)
4. [Folder Structure](#4-folder-structure)
5. [Routing Map](#5-routing-map)
6. [Core Components Architecture](#6-core-components-architecture)
7. [State Management](#7-state-management)
8. [Data Layer](#8-data-layer)
9. [Assets & Fonts](#9-assets--fonts)
10. [Constraints & Design Rules](#10-constraints--design-rules)
11. [Migration Notes (Vite → Next.js)](#11-migration-notes)

---

## 1. Vision del Proyecto

NJM OS es un **"Agentic Operating System"** — un workspace profesional tipo dashboard para gestionar marcas a través de agentes de IA especializados. **NO es un chatbot**. Nunca usar interfaces de chat con burbujas o avatares.

### Flujo Principal

```
Login → Day Zero (onboarding) → Agency Hub (lista de marcas)
  └→ Brand Overview (/brand/:id) — landing zone de marca
       ├→ CEO Workspace (/brand/:id/ceo) — estrategia, vectores, Libro Vivo
       └→ PM Workspace (/brand/:id/pm) — táctica, kanban, ejecución
```

### Roles de Agente

| Agente | Color | Rol | HSL |
|--------|-------|-----|-----|
| Agency Hub | Azul | Gestión de portfolio | `210 100% 52%` |
| CEO | Púrpura | Estrategia y autoridad | `271 81% 56%` |
| PM | Esmeralda | Táctica y ejecución | `160 84% 39%` |

---

## 2. Tech Stack & Dependencies

### Dependencias Actuales (package.json)

```json
{
  "dependencies": {
    "@radix-ui/react-accordion": "^1.2.3",
    "@radix-ui/react-alert-dialog": "^1.1.6",
    "@radix-ui/react-aspect-ratio": "^1.1.2",
    "@radix-ui/react-avatar": "^1.1.3",
    "@radix-ui/react-checkbox": "^1.1.4",
    "@radix-ui/react-collapsible": "^1.1.3",
    "@radix-ui/react-context-menu": "^2.2.6",
    "@radix-ui/react-dialog": "^1.1.6",
    "@radix-ui/react-dropdown-menu": "^2.1.6",
    "@radix-ui/react-hover-card": "^1.1.6",
    "@radix-ui/react-label": "^2.1.2",
    "@radix-ui/react-menubar": "^1.1.6",
    "@radix-ui/react-navigation-menu": "^1.2.5",
    "@radix-ui/react-popover": "^1.1.6",
    "@radix-ui/react-progress": "^1.1.2",
    "@radix-ui/react-radio-group": "^1.2.3",
    "@radix-ui/react-scroll-area": "^1.2.3",
    "@radix-ui/react-select": "^2.1.6",
    "@radix-ui/react-separator": "^1.1.2",
    "@radix-ui/react-slider": "^1.2.3",
    "@radix-ui/react-slot": "^1.1.2",
    "@radix-ui/react-switch": "^1.1.3",
    "@radix-ui/react-tabs": "^1.1.3",
    "@radix-ui/react-toast": "^1.2.6",
    "@radix-ui/react-toggle": "^1.1.2",
    "@radix-ui/react-toggle-group": "^1.1.2",
    "@radix-ui/react-tooltip": "^1.1.8",
    "@tanstack/react-query": "^7.72.0",
    "class-variance-authority": "^0.7.1",
    "clsx": "^2.1.1",
    "cmdk": "^1.0.4",
    "date-fns": "^3.6.0",
    "embla-carousel-react": "^8.5.1",
    "input-otp": "^1.4.1",
    "lucide-react": "^0.462.0",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-day-picker": "^8.10.1",
    "react-resizable-panels": "^2.1.7",
    "react-router-dom": "^6.26.2",
    "recharts": "^2.15.0",
    "sonner": "^1.7.1",
    "tailwind-merge": "^2.6.0",
    "tailwindcss-animate": "^1.0.7",
    "vaul": "^0.9.9"
  }
}
```

### Equivalencias para Next.js

| Actual | Next.js |
|--------|---------|
| `react-router-dom` | Next.js App Router (`app/` directory) |
| `vite` | Next.js built-in bundler |
| `@vitejs/plugin-react-swc` | Next.js SWC (built-in) |
| `lovable-tagger` | Eliminar (dev-only de Lovable) |
| Todo lo demás | Compatible directo con Next.js |

### Shadcn UI Components Instalados

Todos estos componentes de Shadcn UI están presentes en `src/components/ui/`:

```
accordion, alert, alert-dialog, aspect-ratio, avatar, badge, breadcrumb,
button, calendar, card, carousel, chart, checkbox, collapsible, command,
context-menu, dialog, drawer, dropdown-menu, form, hover-card, input,
input-otp, label, menubar, navigation-menu, pagination, popover, progress,
radio-group, resizable, scroll-area, select, separator, sheet, sidebar,
skeleton, slider, sonner, switch, table, tabs, textarea, toast, toaster,
toggle, toggle-group, tooltip
```

---

## 3. Design System & Styling

### 3.1 Tailwind Config (tailwind.config.ts)

```ts
import type { Config } from "tailwindcss";

export default {
  darkMode: ["class"],
  content: [
    "./pages/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./app/**/*.{ts,tsx}",
    "./src/**/*.{ts,tsx}",
  ],
  prefix: "",
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: { "2xl": "1400px" },
    },
    extend: {
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["Fira Code", "JetBrains Mono", "monospace"],
      },
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        surface: {
          0: "hsl(var(--surface-0))",
          1: "hsl(var(--surface-1))",
          2: "hsl(var(--surface-2))",
          3: "hsl(var(--surface-3))",
        },
        agency: {
          DEFAULT: "hsl(var(--agency-accent))",
          fg: "hsl(var(--agency-accent-fg))",
        },
        ceo: {
          DEFAULT: "hsl(var(--ceo-accent))",
          fg: "hsl(var(--ceo-accent-fg))",
        },
        pm: {
          DEFAULT: "hsl(var(--pm-accent))",
          fg: "hsl(var(--pm-accent-fg))",
        },
        sidebar: {
          DEFAULT: "hsl(var(--sidebar-background))",
          foreground: "hsl(var(--sidebar-foreground))",
          primary: "hsl(var(--sidebar-primary))",
          "primary-foreground": "hsl(var(--sidebar-primary-foreground))",
          accent: "hsl(var(--sidebar-accent))",
          "accent-foreground": "hsl(var(--sidebar-accent-foreground))",
          border: "hsl(var(--sidebar-border))",
          ring: "hsl(var(--sidebar-ring))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
        "slide-in-right": {
          from: { transform: "translateX(100%)" },
          to: { transform: "translateX(0)" },
        },
        "slide-out-right": {
          from: { transform: "translateX(0)" },
          to: { transform: "translateX(100%)" },
        },
        "fade-in": {
          from: { opacity: "0", transform: "translateY(6px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        "success-pulse": {
          "0%, 100%": { transform: "scale(1)" },
          "50%": { transform: "scale(1.04)" },
        },
        "step-complete": {
          "0%": { backgroundColor: "hsla(160, 84%, 39%, 0.15)" },
          "100%": { backgroundColor: "transparent" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
        "slide-in-right": "slide-in-right 0.3s ease-out",
        "slide-out-right": "slide-out-right 0.3s ease-out",
        "fade-in": "fade-in 0.3s ease-out",
        "success-pulse": "success-pulse 0.5s ease-in-out",
        "step-complete": "step-complete 0.8s ease-out",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
} satisfies Config;
```

### 3.2 CSS Variables & Glass Utilities (globals.css / index.css)

```css
@import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600&family=Inter:wght@300;400;500;600;700&display=swap');

@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 200 30% 96%;
    --foreground: 210 25% 15%;
    --card: 0 0% 100%;
    --card-foreground: 210 25% 15%;
    --popover: 0 0% 100%;
    --popover-foreground: 210 25% 15%;
    --primary: 210 100% 52%;
    --primary-foreground: 0 0% 100%;
    --secondary: 200 20% 92%;
    --secondary-foreground: 210 25% 20%;
    --muted: 200 15% 90%;
    --muted-foreground: 210 10% 45%;
    --accent: 200 20% 94%;
    --accent-foreground: 210 25% 15%;
    --destructive: 0 84% 60%;
    --destructive-foreground: 0 0% 100%;
    --border: 200 20% 85%;
    --input: 200 20% 88%;
    --ring: 210 100% 52%;
    --radius: 1rem;

    /* Agent theme colors */
    --agency-accent: 210 100% 52%;
    --agency-accent-fg: 210 100% 42%;
    --ceo-accent: 271 81% 56%;
    --ceo-accent-fg: 271 70% 46%;
    --pm-accent: 160 84% 39%;
    --pm-accent-fg: 160 70% 32%;

    /* Surface layers — glass surfaces */
    --surface-0: 200 30% 97%;
    --surface-1: 0 0% 100%;
    --surface-2: 200 20% 94%;
    --surface-3: 200 15% 90%;

    /* Glass tokens */
    --glass-bg: 0 0% 100% / 0.55;
    --glass-border: 0 0% 100% / 0.7;
    --glass-shadow: 210 40% 60% / 0.12;

    --sidebar-background: 0 0% 100% / 0.4;
    --sidebar-foreground: 210 10% 40%;
    --sidebar-primary: 210 100% 52%;
    --sidebar-primary-foreground: 0 0% 100%;
    --sidebar-accent: 200 20% 94%;
    --sidebar-accent-foreground: 210 25% 15%;
    --sidebar-border: 0 0% 100% / 0.5;
    --sidebar-ring: 210 100% 52%;
  }

  .dark {
    --background: 222 47% 5%;
    --foreground: 210 20% 90%;
    --card: 222 40% 8%;
    --card-foreground: 210 20% 90%;
    --popover: 222 40% 8%;
    --popover-foreground: 210 20% 90%;
    --primary: 210 100% 52%;
    --primary-foreground: 0 0% 100%;
    --secondary: 222 30% 14%;
    --secondary-foreground: 210 20% 85%;
    --muted: 222 25% 12%;
    --muted-foreground: 210 15% 55%;
    --accent: 222 25% 14%;
    --accent-foreground: 210 20% 90%;
    --destructive: 0 84% 60%;
    --destructive-foreground: 0 0% 100%;
    --border: 222 20% 16%;
    --input: 222 20% 14%;
    --ring: 210 100% 52%;

    --agency-accent: 210 100% 52%;
    --agency-accent-fg: 210 100% 62%;
    --ceo-accent: 271 81% 56%;
    --ceo-accent-fg: 271 70% 66%;
    --pm-accent: 160 84% 39%;
    --pm-accent-fg: 160 70% 50%;

    --surface-0: 222 47% 5%;
    --surface-1: 222 40% 8%;
    --surface-2: 222 30% 12%;
    --surface-3: 222 25% 16%;

    --glass-bg: 222 40% 10% / 0.6;
    --glass-border: 0 0% 100% / 0.08;
    --glass-shadow: 222 50% 3% / 0.4;

    --sidebar-background: 222 40% 6% / 0.7;
    --sidebar-foreground: 210 15% 65%;
    --sidebar-primary: 210 100% 52%;
    --sidebar-primary-foreground: 0 0% 100%;
    --sidebar-accent: 222 25% 14%;
    --sidebar-accent-foreground: 210 20% 90%;
    --sidebar-border: 0 0% 100% / 0.06;
    --sidebar-ring: 210 100% 52%;
  }
}

@layer base {
  * {
    @apply border-border;
  }
  body {
    @apply bg-background text-foreground font-sans antialiased;
    font-family: 'Inter', system-ui, sans-serif;
  }
}

@layer utilities {
  .scrollbar-thin {
    scrollbar-width: thin;
    scrollbar-color: hsl(var(--surface-3)) transparent;
  }

  /* === GLASS SYSTEM === */
  .glass {
    background: hsla(var(--glass-bg));
    border: 1px solid hsla(var(--glass-border));
    backdrop-filter: blur(20px) saturate(1.4);
    -webkit-backdrop-filter: blur(20px) saturate(1.4);
    box-shadow: 0 8px 32px hsla(var(--glass-shadow)),
                inset 0 1px 0 hsla(0, 0%, 100%, 0.4);
  }
  .dark .glass {
    box-shadow: 0 8px 32px hsla(var(--glass-shadow)),
                inset 0 1px 0 hsla(0, 0%, 100%, 0.04);
  }

  .glass-subtle {
    background: hsla(0, 0%, 100%, 0.35);
    border: 1px solid hsla(0, 0%, 100%, 0.5);
    backdrop-filter: blur(12px) saturate(1.2);
    -webkit-backdrop-filter: blur(12px) saturate(1.2);
    box-shadow: 0 4px 16px hsla(var(--glass-shadow));
  }
  .dark .glass-subtle {
    background: hsla(222, 40%, 12%, 0.5);
    border: 1px solid hsla(0, 0%, 100%, 0.06);
  }

  .glass-strong {
    background: hsla(0, 0%, 100%, 0.7);
    border: 1px solid hsla(0, 0%, 100%, 0.8);
    backdrop-filter: blur(24px) saturate(1.5);
    -webkit-backdrop-filter: blur(24px) saturate(1.5);
    box-shadow: 0 8px 32px hsla(var(--glass-shadow)),
                inset 0 1px 0 hsla(0, 0%, 100%, 0.6);
  }
  .dark .glass-strong {
    background: hsla(222, 40%, 10%, 0.8);
    border: 1px solid hsla(0, 0%, 100%, 0.08);
    box-shadow: 0 8px 32px hsla(var(--glass-shadow)),
                inset 0 1px 0 hsla(0, 0%, 100%, 0.04);
  }
}
```

### 3.3 Visual Identity Summary

- **Estética**: "Clear Crystal" glassmorphism sobre fondo de naturaleza con blur 20px
- **Fondo**: Imagen `nature-bg.jpg` (1920x1080) con overlay gradiente semi-transparente
- **Overlay Light**: `from-white/20 via-white/10 to-sky-100/30`
- **Overlay Dark**: `from-black/40 via-black/30 to-slate-900/50`
- **Border radius**: `1rem` (16px) — todo es generosamente redondeado
- **Glass levels**: `glass` (standard), `glass-subtle` (lighter), `glass-strong` (more opaque)
- **Tipografía**: Inter (UI), Fira Code (consolas, código)

---

## 4. Folder Structure

### Estructura Actual (Vite + React Router)

```
src/
├── assets/
│   └── nature-bg.jpg              # Fondo principal (AI-generated landscape)
├── components/
│   ├── njm/                       # Componentes de negocio (19 archivos)
│   │   ├── ActivityFeedDrawer.tsx  # Notificaciones cross-brand
│   │   ├── AgencyHubView.tsx       # Dashboard principal con cards de marcas
│   │   ├── AppSidebar.tsx          # Sidebar con navegación contextual
│   │   ├── AuthGuard.tsx           # Guard de autenticación (mock localStorage)
│   │   ├── BrandOverviewView.tsx   # Landing zone de marca con health ring
│   │   ├── CEOWorkspaceView.tsx    # 4 núcleos del CEO (~700 líneas)
│   │   ├── CommandPalette.tsx      # Cmd+K palette (cmdk)
│   │   ├── DataIngestionModal.tsx  # Modal de onboarding de datos
│   │   ├── DayCeroView.tsx         # Wizard de primer uso (Day Zero)
│   │   ├── DocumentDrawer.tsx      # Drawer custom para documentos
│   │   ├── DocumentSheet.tsx       # Sheet (Shadcn) para documentos
│   │   ├── EmptyState.tsx          # Estado vacío genérico
│   │   ├── ErrorBoundary.tsx       # React Error Boundary
│   │   ├── ExecutionConsole.tsx    # Terminal de ejecución de agentes
│   │   ├── LibroVivoViewer.tsx     # Visor del Libro Vivo (manual de marca)
│   │   ├── NewBrandModal.tsx       # Modal para crear nueva marca
│   │   ├── PMWorkspaceView.tsx     # 4 núcleos del PM (~420 líneas)
│   │   ├── SettingsView.tsx        # Configuraciones (rutas de exportación)
│   │   └── WorkspaceSkeleton.tsx   # Loading skeleton
│   ├── ui/                        # Shadcn UI primitives (~46 archivos)
│   └── NavLink.tsx                # Link de navegación
├── context/
│   ├── AgencyContext.tsx           # Estado del setup wizard
│   └── BrandContext.tsx            # Estado de vectores, Libro Vivo, ejecuciones
├── data/
│   ├── brands.ts                  # Marcas, vectores estratégicos, artefactos
│   ├── brandTriage.ts             # Diagnósticos de marca
│   ├── ceoManagement.ts           # Tipos y mock data del CEO (agentes, OKRs)
│   └── pmManagement.ts            # Tipos y mock data del PM (epics, kanban, constraints)
├── hooks/
│   ├── use-mobile.tsx             # Hook para detectar mobile
│   └── use-toast.ts               # Hook de toast
├── layouts/
│   └── AppLayout.tsx              # Layout principal (sidebar + nature bg + providers)
├── pages/
│   ├── Index.tsx                   # → DayCeroView | AgencyHubView
│   ├── BrandOverviewPage.tsx      # → BrandOverviewView
│   ├── CEOPage.tsx                # → CEOWorkspaceView
│   ├── PMPage.tsx                 # → PMWorkspaceView
│   ├── LibroVivoPage.tsx          # → LibroVivoViewer
│   ├── LoginPage.tsx              # → Página de login
│   ├── SettingsPage.tsx           # → SettingsView
│   └── NotFound.tsx               # 404
├── lib/
│   └── utils.ts                   # cn() helper (clsx + tailwind-merge)
├── App.tsx                        # Router + providers
├── main.tsx                       # Entry point
└── index.css                      # Design tokens + glass utilities
```

### Estructura Propuesta Next.js App Router

```
app/
├── layout.tsx                     # RootLayout (html, body, fonts, providers)
├── globals.css                    # ≡ index.css actual
├── login/
│   └── page.tsx                   # LoginPage
├── (authenticated)/               # Route group con AuthGuard
│   ├── layout.tsx                 # AppLayout (sidebar + nature bg + providers)
│   ├── page.tsx                   # Index (DayCeroView | AgencyHubView)
│   ├── settings/
│   │   └── page.tsx               # SettingsPage
│   └── brand/
│       └── [id]/
│           ├── page.tsx           # BrandOverviewPage
│           ├── ceo/
│           │   └── page.tsx       # CEOPage
│           ├── pm/
│           │   └── page.tsx       # PMPage
│           └── libro-vivo/
│               └── page.tsx       # LibroVivoPage
├── not-found.tsx                  # 404
components/
├── njm/                           # Business components (sin cambios)
└── ui/                            # Shadcn UI (sin cambios)
context/                           # React Context providers
data/                              # Mock data & types
hooks/                             # Custom hooks
lib/
└── utils.ts                       # cn()
public/
└── nature-bg.jpg                  # Mover de src/assets/ a public/
```

---

## 5. Routing Map

| Ruta | Componente | Guard | Descripción |
|------|-----------|-------|-------------|
| `/login` | `LoginPage` | Ninguno | Login mock (localStorage) |
| `/` | `Index` → `DayCeroView` \| `AgencyHubView` | `AuthGuard` | Setup wizard o hub de marcas |
| `/brand/:id` | `BrandOverviewPage` → `BrandOverviewView` | `AuthGuard` | Health ring + resumen de marca |
| `/brand/:id/ceo` | `CEOPage` → `CEOWorkspaceView` | `AuthGuard` | 4 núcleos del CEO |
| `/brand/:id/pm` | `PMPage` → `PMWorkspaceView` | `AuthGuard` | 4 núcleos del PM |
| `/brand/:id/libro-vivo` | `LibroVivoPage` → `LibroVivoViewer` | `AuthGuard` | Visor del Libro Vivo |
| `/settings` | `SettingsPage` → `SettingsView` | `AuthGuard` | Configuraciones |
| `*` | `NotFound` | Ninguno | 404 |

### AuthGuard (Mock)

```tsx
// Chequea localStorage.getItem("njm-auth") === "true"
// Redirige a /login si no autenticado
// NOTA: Inseguro — reemplazar con auth real (Supabase/NextAuth)
```

---

## 6. Core Components Architecture

### 6.1 AppLayout

**Archivo**: `src/layouts/AppLayout.tsx`  
**Responsabilidad**: Shell principal de la app

```
┌──────────────────────────────────┐
│ nature-bg.jpg (absolute, cover)  │
│ ┌──────────────────────────────┐ │
│ │ gradient overlay             │ │
│ │ ┌────┬───────────────────┐   │ │
│ │ │Side│    <Outlet />     │   │ │
│ │ │bar │    (page content) │   │ │
│ │ └────┴───────────────────┘   │ │
│ │ <CommandPalette /> (floating)│ │
│ └──────────────────────────────┘ │
└──────────────────────────────────┘
```

- Envuelve todo en `AgencyProvider` > `BrandProvider`
- Fondo: imagen de naturaleza + overlay semitransparente
- Sidebar a la izquierda, contenido a la derecha via `<Outlet />`
- `CommandPalette` flotante (activado con Cmd+K)

### 6.2 AppSidebar

**Archivo**: `src/components/njm/AppSidebar.tsx` (~300 líneas)  
**Props**: Ninguna (usa hooks internos)

**Comportamiento**:
- Desktop: sidebar fijo colapsable (64px collapsed, 256px expanded)
- Mobile: hamburger menu → sheet overlay
- Navegación contextual: muestra items diferentes según la ruta actual
- Secciones:
  - Header con logo "NJM" + toggle collapse
  - Navegación: Hub, Marcas (dinámicas), Settings
  - Footer: ActivityFeed bell icon, theme toggle (dark/light), user avatar
- Usa `useLocation()` de react-router para highlight activo
- Incluye `ActivityFeedDrawer` (notificaciones) inline

### 6.3 DayCeroView (Day Zero — Onboarding Wizard)

**Archivo**: `src/components/njm/DayCeroView.tsx`  
**Props**: Ninguna (usa `useAgency()`)

**Comportamiento**:
- Wizard de 4 pasos para configurar la agencia
- Paso 1: Nombre de agencia
- Paso 2: Objetivos
- Paso 3: Estilo de comunicación (multi-select chips)
- Paso 4: Valores
- Al completar → `completeSetup(profile)` → redirige a AgencyHubView
- Animaciones de transición entre pasos

### 6.4 AgencyHubView (Dashboard Principal)

**Archivo**: `src/components/njm/AgencyHubView.tsx` (~350 líneas)  
**Props**: Ninguna (usa `useAgency()`, data de `brands.ts`)

**Secciones**:
1. Header con título "Hub de Agencias" + barra de búsqueda + botón "Nueva Marca"
2. Grid de Brand Cards (responsive: 1/2/3 columnas)
   - Cada card muestra: logo, nombre, categoría, health indicator, CEO/PM status badges
   - Click → navega a `/brand/:id`
3. `NewBrandModal` — dialog para crear marca nueva
4. `DataIngestionModal` — modal de carga de datos

### 6.5 BrandOverviewView

**Archivo**: `src/components/njm/BrandOverviewView.tsx` (~400 líneas)  
**Props**: Ninguna (usa `useParams()`, `useBrandContext()`)

**Secciones**:
1. Breadcrumb: Hub > [Brand Name]
2. Brand header (nombre, categoría, descripción)
3. **SVG Health Ring**: Anillo circular animado que muestra % de vectores validados
4. Grid de "Agent Cards" — CEO y PM con status y link a workspace
5. Quick stats (vectores completados, Libro Vivo status)

### 6.6 CEOWorkspaceView (4 Núcleos)

**Archivo**: `src/components/njm/CEOWorkspaceView.tsx` (~700 líneas)  
**Props**: Ninguna (usa `useParams()`, `useBrandContext()`)

**Fases**:
- **Phase 1** (vectores no validados): Muestra vectores pendientes → ejecutar auditoría
- **Phase 2** (todos validados): Dashboard de 4 núcleos

**4 Núcleos del CEO (Phase 2)**:

```
┌─────────────────────────────────────────────┐
│ HEADER (breadcrumb + brand name + badges)    │
├───────────────────────┬─────────────────────┤
│ Núcleo 1:             │ Núcleo 2:           │
│ Autonomía & Control   │ OKRs Estratégicos   │
│ - Slider 0-100%       │ - Lista de OKRs     │
│ - Nivel label         │ - Progress bars     │
│ - Description         │ - KRs anidados      │
├───────────────────────┴─────────────────────┤
│ Núcleo 3: Pull Requests de Decisión         │
│ - Lista de PRs pendientes/aprobados         │
│ - Approve/Reject buttons                     │
├─────────────────────────────────────────────┤
│ Núcleo 4: Agentes Disponibles               │
│ - Grid 3 cards (PM, Marketing, Ventas)       │
│ - Status: active/standby/inactive            │
│ - "Inicializar" button                       │
└─────────────────────────────────────────────┘
```

**Datos del CEO** (`ceoManagement.ts`):
- `AutonomyLevel`: enum (supervised → full_auto)
- `StrategicOKR`: { objective, keyResults[], progress }
- `DecisionPR`: { title, status, author, description, impact }
- `AvailableAgent`: { id, name, icon, status, skills, color }

### 6.7 PMWorkspaceView (4 Núcleos)

**Archivo**: `src/components/njm/PMWorkspaceView.tsx` (~420 líneas)  
**Props**: Ninguna (usa `useParams()`, `useBrandContext()`)

**Gate**: Bloqueado si `!isLibroVivoComplete(brandId)` → muestra EmptyState

**4 Núcleos del PM**:

```
┌─────────────────────────────────────────────┐
│ HEADER (breadcrumb + brand + PM badge)       │
├──────────────────────┬──────────────────────┤
│ Núcleo 1:            │ Núcleo 2:            │
│ Mapa de Épicas       │ Restricciones        │
│ - Accordion épicas   │ & Dependencias       │
│ - Sub-tareas         │ - Constraint cards   │
│ - Progress bars      │ - Dependency links   │
│ - Priority badges    │ - Risk indicators    │
├──────────────────────┴──────────────────────┤
│ Núcleo 3: Tablero Kanban                     │
│ - 4 columnas: Backlog, En Progreso,          │
│   En Revisión (CEO), Completado              │
│ - Tarjetas con ID, título, prioridad         │
├─────────────────────────────────────────────┤
│ Núcleo 4: Terminal de Producción             │
│ - Split view (ResizablePanelGroup)           │
│ - Panel Izq: Context/Sources (Libro Vivo)    │
│ - Panel Der: Output (generated content)      │
│ - ExecutionConsole en la base                │
└─────────────────────────────────────────────┘
```

**Datos del PM** (`pmManagement.ts`):
- `PMEpic`: { id, title, description, progress, priority, subTasks[] }
- `PMSubTask`: { id, title, status, assignee, priority, epicId }
- `PMConstraint`: { id, type, title, severity, description, mitigations[] }
- `KanbanColumn`: backlog | in_progress | in_review | completed
- `ProductionContext`: { sources[], output }

### 6.8 LibroVivoViewer

**Archivo**: `src/components/njm/LibroVivoViewer.tsx`  
**Props**: Ninguna (usa `useParams()`, `useBrandContext()`)

**Comportamiento**:
- Read-only premium viewer del "Libro Vivo" (manual de marca)
- Agrupa vectores validados por categoría
- Cada sección muestra: nombre del vector, summary, status badge
- Botón de descarga como Markdown
- Botón de firma CEO (si aún no firmado)

### 6.9 ExecutionConsole

**Archivo**: `src/components/njm/ExecutionConsole.tsx`  
**Props**:
```ts
interface ExecutionConsoleProps {
  steps: ExecutionStep[];
  title?: string;
}
interface ExecutionStep {
  label: string;
  status: "pending" | "active" | "done";
}
```

**Comportamiento**:
- Terminal-style con fondo oscuro y font mono (Fira Code)
- Muestra pasos de ejecución con indicadores: ○ pending, ● active (pulsing), ✓ done
- Auto-scroll al paso activo
- Se usa en CEO (auditoría) y PM (ejecución táctica)

### 6.10 CommandPalette

**Archivo**: `src/components/njm/CommandPalette.tsx`  
**Props**: Ninguna

- Activación: `Cmd+K` (Mac) / `Ctrl+K` (Windows)
- Usa `cmdk` library
- Comandos: navegar a marcas, workspaces, settings
- Filtrado fuzzy por texto

### 6.11 Componentes Secundarios

| Componente | Props | Descripción |
|-----------|-------|-------------|
| `ActivityFeedDrawer` | `open, onOpenChange` | Lista de actividades recientes cross-brand |
| `DataIngestionModal` | `open, onOpenChange, brandId` | Upload de archivos (PDF/Excel) + briefing |
| `NewBrandModal` | `open, onOpenChange` | Formulario para crear marca nueva |
| `DocumentSheet` | `open, onOpenChange, artifact: Artifact` | Sheet lateral para ver/aprobar documentos |
| `DocumentDrawer` | `open, onClose, document` | Drawer custom para documentos (alternativo) |
| `EmptyState` | `icon, title, description, action?` | Estado vacío reutilizable |
| `ErrorBoundary` | `children` | React Error Boundary con fallback UI |
| `WorkspaceSkeleton` | Ninguna | Loading skeleton para workspaces |

---

## 7. State Management

### 7.1 AgencyContext

**Archivo**: `src/context/AgencyContext.tsx`  
**Scope**: Setup wizard (Day Zero)

```ts
interface AgencyContextValue {
  isSetupComplete: boolean;        // ¿Ya pasó el wizard?
  profile: AgencyProfile | null;   // Datos de la agencia
  completeSetup: (profile) => void;// Completar wizard
  resetSetup: () => void;          // Reset para re-hacer wizard
}

interface AgencyProfile {
  name: string;
  objectives: string;
  style: string[];
  values: string;
}
```

**Persistencia**: `localStorage`
- `njm-agency-setup`: `"true"` | absent
- `njm-agency-profile`: JSON string del profile

### 7.2 BrandContext

**Archivo**: `src/context/BrandContext.tsx`  
**Scope**: Todo el estado de marcas y ejecución de agentes

```ts
interface BrandContextValue {
  // Vectores estratégicos
  getVectors: (brandId: string) => StrategicVector[];
  toggleVector: (brandId: string, vectorId: string) => void;
  validateAllVectors: (brandId: string) => void;

  // Libro Vivo
  isLibroVivoComplete: (brandId: string) => boolean;
  signLibroVivo: (brandId: string) => void;

  // CEO Execution
  isScanning: boolean;
  scanningVectorId: string | null;
  executionSteps: ExecutionStep[];
  runCEOAudit: (brandId: string, onComplete?: () => void) => void;

  // PM Execution
  runPMExecution: (onComplete?: () => void) => void;
  isPMRunning: boolean;
  pmExecutionSteps: ExecutionStep[];
}
```

**Estado interno**:
- `vectors`: `Record<string, StrategicVector[]>` — vectores por brandId
- `libroVivoStatus`: `Record<string, boolean>` — ¿Libro Vivo firmado?
- Inicializado con brands `"1"` y `"4"` como ya firmados

**Flujo de ejecución CEO** (`runCEOAudit`):
1. Filtra vectores no validados
2. Itera con `setTimeout` (1s entre cada uno)
3. Actualiza steps: pending → active → done
4. Toast por cada vector validado
5. Al finalizar: limpia estado de scanning

**Flujo de ejecución PM** (`runPMExecution`):
1. 6 pasos fijos (labels en `pmStepLabels`)
2. Itera con `setTimeout` (1.2s entre cada uno)
3. Misma mecánica de steps
4. Toast final de éxito

### 7.3 localStorage Keys

| Key | Uso | Valor |
|-----|-----|-------|
| `njm-auth` | Mock authentication | `"true"` |
| `njm-agency-setup` | Setup wizard completado | `"true"` |
| `njm-agency-profile` | Perfil de agencia | JSON |
| `njm-theme` | Tema dark/light | `"dark"` \| `"light"` |

### 7.4 Flujo de Estado entre Componentes

```
AgencyContext.isSetupComplete
  ├── false → DayCeroView (wizard)
  └── true → AgencyHubView (brand cards)
              └── click brand → BrandOverviewView
                    ├── CEO card → CEOWorkspaceView
                    │     ├── vectors not validated → Phase 1 (audit)
                    │     └── all validated → Phase 2 (4 nucleos)
                    │           └── signLibroVivo() → unlocks PM
                    └── PM card → PMWorkspaceView
                          ├── !isLibroVivoComplete → EmptyState (locked)
                          └── isLibroVivoComplete → 4 nucleos PM
```

---

## 8. Data Layer

### 8.1 brands.ts — Tipos Principales

```ts
interface Brand {
  id: string;
  name: string;
  category: string;
  description: string;
  logo: string;        // Emoji o URL
  color: string;       // HSL string
  industry: string;
  stage: string;
}

interface StrategicVector {
  id: string;
  brandId: string;
  name: string;
  category: "growth" | "positioning" | "operations" | "innovation";
  description: string;
  validated: boolean;
  summary?: string;
}

interface Artifact {
  id: string;
  brandId: string;
  name: string;
  description: string;
  framework?: string;
  status: "draft" | "review" | "approved";
  type: "analysis" | "strategy" | "plan";
}
```

**Mock Data**:
- `brands`: Array de ~6 marcas de ejemplo
- `strategicVectors`: Array de ~8 vectores por marca
- `artifacts`: Array de artefactos por marca

### 8.2 brandTriage.ts

```ts
interface BrandDiagnosis {
  brandId: string;
  health: number;       // 0-100
  risks: string[];
  opportunities: string[];
  recommendations: string[];
}
```

### 8.3 ceoManagement.ts

```ts
type AutonomyLevel = "supervised" | "assisted" | "autonomous" | "full_auto";

interface StrategicOKR {
  id: string;
  objective: string;
  keyResults: { id: string; title: string; current: number; target: number }[];
  progress: number;
}

interface DecisionPR {
  id: string;
  title: string;
  description: string;
  author: string;           // "Agente PM" | "Agente Marketing"
  status: "pending" | "approved" | "rejected";
  impact: "high" | "medium" | "low";
  createdAt: string;
}

interface AvailableAgent {
  id: string;
  name: string;
  icon: string;             // Lucide icon name
  status: "active" | "standby" | "inactive";
  skills: string[];
  color: string;            // HSL
}
```

### 8.4 pmManagement.ts

```ts
interface PMEpic {
  id: string;
  title: string;
  description: string;
  progress: number;         // 0-100
  priority: "critical" | "high" | "medium" | "low";
  subTasks: PMSubTask[];
}

interface PMSubTask {
  id: string;
  title: string;
  status: "backlog" | "in_progress" | "in_review" | "completed";
  assignee: string;
  priority: "critical" | "high" | "medium" | "low";
  epicId: string;
}

interface PMConstraint {
  id: string;
  type: "budget" | "time" | "resource" | "technical" | "dependency";
  title: string;
  severity: "critical" | "high" | "medium" | "low";
  description: string;
  mitigations: string[];
}

interface ProductionContext {
  sources: { title: string; content: string; type: "libro_vivo" | "external" }[];
  output: string;
}

// Kanban columns
type KanbanColumn = "backlog" | "in_progress" | "in_review" | "completed";
```

---

## 9. Assets & Fonts

### Fonts (Google Fonts)

```
Inter: 300, 400, 500, 600, 700 — UI principal
Fira Code: 400, 500, 600 — Monospace (consolas, terminal)
```

URL: `https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600&family=Inter:wght@300;400;500;600;700&display=swap`

Para Next.js, usar `next/font`:
```ts
import { Inter, Fira_Code } from 'next/font/google';
const inter = Inter({ subsets: ['latin'], variable: '--font-sans' });
const firaCode = Fira_Code({ subsets: ['latin'], variable: '--font-mono' });
```

### Images

| Asset | Ubicación | Dimensiones | Uso |
|-------|-----------|-------------|-----|
| `nature-bg.jpg` | `src/assets/` | 1920x1080 | Fondo principal (AI landscape) |
| `placeholder.svg` | `public/` | Variable | Placeholder genérico |

### Icons

Todo el iconset viene de **Lucide React** (`lucide-react`). No hay iconos custom SVG.

Iconos más usados:
```
Building2, Brain, Cpu, Target, TrendingUp, Shield, Zap, Clock,
CheckCircle2, XCircle, AlertTriangle, Sparkles, Download,
ChevronRight, ChevronDown, Plus, Search, Settings, Bell,
Moon, Sun, LogOut, Home, BookOpen, BarChart3, GitPullRequest,
Users, Layers, Terminal, PanelLeftClose, PanelLeft, Menu
```

---

## 10. Constraints & Design Rules

### Absolutos (NUNCA hacer)

1. **NO chat interfaces** — Sin burbujas de chat, avatares conversacionales, ni interfaces tipo ChatGPT
2. **NO colores directos** — Usar siempre tokens semánticos (`text-foreground`, `bg-card`, `text-pm-fg`, etc.)
3. **NO serif fonts** — Solo Inter y Fira Code
4. **NO API keys en frontend** — Tab de API keys fue removido por seguridad
5. **NO auth real** — Mock auth via localStorage hasta implementar backend

### Principios de UI

1. **Workspace-centric**: Cada agente tiene su propio workspace con núcleos específicos
2. **Glass everywhere**: Todos los paneles usan clases `glass`, `glass-subtle`, o `glass-strong`
3. **Agent color coding**: Blue (agency), Purple (CEO), Emerald (PM) — consistente en badges, borders, accents
4. **Density gradient**: CEO = high-level metrics; PM = high-density tactical data
5. **Terminal aesthetic**: Execution consoles usan Fira Code sobre fondo oscuro
6. **Generous border-radius**: `rounded-2xl` (16px) es el estándar para cards y paneles

### Responsividad

- Sidebar: collapse a hamburger en mobile
- Grids: 1 col mobile → 2 col tablet → 3 col desktop
- Sheets/Drawers: full-width en mobile, max-width en desktop
- Nature background: `object-cover` con overlay adaptativo

---

## 11. Migration Notes (Vite → Next.js)

### Cambios Requeridos

1. **Routing**: Reemplazar `react-router-dom` con Next.js App Router
   - `useNavigate()` → `useRouter()` de `next/navigation`
   - `useParams()` → `useParams()` de `next/navigation`
   - `useLocation()` → `usePathname()` de `next/navigation`
   - `<Link to="">` → `<Link href="">`
   - `<Navigate to="" replace />` → `redirect()` o `useRouter().replace()`
   - `<Outlet />` → `{children}` en layouts

2. **Images**: 
   - `import img from "@/assets/img.jpg"` → `<Image src="/img.jpg" />` con `next/image`
   - Mover `nature-bg.jpg` de `src/assets/` a `public/`

3. **Providers**: Marcar contexts como `"use client"` en Next.js

4. **Path alias**: `@/` ya funciona con Next.js `tsconfig.json`

5. **Metadata/SEO**:
   ```ts
   // app/layout.tsx
   export const metadata = {
     title: "NJM OS — Agentic Workspace",
     description: "Sistema operativo para agentes de IA estratégicos",
   };
   ```

6. **Components**: Todos los componentes interactivos necesitan `"use client"` directive

### Lo que NO cambia

- Todos los componentes de `src/components/njm/` y `src/components/ui/`
- Contexts (`AgencyContext`, `BrandContext`) — solo agregar `"use client"`
- Data files (`brands.ts`, `ceoManagement.ts`, `pmManagement.ts`)
- CSS variables, glass utilities, tailwind config
- Shadcn UI components (compatibles 1:1)

---

## Apéndice: Resumen de Archivos por Prioridad de Migración

### Críticos (migrar primero)
1. `globals.css` (index.css) — Design tokens
2. `tailwind.config.ts` — Theme config
3. `lib/utils.ts` — cn() helper
4. `components/ui/*` — Shadcn primitives
5. `context/AgencyContext.tsx` + `context/BrandContext.tsx`
6. `data/*` — Mock data layer

### Core Views (migrar segundo)
7. `layouts/AppLayout.tsx` → `app/(authenticated)/layout.tsx`
8. `components/njm/AppSidebar.tsx`
9. `components/njm/AgencyHubView.tsx`
10. `components/njm/CEOWorkspaceView.tsx`
11. `components/njm/PMWorkspaceView.tsx`
12. `components/njm/BrandOverviewView.tsx`

### Secundarios (migrar tercero)
13. `components/njm/LibroVivoViewer.tsx`
14. `components/njm/DayCeroView.tsx`
15. `components/njm/CommandPalette.tsx`
16. `components/njm/ExecutionConsole.tsx`
17. Modales y drawers

---

*Fin del documento de handoff. Toda la información necesaria para recrear NJM OS en Next.js está contenida aquí.*
