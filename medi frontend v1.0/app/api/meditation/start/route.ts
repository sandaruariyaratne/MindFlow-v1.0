import { NextResponse } from 'next/server'
import { spawn } from 'child_process'
import path from 'path'
import { registerSimulationSession } from '@/lib/simulation'

export async function POST(request: Request) {
  try {
    const body = await request.json()
    const { sessionId, duration: durationMinutes, meditationType } = body
    const duration = durationMinutes * 60 // Convert minutes to seconds

    // Register session in simulation memory
    registerSimulationSession({
      sessionId,
      startTime: Date.now(),
      durationSeconds: duration,
      meditationType,
    })

    // Map meditation type to generator state
    let state = 'relaxed'
    if (['focused', 'mantra', 'spiritual'].includes(meditationType)) {
      state = 'focused'
    } else if (meditationType === 'stress-test') {
      state = 'stress'
    }

    // Path to the root directory (where Python scripts are)
    const rootDir = path.resolve(process.cwd(), '..')
    const pythonPath = path.join(rootDir, '.venv', 'bin', 'python')
    const logPath = path.join(rootDir, 'pipeline.log')
    const fs = await import('fs')

    // Detect if we are on a serverless/cloud environment where Python .venv is absent
    const isVercel = process.env.VERCEL === '1' || Boolean(process.env.NEXT_PUBLIC_VERCEL_ENV)
    const pythonAvailable = !isVercel && fs.existsSync(pythonPath)

    if (pythonAvailable) {
      const logFd = fs.openSync(logPath, 'a')
      console.log(`Starting meditation session ${sessionId} for ${duration}s... Logs at: ${logPath}`)

      // 1. Start Generator
      const generator = spawn(pythonPath, [
        path.join(rootDir, 'eeg_heartbeat_generator.py'),
        '--duration', duration.toString(),
        '--state', state
      ], { cwd: rootDir, detached: true, stdio: ['ignore', logFd, logFd] })
      generator.unref()

      // 2. Start EEG Processor
      const eegProcessor = spawn(pythonPath, [
        path.join(rootDir, 'eeg_processor_questdb.py'),
        '--session-id', sessionId,
        '--duration', duration.toString()
      ], { cwd: rootDir, detached: true, stdio: ['ignore', logFd, logFd] })
      eegProcessor.unref()

      // 3. Start HRV Processor
      const hrvProcessor = spawn(pythonPath, [
        path.join(rootDir, 'hrv_processor_questdb.py'),
        '--session-id', sessionId,
        '--duration', duration.toString()
      ], { cwd: rootDir, detached: true, stdio: ['ignore', logFd, logFd] })
      hrvProcessor.unref()

      // 4. Start Final Features Aggregator
      const aggregator = spawn(pythonPath, [
        path.join(rootDir, 'final_features_aggregator.py'),
        '--session-id', sessionId,
        '--duration', duration.toString(),
        '--meditation-type', meditationType
      ], { cwd: rootDir, detached: true, stdio: ['ignore', logFd, logFd] })
      aggregator.unref()

      // 5. Start Meditation Quality Monitor (Calmness)
      const qualityMonitor = spawn(pythonPath, [
        path.join(rootDir, 'meditation_quality_monitor.py'),
        '--session-id', sessionId,
        '--duration', duration.toString()
      ], { cwd: rootDir, detached: true, stdio: ['ignore', logFd, logFd] })
      qualityMonitor.unref()

      return NextResponse.json({ 
        success: true, 
        message: 'Meditation processes started',
        mode: 'native-daemon',
        details: { sessionId, duration, state }
      })
    } else {
      console.log(`Serverless environment detected: Running session ${sessionId} in cloud simulation mode.`)
      return NextResponse.json({ 
        success: true, 
        message: 'Meditation session started in cloud demonstration mode',
        mode: 'cloud-simulation',
        details: { sessionId, duration, state }
      })
    }
  } catch (error: any) {
    console.error('Error starting meditation processes:', error)
    return NextResponse.json({ success: false, error: error.message }, { status: 500 })
  }
}
