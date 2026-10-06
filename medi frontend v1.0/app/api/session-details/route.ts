import { NextResponse } from 'next/server'
import { query } from '@/lib/db'
import { generateSessionDetails } from '@/lib/simulation'

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const sessionId = searchParams.get('sessionId')

  if (!sessionId) {
    return NextResponse.json({ error: 'Session ID is required' }, { status: 400 })
  }

  try {
    // 1. Fetch Alpha/Beta and RMSSD from final_features
    const featuresResult = await query(`
      SELECT 
        timestamp,
        Alpha_Beta_Ratio as alphabeta,
        RMSSD as rmssd
      FROM final_features
      WHERE session_id = $1
      ORDER BY timestamp ASC
    `, [sessionId])

    // 2. Fetch Calmness Score from calmness table
    const calmnessResult = await query(`
      SELECT 
        timestamp,
        calmness_score as score
      FROM calmness
      WHERE session_id = $1
      ORDER BY timestamp ASC
    `, [sessionId])

    if (featuresResult.rows && featuresResult.rows.length > 0) {
      return NextResponse.json({
        features: featuresResult.rows,
        calmness: calmnessResult.rows
      })
    }
  } catch (error: any) {
    console.warn('Database offline or skipped in /api/session-details, using simulation:', error.message)
  }

  // Cloud Simulation Fallback
  const simDetails = generateSessionDetails(sessionId)
  return NextResponse.json(simDetails)
}
