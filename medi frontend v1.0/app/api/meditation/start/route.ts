import { NextResponse } from 'next/server'
import { spawn } from 'child_process'
import path from 'path'

export async function POST(request: Request) {
  try {
    const body = await request.json()
    const { sessionId, duration: durationMinutes, meditationType } = body
    const duration = durationMinutes * 60 // Convert minutes to seconds

    // Map meditation type to generator state
    let state = 'relaxed'
    if (['focused', 'mantra', 'spiritual'].includes(meditationType)) {
      state = 'focused'
    } else if (meditationType === 'stress-test') {
      state = 'stress'
    }

    // Path to the root directory (where Python scripts are)
    const rootDir = path.resolve(process.cwd(), '..')
    
    // Command to run (using the virtual environment python)
    const pythonPath = path.join(rootDir, '.venv', 'bin', 'python')

    console.log(`Starting meditation session ${sessionId} for ${duration}s...`)

    // 1. Start Generator
    const generator = spawn(pythonPath, [
      path.join(rootDir, 'eeg_heartbeat_generator.py'),
      '--duration', duration.toString(),
      '--state', state
    ], { cwd: rootDir, detached: true, stdio: 'ignore' })
    generator.unref()

    // 2. Start EEG Processor
    const eegProcessor = spawn(pythonPath, [
      path.join(rootDir, 'eeg_processor_questdb.py'),
      '--session-id', sessionId,
      '--duration', duration.toString()
    ], { cwd: rootDir, detached: true, stdio: 'ignore' })
    eegProcessor.unref()

    // 3. Start HRV Processor
    const hrvProcessor = spawn(pythonPath, [
      path.join(rootDir, 'hrv_processor_questdb.py'),
      '--session-id', sessionId,
      '--duration', duration.toString()
    ], { cwd: rootDir, detached: true, stdio: 'ignore' })
    hrvProcessor.unref()

    // 4. Start Final Features Aggregator
    const aggregator = spawn(pythonPath, [
      path.join(rootDir, 'final_features_aggregator.py'),
      '--session-id', sessionId,
      '--duration', duration.toString(),
      '--meditation-type', meditationType
    ], { cwd: rootDir, detached: true, stdio: 'ignore' })
    aggregator.unref()

    // 5. Start Meditation Quality Monitor (Calmness)
    const qualityMonitor = spawn(pythonPath, [
      path.join(rootDir, 'meditation_quality_monitor.py'),
      '--session-id', sessionId,
      '--duration', duration.toString()
    ], { cwd: rootDir, detached: true, stdio: 'ignore' })
    qualityMonitor.unref()

    return NextResponse.json({ 
      success: true, 
      message: 'Meditation processes started',
      details: { sessionId, duration, state }
    })
  } catch (error: any) {
    console.error('Error starting meditation processes:', error)
    return NextResponse.json({ success: false, error: error.message }, { status: 500 })
  }
}
