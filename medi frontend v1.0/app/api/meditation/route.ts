import { NextResponse } from 'next/server'
import { query } from '@/lib/db'
import { registerSimulationSession } from '@/lib/simulation'

export async function POST(request: Request) {
  try {
    const body = await request.json()
    const {
      sessionId,
      name,
      age,
      gender,
      meditationType,
      duration,
      expertLevel,
      backgroundSound,
      masterVolume,
      backgroundVolume,
    } = body

    // Register session in simulation memory as immediate fallback
    registerSimulationSession({
      sessionId,
      durationSeconds: (parseInt(duration) || 5) * 60,
      meditationType: meditationType || 'mindfulness',
      name,
      age: parseInt(age) || undefined,
      gender,
      expertLevel,
      backgroundSound,
    })

    try {
      // Create table if not exists in QuestDB
      await query(`
        CREATE TABLE IF NOT EXISTS meditation_sessions (
          timestamp TIMESTAMP,
          sessionId STRING,
          name STRING,
          age INT,
          gender STRING,
          meditationType STRING,
          duration INT,
          expertLevel STRING,
          backgroundSound STRING,
          masterVolume INT,
          backgroundVolume INT
        ) timestamp(timestamp) PARTITION BY DAY;
      `)

      // Insert data
      await query(`
        INSERT INTO meditation_sessions (
          timestamp, sessionId, name, age, gender, 
          meditationType, duration, expertLevel, 
          backgroundSound, masterVolume, backgroundVolume
        ) VALUES (
          $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11
        )
      `, [
        new Date(),
        sessionId,
        name,
        parseInt(age),
        gender,
        meditationType,
        duration,
        expertLevel,
        backgroundSound,
        masterVolume,
        backgroundVolume,
      ])
    } catch (dbError) {
      console.warn('QuestDB offline or unreachable, continuing in cloud simulation mode:', dbError)
    }

    return NextResponse.json({ success: true, message: 'Data saved successfully' })
  } catch (error: any) {
    console.error('API Error in /api/meditation:', error)
    return NextResponse.json(
      { success: false, message: 'Failed to process meditation setup', error: error.message },
      { status: 500 }
    )
  }
}
