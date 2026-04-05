const en = {
  nav: {
    dashboard: 'Dashboard',
    orders: 'Orders',
    map: 'Map',
    admin: 'Admin',
    settings: 'Settings',
  },
  settings: {
    title: 'Preferences & Settings',
    tabs: {
      appearance: 'Appearance',
      language: 'Language',
      notifications: 'Notifications',
    },
    appearance: {
      heading: 'Appearance',
      darkMode: 'Dark Mode',
      darkModeDesc: 'Switch between light and dark interface theme.',
      light: 'Light',
      dark: 'Dark',
    },
    language: {
      heading: 'Language',
      desc: 'Choose the language used throughout the application.',
      en: 'English',
      pt: 'Português',
    },
    notifications: {
      heading: 'Notifications',
      criticalAlerts: 'Critical order alerts',
      criticalAlertsDesc: 'Show a banner and sound when a critical-priority order is created or updated.',
      statusUpdates: 'Status update alerts',
      statusUpdatesDesc: 'Notify when an order status changes (dispatched, in-transit, delivered).',
      driverUpdates: 'Driver assignment alerts',
      driverUpdatesDesc: 'Notify when a driver is assigned or reassigned to an order.',
    },
    saved: 'Preferences saved',
  },
} as const;

export default en;
