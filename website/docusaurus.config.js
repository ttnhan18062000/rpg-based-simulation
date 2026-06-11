// @ts-check

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'RPG Simulation Docs',
  url: process.env.DOCS_URL || 'http://localhost',
  baseUrl: process.env.DOCS_BASE_URL || '/',
  onBrokenLinks: 'warn',
  trailingSlash: false,
  markdown: {
    format: 'md',
  },

  plugins: [
    [
      '@docusaurus/plugin-content-docs',
      {
        id: 'tickets',
        path: '../tickets/done',
        routeBasePath: 'tickets',
        sidebarPath: require.resolve('./sidebars-tickets.js'),
        showLastUpdateTime: true,
        showLastUpdateAuthor: true,
      },
    ],
    [
      '@docusaurus/plugin-content-docs',
      {
        id: 'artifacts',
        path: '../stored_artifacts',
        routeBasePath: 'artifacts',
        sidebarPath: require.resolve('./sidebars-artifacts.js'),
        showLastUpdateTime: true,
        showLastUpdateAuthor: true,
      },
    ],
  ],

  themes: [
    [
      require.resolve('@easyops-cn/docusaurus-search-local'),
      {
        hashed: false,
        docsRouteBasePath: ['docs', 'tickets', 'artifacts'],
        indexBlog: false,
      },
    ],
  ],

  presets: [
    [
      'classic',
      {
        docs: {
          path: '../docs',
          routeBasePath: 'docs',
          exclude: ['superpowers/**', 'specs/**', 'parity_ledger/**', 'scenarios/**', 'entity/**'],
          sidebarPath: require.resolve('./sidebars.js'),
          showLastUpdateTime: true,
          showLastUpdateAuthor: true,
        },
        blog: false,
        theme: { customCss: [require.resolve('./src/css/custom.css')] },
      },
    ],
  ],

  themeConfig: {
    navbar: {
      title: 'RPG Simulation Docs',
      items: [
        { to: '/docs/', label: 'Docs', position: 'left' },
        { to: '/tickets/', label: 'Tickets', position: 'left' },
        { to: '/artifacts/', label: 'Artifacts', position: 'left' },
        { to: '/docs/archive/', label: 'Archive', position: 'left' },
      ],
    },
  },
};

module.exports = config;
