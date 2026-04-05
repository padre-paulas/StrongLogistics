const pt = {
  nav: {
    dashboard: 'Painel',
    orders: 'Pedidos',
    map: 'Mapa',
    admin: 'Administração',
    settings: 'Preferências',
  },
  settings: {
    title: 'Preferências e Configurações',
    tabs: {
      appearance: 'Aparência',
      language: 'Idioma',
      notifications: 'Notificações',
    },
    appearance: {
      heading: 'Aparência',
      darkMode: 'Modo Escuro',
      darkModeDesc: 'Alternar entre o tema claro e escuro da interface.',
      light: 'Claro',
      dark: 'Escuro',
    },
    language: {
      heading: 'Idioma',
      desc: 'Escolha o idioma utilizado em toda a aplicação.',
      en: 'English',
      pt: 'Português',
    },
    notifications: {
      heading: 'Notificações',
      criticalAlerts: 'Alertas de pedidos críticos',
      criticalAlertsDesc: 'Mostrar um aviso e som quando um pedido crítico for criado ou atualizado.',
      statusUpdates: 'Alertas de atualização de status',
      statusUpdatesDesc: 'Notificar quando o status de um pedido mudar (despachado, em trânsito, entregue).',
      driverUpdates: 'Alertas de atribuição de motorista',
      driverUpdatesDesc: 'Notificar quando um motorista for atribuído ou reatribuído a um pedido.',
    },
    saved: 'Preferências salvas',
  },
} as const;

export default pt;
