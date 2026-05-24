"use client"

import { useState } from "react"
import { MeditationForm, SessionConfig } from "@/components/meditation-form"
import { MeditationSession } from "@/components/meditation-session"
import { SelfReport, ReportResponses } from "@/components/self-report"
import { MeditationSummary } from "@/components/meditation-summary"
import { BackgroundAnimation } from "@/components/background-animation"
import { Sparkles } from "lucide-react"

type AppView = "form" | "session" | "report" | "summary"

function generateSessionId() {
  const timestamp = Date.now().toString(36).toUpperCase()
  const random = Math.random().toString(36).substring(2, 8).toUpperCase()
  return `MF-${timestamp}-${random}`
}

export default function MeditationStartPage() {
  const [currentView, setCurrentView] = useState<AppView>("form")
  const [isStarting, setIsStarting] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [sessionConfig, setSessionConfig] = useState<SessionConfig | null>(null)
  const [sessionId, setSessionId] = useState<string>("")
  const [sessionStartTime, setSessionStartTime] = useState<Date | null>(null)
  const [reportResponses, setReportResponses] = useState<ReportResponses | null>(null)

  const handleStart = async (config: SessionConfig) => {
    setIsStarting(true)
    const newSessionId = generateSessionId()
    setSessionConfig(config)
    setSessionId(newSessionId)
    setSessionStartTime(new Date())
    
    try {
      const response = await fetch('/api/meditation', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...config,
          sessionId: newSessionId,
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to save session data')
      }

      console.log('Session data saved successfully')

      // 3. Start real-time data generation and processing
      await fetch('/api/meditation/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          sessionId: newSessionId,
          duration: config.duration,
          meditationType: config.meditationType,
        }),
      })
      
      console.log('Real-time processes started')
    } catch (error) {
      console.error('Error saving session data:', error)
      // We continue anyway so the user can meditate, but we log the error
    }

    // Brief transition delay before starting session
    setTimeout(() => {
      setIsStarting(false)
      setCurrentView("session")
    }, 1500)
  }

  const handleEndSession = () => {
    setCurrentView("form")
    setSessionConfig(null)
    setSessionId("")
    setSessionStartTime(null)
    setReportResponses(null)
  }

  const handleSessionComplete = () => {
    setCurrentView("report")
  }

  const handleReportSubmit = async (responses: ReportResponses, qualityScore: number) => {
    setIsSubmitting(true)
    setReportResponses(responses)
    
    try {
      const response = await fetch('/api/report', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...responses,
          sessionId: sessionId,
          qualityScore: qualityScore,
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to save report data')
      }

      console.log('Report data saved successfully')
    } catch (error) {
      console.error('Error saving report data:', error)
    }

    // Simulate submission
    setTimeout(() => {
      setIsSubmitting(false)
      setCurrentView("summary")
    }, 1500)
  }

  const handleNewSession = () => {
    setCurrentView("form")
    setSessionConfig(null)
    setSessionId("")
    setSessionStartTime(null)
    setReportResponses(null)
  }

  return (
    <main className="relative min-h-screen overflow-hidden">
      <BackgroundAnimation />
      
      {currentView === "form" && (
        <div className="relative z-10 flex min-h-screen flex-col items-center justify-center px-4 py-12">
          {/* Header */}
          <header className="mb-8 text-center">
            <div className="mb-4 flex items-center justify-center gap-2">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/20">
                <Sparkles className="h-6 w-6 text-primary" />
              </div>
            </div>
            <h1 className="font-[family-name:var(--font-playfair)] text-4xl font-semibold tracking-tight text-foreground md:text-5xl">
              MindFlow
            </h1>
            <p className="mt-2 text-muted-foreground">
              Measure and elevate your meditation practice
            </p>
          </header>

          {/* Main Form Card */}
          <MeditationForm onStart={handleStart} isStarting={isStarting} />

          {/* Footer */}
          <footer className="mt-8 text-center text-sm text-muted-foreground">
            <p>Find your inner peace. One breath at a time.</p>
          </footer>
        </div>
      )}

      {currentView === "session" && sessionConfig && (
        <div className="relative z-10">
          <MeditationSession 
            sessionId={sessionId}
            config={sessionConfig} 
            onEnd={handleEndSession}
            onComplete={handleSessionComplete}
          />
        </div>
      )}

      {currentView === "report" && sessionConfig && (
        <div className="relative z-10">
          <SelfReport 
            onSubmit={handleReportSubmit}
            isSubmitting={isSubmitting}
            meditationType={sessionConfig.meditationType}
          />
        </div>
      )}

      {currentView === "summary" && sessionConfig && reportResponses && sessionStartTime && (
        <div className="relative z-10">
          <MeditationSummary
            sessionId={sessionId}
            config={sessionConfig}
            responses={reportResponses}
            sessionStartTime={sessionStartTime}
            onNewSession={handleNewSession}
          />
        </div>
      )}
    </main>
  )
}
