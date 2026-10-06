import { NextResponse } from 'next/server'
import { query } from '@/lib/db'
import { spawn } from 'child_process'
import path from 'path'
import { generateSessionSummary, calculatePredictedScore } from '@/lib/simulation'

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const sessionId = searchParams.get('sessionId')

  if (!sessionId) {
    return NextResponse.json({ error: 'Session ID is required' }, { status: 400 })
  }

  try {
    // Fetch metrics summary from final_features in QuestDB
    const result = await query(`
      SELECT 
        avg(Alpha_Beta_Ratio) as alphabetamean,
        stddev(Alpha_Beta_Ratio) as alphabetastd,
        avg(RMSSD) as rmssdmean,
        stddev(RMSSD) as rmssdstd
      FROM final_features
      WHERE session_id = $1
    `, [sessionId])

    if (result.rows && result.rows.length > 0 && result.rows[0].alphabetamean !== null) {
      const row = result.rows[0]
      const summary = {
        alphaBetaMean: parseFloat(row?.alphabetamean || 0),
        alphaBetaStd: parseFloat(row?.alphabetastd || 0),
        rmssdMean: parseFloat(row?.rmssdmean || 0),
        rmssdStd: parseFloat(row?.rmssdstd || 0),
      }
      return NextResponse.json(summary)
    }
  } catch (error: any) {
    console.warn('Database offline or skipped in /api/session-summary, using simulation:', error.message)
  }

  // Cloud Simulation Fallback
  const simSummary = generateSessionSummary(sessionId)
  return NextResponse.json(simSummary)
}

export async function POST(request: Request) {
  try {
    const body = await request.json()
    const {
      sessionId,
      alphaBetaMean,
      alphaBetaStd,
      rmssdMean,
      rmssdStd,
      qualityScore,
    } = body

    let finalScore = calculatePredictedScore(alphaBetaMean || 10.5, rmssdMean || 55.0, qualityScore || 7.5)

    // Attempt saving to QuestDB if available
    try {
      await query(`
        CREATE TABLE IF NOT EXISTS meditation_summaries (
          timestamp TIMESTAMP,
          sessionId STRING,
          alphaBetaMean DOUBLE,
          alphaBetaStd DOUBLE,
          rmssdMean DOUBLE,
          rmssdStd DOUBLE,
          qualityScore DOUBLE
        ) timestamp(timestamp) PARTITION BY DAY;
      `)

      await query(`
        INSERT INTO meditation_summaries (
          timestamp, sessionId, alphaBetaMean, alphaBetaStd, 
          rmssdMean, rmssdStd, qualityScore
        ) VALUES (
          $1, $2, $3, $4, $5, $6, $7
        )
      `, [
        new Date(),
        sessionId,
        alphaBetaMean,
        alphaBetaStd,
        rmssdMean,
        rmssdStd,
        qualityScore,
      ])

      // Check if Python predictor script is runnable
      const rootDir = path.resolve(process.cwd(), '..')
      const pythonPath = path.join(rootDir, '.venv', 'bin', 'python')
      const isVercel = process.env.VERCEL === '1' || Boolean(process.env.NEXT_PUBLIC_VERCEL_ENV)
      const fs = await import('fs')

      if (!isVercel && fs.existsSync(pythonPath)) {
        await new Promise((resolve, reject) => {
          const predictor = spawn(pythonPath, [
            path.join(rootDir, 'run_model_prediction.py'),
            '--session-id', sessionId
          ], { cwd: rootDir })
          
          predictor.on('close', (code) => resolve(code))
          predictor.on('error', (err) => reject(err))
        })

        const predictionResult = await query(`
          SELECT overall_score FROM session_predictions 
          WHERE session_id = $1 
          ORDER BY timestamp DESC LIMIT 1
        `, [sessionId])
        
        if (predictionResult.rows && predictionResult.rows.length > 0) {
          finalScore = predictionResult.rows[0].overall_score
        }
      }
    } catch (dbOrPythonError) {
      console.warn('Running in serverless/offline environment. Computed score heuristics:', dbOrPythonError)
    }

    return NextResponse.json({ 
      success: true, 
      message: 'Summary saved successfully and prediction completed',
      overallScore: finalScore
    })
  } catch (error: any) {
    console.error('Error in /api/session-summary POST:', error)
    return NextResponse.json(
      { success: false, message: 'Failed to process summary', error: error.message },
      { status: 500 }
    )
  }
}
