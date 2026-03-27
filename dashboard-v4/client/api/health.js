module.exports = (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.json({ status: 'ok', version: '1.0.0', timestamp: new Date().toISOString() });
};
