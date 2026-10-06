import { NextResponse } from 'next/server'
import { query } from '@/lib/db'
import { generateCalmnessData } from '@/lib/simulation'

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

    if (result.rows && result.rows.length > 0) {
      return NextResponse.json(result.rows)
    }
  } catch (error: any) {
    console.warn('Database query skipped or offline in /api/calmness, using simulation telemetry:', error.message)
  }

  // Resilient Cloud Fallback
  const simFrames = generateCalmnessData(sessionId)
  const returnedFrames = isAll ? simFrames : simFrames.slice(-50)
  return NextResponse.json(returnedFrames)
}
