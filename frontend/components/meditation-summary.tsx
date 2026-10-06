"use client"

import { useEffect, useState, useRef } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import {
  User,
  Clock,
  Music,
  Brain,
  Activity,
  Heart,
  BarChart3,
  Calendar,
  Hash,
  Download,
  RotateCcw,
  Award,
  Loader2,
} from "lucide-react"
import { SessionConfig } from "./meditation-form"
import { ReportResponses, calculateQualityScore } from "./self-report"
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts"

interface MeditationSummaryProps {
  sessionId: string
  config: SessionConfig
  responses: ReportResponses
  sessionStartTime: Date
  onNewSession: () => void
}

interface Biometrics {
  alphaBetaMean: number
  alphaBetaStd: number
  rmssdMean: number
  rmssdStd: number
}

interface MetricCardProps {
  label: string
  value: string | number
  subValue?: string
  icon: React.ElementType
  highlight?: boolean
}

function MetricCard({ label, value, subValue, icon: Icon, highlight }: MetricCardProps) {
  return (
    <div className={`rounded-xl border p-4 ${highlight ? 'border-primary/50 bg-primary/10' : 'border-border/50 bg-secondary/30'}`}>
      <div className="flex items-start justify-between">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10">
          <Icon className={`h-4 w-4 ${highlight ? 'text-primary' : 'text-muted-foreground'}`} />
        </div>
        {highlight && (
          <Award className="h-5 w-5 text-primary" />
        )}
      </div>
      <div className="mt-3">
        <p className="text-xs text-muted-foreground">{label}</p>
        <p className={`text-xl font-semibold ${highlight ? 'text-primary' : 'text-foreground'}`}>{value}</p>
        {subValue && (
          <p className="text-xs text-muted-foreground mt-1">{subValue}</p>
        )}
      </div>
    </div>
  )
}

function StatRow({ label, mean, std }: { label: string; mean: string; std: string }) {
  return (
    <div className="flex items-center justify-between py-3 border-b border-border/30 last:border-0">
      <span className="text-sm text-muted-foreground">{label}</span>
      <div className="flex gap-6">
        <div className="text-right">
          <p className="text-xs text-muted-foreground">Mean</p>
          <p className="text-sm font-medium text-foreground">{mean}</p>
        </div>
        <div className="text-right">
          <p className="text-xs text-muted-foreground">Std</p>
          <p className="text-sm font-medium text-foreground">{std}</p>
        </div>
      </div>
    </div>
  )
}

const MEDITATION_TYPES: Record<string, string> = {
  mindfulness: "Mindfulness Meditation",
  "loving-kindness": "Loving-Kindness Meditation",
  "body-scan": "Body Scan Meditation",
  spiritual: "Spiritual Meditation",
  focused: "Focused Meditation",
  mantra: "Mantra Meditation",
}

const BACKGROUND_SOUNDS: Record<string, string> = {
  none: "None",
  "ocean-waves": "Ocean Waves",
  "rain-sounds": "Rain Sounds",
  waterfalls: "Waterfalls",
  "forest-ambience": "Forest Ambience",
  "birds-chirping": "Birds Chirping",
  "wind-sounds": "Wind Sounds",
  "crackling-fire": "Crackling Fire",
  "synth-pads": "Synth Pads",
  "soft-drones": "Soft Drones",
  "gentle-piano": "Gentle Piano",
  "cinematic-ambient": "Cinematic Ambient",
  "pink-noise": "Pink Noise",
  "brown-noise": "Brown Noise",
}

