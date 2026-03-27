module.exports = (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.json({ data: [
    { id: 1, type: 'project_start', source: 'main', created_at: new Date().toISOString() },
    { id: 2, type: 'test_pass', source: 'qa_engineer', created_at: new Date().toISOString() },
    { id: 3, type: 'deploy', source: 'dev_engineer', created_at: new Date().toISOString() },
  ]});
};
