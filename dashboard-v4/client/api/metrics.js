module.exports = (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.json({ data: { agents: { total: 13, online: 6 }, tasks: { total: 10, done: 4 }, uptime: 999, memoryMB: 42 } });
};
