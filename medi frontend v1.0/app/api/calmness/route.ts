import { NextResponse } from 'next/server'
import { query } from '@/lib/db'

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const sessionId = searchParams.get('sessionId')

  if (!sessionId) {
    return NextResponse.json({ error: 'Session ID is required' }, { status: 400 })
  }

  const isAll = searchParams.get('all') === 'true'

  try {
    const queryStr = isAll 
      ? `SELECT timestamp, calmness_score as score FROM calmness WHERE session_id = $1 ORDER BY timestamp ASC`
      : `SELECT * FROM (
          SELECT timestamp, calmness_score as score FROM calmness WHERE session_id = $1 ORDER BY timestamp DESC LIMIT 50
        ) sub ORDER BY timestamp ASC`

    const result = await query(queryStr, [sessionId])

    return NextResponse.json(result.rows)
  } catch (error: any) {
    console.error('Database Error:', error)
    return NextResponse.json({ error: error.message }, { status: 500 })
  }
}
