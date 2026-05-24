import { Pool } from 'pg'

const pool = new Pool({
  host: 'localhost',
  port: 8812,
  user: 'admin',
  password: 'quest',
  database: 'qdb',
})

export const query = (text: string, params?: any[]) => pool.query(text, params)
