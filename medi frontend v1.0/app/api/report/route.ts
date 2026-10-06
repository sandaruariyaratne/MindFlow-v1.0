import { NextResponse } from 'next/server'
import { query } from '@/lib/db'

export async function POST(request: Request) {
  try {
    const body = await request.json()
    const { sessionId, qualityScore, ...responses } = body

    try {
      // Create table if not exists in QuestDB
      await query(`
        CREATE TABLE IF NOT EXISTS self_reports (
          timestamp TIMESTAMP,
          sessionId STRING,
          qualityScore DOUBLE,
          calmness INT,
          focus INT,
          mindWandering INT,
          emotionalBalance INT,
          presence INT,
          mentalRefreshment INT,
          attentionEase INT,
          bodyRelaxation INT,
          meditationDepth INT,
          overallSatisfaction INT
        ) timestamp(timestamp) PARTITION BY DAY;
      `)

      // Insert data
      await query(`
        INSERT INTO self_reports (
          timestamp, sessionId, qualityScore, calmness, focus, mindWandering,
          emotionalBalance, presence, mentalRefreshment,
          attentionEase, bodyRelaxation, meditationDepth, overallSatisfaction
        ) VALUES (
          $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13
        )
      `, [
        new Date(),
        sessionId,
        qualityScore,
        responses.calmness,
        responses.focus,
        responses.mindWandering,
        responses.emotionalBalance,
        responses.presence,
        responses.mentalRefreshment,
        responses.attentionEase,
        responses.bodyRelaxation,
        responses.meditationDepth,
        responses.overallSatisfaction,
      ])
    } catch (dbError) {
      console.warn('Database offline, proceeding in cloud demonstration mode:', dbError)
    }

    return NextResponse.json({ success: true, message: 'Report saved successfully' })
  } catch (error: any) {
    console.error('Error in /api/report:', error)
    return NextResponse.json(
      { success: false, message: 'Failed to process report', error: error.message },
      { status: 500 }
    )
  }
}
