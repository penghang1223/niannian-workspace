const db = require('../database');
const bcrypt = require('bcrypt');

class User {
  static async create(userData) {
    const { name, email, password, role = 'user' } = userData;

    // 检查邮箱是否已存在
    const existingUser = await this.findByEmail(email);
    if (existingUser) {
      throw new Error('邮箱已存在');
    }

    // 加密密码
    const hashedPassword = await bcrypt.hash(password, 10);

    const query = `
      INSERT INTO users (name, email, password, role)
      VALUES ($1, $2, $3, $4)
      RETURNING *
    `;

    const values = [name, email, hashedPassword, role];

    const result = await db.query(query, values);
    return result.rows[0];
  }

  static async findByEmail(email) {
    const query = 'SELECT * FROM users WHERE email = $1';
    const result = await db.query(query, [email]);
    return result.rows[0];
  }

  static async findById(id) {
    const query = 'SELECT id, name, email, role, created_at FROM users WHERE id = $1';
    const result = await db.query(query, [id]);
    return result.rows[0];
  }

  static async validatePassword(email, password) {
    const user = await this.findByEmail(email);
    if (!user) return false;

    const isValid = await bcrypt.compare(password, user.password);
    return isValid ? user : false;
  }

  static async updateProfile(id, data) {
    const { name, email } = data;

    const query = `
      UPDATE users
      SET name = $1, email = $2
      WHERE id = $3
      RETURNING id, name, email, role, updated_at
    `;

    const values = [name, email, id];

    const result = await db.query(query, values);
    return result.rows[0];
  }
}

module.exports = User;