# 🚚 LogiFlow — Logistics Dashboard

A full-featured logistics management dashboard built with React, TypeScript, Vite, TailwindCSS, and React Leaflet.

## Features

- **Authentication** — JWT-based login with role-based access (Admin, Dispatcher, Driver)
- **Dashboard** — KPI cards, recent orders, auto-assignment
- **Orders** — Full data table with filtering, sorting, pagination, and status management
- **Map** — Interactive Leaflet map with delivery point markers, clustering, and nearby stock search
- **Admin Panel** — User, resource, and delivery point management
- **Notifications** — Real-time WebSocket notifications
- **Offline Support** — Banner shown when offline

## Setup

### Prerequisites
- Node.js 18+
- npm 9+

### Installation

```bash
npm install
```

### Configuration

```bash
cp .env.example .env
```

Edit `.env` to point to your backend:

```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

### Development

```bash
npm run dev
```

### Production Build

```bash
npm run build
```

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `VITE_API_URL` | Backend REST API base URL | `http://localhost:8000` |
| `VITE_WS_URL` | WebSocket server base URL | `ws://localhost:8000` |

## Project Structure

```
src/
├── api/            # Axios client + API call functions
├── components/     # Reusable UI components
├── pages/          # Route-level page components
├── features/       # Feature-specific components (modals, drawers, map)
├── hooks/          # Custom React hooks
├── context/        # Auth, Toast, and Notification contexts
├── utils/          # Helper utilities
└── types/          # TypeScript interfaces
```

## Auth Roles

- **Admin** — Full access including admin panel
- **Dispatcher** — Can manage orders and drivers
- **Driver** — Read-only order access