export function MeditationSummary({
  sessionId,
  config,
  responses,
  sessionStartTime,
  onNewSession,
}: MeditationSummaryProps) {
  const [biometrics, setBiometrics] = useState<Biometrics | null>(null)
  const [sessionData, setSessionData] = useState<{ features: any[], calmness: any[] } | null>(null)
  const [finalOverallScore, setFinalOverallScore] = useState<number | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // Calculate weighted quality score from self-report
  const qualityScore = calculateQualityScore(responses, config.meditationType)
  const displayScore = finalOverallScore !== null ? finalOverallScore.toFixed(1) : qualityScore.toFixed(1)
  
  const hasSaved = useRef(false)
  
  useEffect(() => {
    async function fetchAndSaveSummary() {
      if (hasSaved.current) return
      
      try {
        // 1. Fetch real biometric averages from processed tables
        const fetchResponse = await fetch(`/api/session-summary?sessionId=${sessionId}`)
        if (!fetchResponse.ok) throw new Error('Failed to fetch biometric data')
        const data = await fetchResponse.json()
        setBiometrics(data)

        // 2. Fetch detailed session data for graphs
        const detailsResponse = await fetch(`/api/session-details?sessionId=${sessionId}`)
        if (detailsResponse.ok) {
          const detailsData = await detailsResponse.json()
          setSessionData({
            features: detailsData.features.map((d: any) => ({
              ...d,
              time: new Date(d.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            })),
            calmness: detailsData.calmness.map((d: any) => ({
              ...d,
              time: new Date(d.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            }))
          })
        }

        // 3. Save final summary to meditation_summaries table
        const saveResponse = await fetch('/api/session-summary', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            sessionId,
            alphaBetaMean: data.alphaBetaMean,
            alphaBetaStd: data.alphaBetaStd,
            rmssdMean: data.rmssdMean,
            rmssdStd: data.rmssdStd,
            qualityScore: qualityScore,
          }),
        })

        if (saveResponse.ok) {
          hasSaved.current = true
          const saveData = await saveResponse.json()
          if (saveData.overallScore !== undefined) {
            setFinalOverallScore(saveData.overallScore)
          }
        }

      } catch (error) {
        console.error('Error fetching/saving summary:', error)
      } finally {
        setIsLoading(false)
      }
    }

    // Small delay to allow aggregator to finish its last loop
    const timer = setTimeout(fetchAndSaveSummary, 1000)
    return () => clearTimeout(timer)
  }, [sessionId, qualityScore])

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: true,
    })
  }

  const formatDate = (date: Date) => {
    return date.toLocaleDateString("en-US", {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
    })
  }

  const getScoreLabel = (score: number) => {
    if (score >= 8) return "Excellent"
    if (score >= 6) return "Good"
    if (score >= 4) return "Fair"
    return "Needs Improvement"
  }

  if (isLoading) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center">
        <Loader2 className="h-12 w-12 animate-spin text-primary" />
        <p className="mt-4 text-muted-foreground font-medium">Generating your session analysis...</p>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-start px-4 py-8">
      {/* Header */}
      <div className="mb-8 text-center">
        <div className="mb-4 flex items-center justify-center gap-2">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/20">
            <BarChart3 className="h-6 w-6 text-primary" />
          </div>
        </div>
        <h1 className="font-[family-name:var(--font-playfair)] text-3xl font-semibold tracking-tight text-foreground md:text-4xl">
          Session Summary
        </h1>
        <p className="mt-2 max-w-md text-muted-foreground">
          Here&apos;s a complete overview of your meditation session and biometric data.
        </p>
      </div>

      <div className="w-full max-w-4xl space-y-6">
        {/* Session Info Card */}
        <Card className="border-border/50 bg-card/80 backdrop-blur-sm">
          <CardContent className="p-6">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-6">
              <div>
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Hash className="h-4 w-4" />
                  <span className="text-xs uppercase tracking-wide">Session ID</span>
                </div>
                <p className="mt-1 font-mono text-lg font-semibold text-foreground">{sessionId}</p>
              </div>
              <div className="text-right">
                <div className="flex items-center justify-end gap-2 text-muted-foreground">
                  <Calendar className="h-4 w-4" />
                  <span className="text-xs uppercase tracking-wide">Date & Time</span>
                </div>
                <p className="mt-1 text-sm text-foreground">{formatDate(sessionStartTime)}</p>
                <p className="text-sm text-muted-foreground">{formatTime(sessionStartTime)}</p>
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <MetricCard label="Name" value={config.name} icon={User} />
              <MetricCard label="Age" value={config.age} subValue="years old" icon={User} />
              <MetricCard label="Gender" value={config.gender.charAt(0).toUpperCase() + config.gender.slice(1).replace(/-/g, ' ')} icon={User} />
              <MetricCard label="Experience" value={config.expertLevel.charAt(0).toUpperCase() + config.expertLevel.slice(1)} icon={Brain} />
            </div>
          </CardContent>
        </Card>

        {/* Meditation Details Card */}
        <Card className="border-border/50 bg-card/80 backdrop-blur-sm">
          <CardContent className="p-6">
            <h3 className="flex items-center gap-2 text-lg font-semibold text-foreground mb-4">
              <Clock className="h-5 w-5 text-primary" />
              Meditation Details
            </h3>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <MetricCard label="Meditation Type" value={MEDITATION_TYPES[config.meditationType] || config.meditationType} icon={Brain} />
              <MetricCard label="Duration" value={`${config.duration} min`} icon={Clock} />
              <MetricCard label="Background Sound" value={BACKGROUND_SOUNDS[config.backgroundSound] || "None"} icon={Music} />
            </div>
          </CardContent>
        </Card>

        {/* Overall Score Card */}
        <Card className="border-primary/30 bg-primary/5 backdrop-blur-sm">
          <CardContent className="p-6">
            <div className="flex flex-col items-center justify-center text-center">
              <div className="flex h-24 w-24 items-center justify-center rounded-full bg-primary/20 mb-4">
                <span className="text-4xl font-bold text-primary">{displayScore}</span>
              </div>
              <h3 className="text-xl font-semibold text-foreground">Overall Meditation Score</h3>
              <p className="text-muted-foreground mt-1">{getScoreLabel(parseFloat(displayScore))}</p>
              <div className="mt-4 flex flex-wrap justify-center gap-2">
                {Object.entries(responses).map(([key, value]) => (
                  <div key={key} className="rounded-full bg-secondary/50 px-3 py-1 text-xs" title={key.replace(/([A-Z])/g, ' $1').trim()}>
                    <span className="text-muted-foreground capitalize">{key.replace(/([A-Z])/g, ' $1').trim()}:</span> <span className="font-semibold text-foreground">{value}</span>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Biometric Data Card */}
        <Card className="border-border/50 bg-card/80 backdrop-blur-sm">
          <CardContent className="p-6">
            <h3 className="flex items-center gap-2 text-lg font-semibold text-foreground mb-4">
              <Activity className="h-5 w-5 text-primary" />
              Biometric Analysis
            </h3>
            
            <div className="grid gap-6 lg:grid-cols-2 mb-8">
              <div className="rounded-xl border border-border/50 bg-secondary/20 p-4">
                <div className="flex items-center gap-2 mb-3">
                  <Brain className="h-4 w-4 text-primary" />
                  <h4 className="font-medium text-foreground">Alpha/Beta Ratio</h4>
                </div>
                <StatRow 
                  label="Alpha/Beta Stats" 
                  mean={biometrics?.alphaBetaMean.toFixed(2) || "0.00"} 
                  std={biometrics?.alphaBetaStd.toFixed(2) || "0.00"} 
                />
                
                {/* Alpha/Beta Chart */}
                <div className="h-48 w-full mt-4">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={sessionData?.features || []}>
                      <defs>
                        <linearGradient id="colorAlpha" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#10b981" stopOpacity={0.2}/>
                          <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                      <XAxis dataKey="time" hide={true} />
                      <YAxis hide={true} domain={['auto', 'auto']} />
                      <Tooltip 
                        contentStyle={{ backgroundColor: '#0f172a', border: 'none', borderRadius: '8px', fontSize: '10px' }}
                        itemStyle={{ color: '#10b981' }}
                      />
                      <Area type="monotone" dataKey="alphabeta" stroke="#10b981" fillOpacity={1} fill="url(#colorAlpha)" />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="rounded-xl border border-border/50 bg-secondary/20 p-4">
                <div className="flex items-center gap-2 mb-3">
                  <Heart className="h-4 w-4 text-rose-500" />
                  <h4 className="font-medium text-foreground">RMSSD (HRV)</h4>
                </div>
                <StatRow 
                  label="RMSSD Stats" 
                  mean={`${biometrics?.rmssdMean.toFixed(1) || "0.0"} ms`} 
                  std={`${biometrics?.rmssdStd.toFixed(1) || "0.0"} ms`} 
                />
                
                {/* RMSSD Chart */}
                <div className="h-48 w-full mt-4">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={sessionData?.features || []}>
                      <defs>
                        <linearGradient id="colorRmssd" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.2}/>
                          <stop offset="95%" stopColor="#f43f5e" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                      <XAxis dataKey="time" hide={true} />
                      <YAxis hide={true} domain={['auto', 'auto']} />
                      <Tooltip 
                        contentStyle={{ backgroundColor: '#0f172a', border: 'none', borderRadius: '8px', fontSize: '10px' }}
                        itemStyle={{ color: '#f43f5e' }}
                      />
                      <Area type="monotone" dataKey="rmssd" stroke="#f43f5e" fillOpacity={1} fill="url(#colorRmssd)" />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>

            {/* Calmness Score Chart (Full Width) */}
            <div className="rounded-xl border border-border/50 bg-secondary/20 p-6">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-2">
                  <Activity className="h-5 w-5 text-sky-500" />
                  <h4 className="font-medium text-foreground text-lg">Calmness Score Trend</h4>
                </div>
                <div className="text-right">
                  <p className="text-xs text-muted-foreground uppercase tracking-wider">Session Progression</p>
                </div>
              </div>
              
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={sessionData?.calmness || []}>
                    <defs>
                      <linearGradient id="colorCalmness" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                    <XAxis 
                      dataKey="time" 
                      stroke="#475569" 
                      fontSize={10} 
                      tickLine={false} 
                      axisLine={false} 
                      interval="preserveStartEnd"
                    />
                    <YAxis 
                      domain={[0, 100]} 
                      stroke="#475569" 
                      fontSize={10} 
                      tickLine={false} 
                      axisLine={false} 
                      tickFormatter={(val) => `${val}%`}
                    />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#0f172a', border: 'none', borderRadius: '8px' }}
                      itemStyle={{ color: '#0ea5e9' }}
                    />
                    <Area 
                      type="monotone" 
                      dataKey="score" 
                      stroke="#0ea5e9" 
                      strokeWidth={3}
                      fillOpacity={1} 
                      fill="url(#colorCalmness)" 
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Action Buttons */}
        <div className="flex flex-col gap-4 sm:flex-row sm:justify-center pt-6">
          <Button variant="outline" size="lg" className="h-12 px-6" onClick={() => window.print()}>
            <Download className="mr-2 h-4 w-4" /> Export Report
          </Button>
          <Button size="lg" className="h-12 px-6" onClick={onNewSession}>
            <RotateCcw className="mr-2 h-4 w-4" /> Start New Session
          </Button>
        </div>
      </div>
    </div>
  )
}
