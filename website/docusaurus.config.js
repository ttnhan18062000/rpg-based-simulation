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

  plugins: [],

  themes: [
    [
      require.resolve('@easyops-cn/docusaurus-search-local'),
      {
        hashed: false,
        docsRouteBasePath: ['docs'],
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
          exclude: [
            'superpowers/**',
            'specs/**',
            'parity_ledger/**',
            'scenarios/**',
            'entity/**',
            'archive/**',
            'plans/**',
            'audits/**',
            'optimization_audit_ledger.md',
          ],
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
      ],
    },
  },
};

module.exports = config;
