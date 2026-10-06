import { Pool } from 'pg'

const isVercel = process.env.VERCEL === '1' || Boolean(process.env.NEXT_PUBLIC_VERCEL_ENV)

const pool = new Pool({
  host: process.env.QUESTDB_HOST || (isVercel ? 'unreachable-host' : 'localhost'),
  port: parseInt(process.env.QUESTDB_PORT || '8812'),
  user: process.env.QUESTDB_USER || 'admin',
  password: process.env.QUESTDB_PASSWORD || 'quest',
  database: process.env.QUESTDB_NAME || 'qdb',
  connectionTimeoutMillis: isVercel ? 500 : 2000,
})

export const query = async (text: string, params?: any[]) => {
  // If explicitly deployed to Vercel and no external DB host is set, skip attempting connection
  if (isVercel && !process.env.QUESTDB_HOST) {
    throw new Error('QuestDB not configured for cloud deployment; switching to simulation mode.')
  }
  return pool.query(text, params)
}
