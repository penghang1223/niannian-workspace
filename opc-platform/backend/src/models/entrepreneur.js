const db = require('../database');

class Entrepreneur {
  static async create(data) {
    const { name, city, province, track, lat, lng, mrr, createdAt } = data;

    const query = `
      INSERT INTO entrepreneurs (name, city, province, track, lat, lng, mrr, created_at)
      VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
      RETURNING *
    `;

    const values = [name, city, province, track, lat, lng, mrr, createdAt];

    const result = await db.query(query, values);
    return result.rows[0];
  }

  static async findById(id) {
    const query = 'SELECT * FROM entrepreneurs WHERE id = $1';
    const result = await db.query(query, [id]);
    return result.rows[0];
  }

  static async findAll(filters = {}) {
    const { search, track, limit = 50, offset = 0 } = filters;

    let query = 'SELECT * FROM entrepreneurs WHERE 1=1';
    const values = [];
    let paramCount = 1;

    if (search) {
      query += ` AND (name ILIKE $${paramCount} OR city ILIKE $${paramCount} OR province ILIKE $${paramCount} OR track ILIKE $${paramCount})`;
      values.push(`%${search}%`);
      paramCount++;
    }

    if (track && track !== 'ALL') {
      query += ` AND track = $${paramCount}`;
      values.push(track);
      paramCount++;
    }

    query += ` ORDER BY created_at DESC LIMIT $${paramCount} OFFSET $${paramCount + 1}`;
    values.push(limit, offset);

    const result = await db.query(query, values);
    return result.rows;
  }

  static async count(filters = {}) {
    const { search, track } = filters;

    let query = 'SELECT COUNT(*) FROM entrepreneurs WHERE 1=1';
    const values = [];
    let paramCount = 1;

    if (search) {
      query += ` AND (name ILIKE $${paramCount} OR city ILIKE $${paramCount} OR province ILIKE $${paramCount} OR track ILIKE $${paramCount})`;
      values.push(`%${search}%`);
      paramCount++;
    }

    if (track && track !== 'ALL') {
      query += ` AND track = $${paramCount}`;
      values.push(track);
      paramCount++;
    }

    const result = await db.query(query, values);
    return parseInt(result.rows[0].count);
  }

  static async update(id, data) {
    const { name, city, province, track, lat, lng, mrr } = data;

    const query = `
      UPDATE entrepreneurs
      SET name = $1, city = $2, province = $3, track = $4, lat = $5, lng = $6, mrr = $7
      WHERE id = $8
      RETURNING *
    `;

    const values = [name, city, province, track, lat, lng, mrr, id];

    const result = await db.query(query, values);
    return result.rows[0];
  }

  static async delete(id) {
    const query = 'DELETE FROM entrepreneurs WHERE id = $1 RETURNING *';
    const result = await db.query(query, [id]);
    return result.rows[0];
  }

  static async getStats() {
    const query = `
      SELECT
        COUNT(*) as totalEntrepreneurs,
        COUNT(CASE WHEN created_at >= CURRENT_DATE THEN 1 END) as todayNew,
        COUNT(DISTINCT city) as coveredCities,
        COUNT(DISTINCT track) as activeTracks,
        SUM(mrr) as totalMrr
      FROM entrepreneurs
    `;

    const result = await db.query(query);
    return result.rows[0];
  }
}

module.exports = Entrepreneur;