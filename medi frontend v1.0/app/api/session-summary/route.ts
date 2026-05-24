import { NextResponse } from 'next/server'
import { query } from '@/lib/db'
import { spawn } from 'child_process'
import path from 'path'

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const sessionId = searchParams.get('sessionId')

  if (!sessionId) {
    return NextResponse.json({ error: 'Session ID is required' }, { status: 400 })
  }

  try {
    // Fetch metrics summary from final_features
    const result = await query(`
      SELECT 
        avg(Alpha_Beta_Ratio) as alphabetamean,
        stddev(Alpha_Beta_Ratio) as alphabetastd,
        avg(RMSSD) as rmssdmean,
        stddev(RMSSD) as rmssdstd
      FROM final_features
      WHERE session_id = $1
    `, [sessionId])

    console.log(`Summary query for ${sessionId}:`, result.rows)

    const row = result.rows[0]
    const summary = {
      alphaBetaMean: parseFloat(row?.alphabetamean || 0),
      alphaBetaStd: parseFloat(row?.alphabetastd || 0),
      rmssdMean: parseFloat(row?.rmssdmean || 0),
      rmssdStd: parseFloat(row?.rmssdstd || 0),
    }

    return NextResponse.json(summary)
  } catch (error: any) {
    console.error('Database Error:', error)
    return NextResponse.json({ error: error.message }, { status: 500 })
  }
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

    // Create table if not exists
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

    // Insert data
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

    // Trigger the Machine Learning Model Prediction Script synchronously
    const rootDir = path.resolve(process.cwd(), '..')
    const pythonPath = path.join(rootDir, '.venv', 'bin', 'python')
    
    await new Promise((resolve, reject) => {
      const predictor = spawn(pythonPath, [
        path.join(rootDir, 'run_model_prediction.py'),
        '--session-id', sessionId
      ], { cwd: rootDir })
      
      predictor.on('close', (code) => resolve(code))
      predictor.on('error', (err) => reject(err))
    })

    // Fetch the newly calculated score from QuestDB
    let finalScore = qualityScore
    try {
      const predictionResult = await query(`
        SELECT overall_score FROM session_predictions 
        WHERE session_id = $1 
        ORDER BY timestamp DESC LIMIT 1
      `, [sessionId])
      
      if (predictionResult.rows && predictionResult.rows.length > 0) {
        finalScore = predictionResult.rows[0].overall_score
      }
    } catch (dbError) {
      console.error("Could not fetch overall score, falling back to qualityScore", dbError)
    }

    return NextResponse.json({ 
      success: true, 
      message: 'Summary saved successfully and prediction completed',
      overallScore: finalScore
    })
  } catch (error: any) {
    console.error('Database Error:', error)
    return NextResponse.json(
      { success: false, message: 'Failed to save summary', error: error.message },
      { status: 500 }
    )
  }
}
