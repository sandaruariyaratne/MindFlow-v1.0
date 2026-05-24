import { NextResponse } from 'next/server'
import { query } from '@/lib/db'

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

    // Create table if not exists
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

    return NextResponse.json({ success: true, message: 'Data saved successfully' })
  } catch (error: any) {
    console.error('Database Error:', error)
    return NextResponse.json(
      { success: false, message: 'Failed to save data', error: error.message },
      { status: 500 }
    )
  }
}
