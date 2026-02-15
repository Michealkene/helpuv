module.exports = {
  apps: [{
    name: 'dashboard',
    script: 'server.js',
    cwd: 'C:/Users/Administrator/dashboard',
    env: {
      ACCESS_TOKEN: 'openclaw2026',
      DASHBOARD_PORT: '3333',
      JWT_SECRET: 'openclaw-dashboard-secret-2026'
    }
  }]
};
