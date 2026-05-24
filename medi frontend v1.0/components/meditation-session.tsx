"use client"

import { useState, useEffect, useCallback, useRef } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Slider } from "@/components/ui/slider"
import { Label } from "@/components/ui/label"
import {
  Play,
  Pause,
  Volume2,
  VolumeX,
  Music,
  StopCircle,
  RotateCcw,
  Waves,
  CloudRain,
  TreePine,
  Bird,
  Wind,
  Flame,
  Headphones,
  Activity,
  ChevronLeft,
  ChevronRight,
  History,
  Gauge,
} from "lucide-react"
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
} from "recharts"

interface SessionConfig {
  name: string
  meditationType: string
  duration: number
  expertLevel: string
  backgroundSound: string
  masterVolume: number
  backgroundVolume: number
  playbackSpeed: number
}

interface MeditationSessionProps {
  sessionId: string
  config: SessionConfig
  onEnd: () => void
  onComplete: () => void
}

const SOUND_ICONS: Record<string, React.ElementType> = {
  "ocean-waves": Waves,
  "rain-sounds": CloudRain,
  "waterfall": Waves,
  "forest-ambience": TreePine,
  "birds-chirping": Bird,
  "wind-sounds": Wind,
  "crackling-fire": Flame,
  "synth-pads": Music,
  "gentle-piano": Music,
  "cinematic-ambient": Music,
  "pink-noise": Headphones,
  "brown-noise": Headphones,
  "none": VolumeX,
}

const SOUND_LABELS: Record<string, string> = {
  "ocean-waves": "Ocean Waves",
  "rain-sounds": "Rain Sounds",
  "waterfall": "Waterfalls",
  "forest-ambience": "Forest Ambience",
  "birds-chirping": "Birds Chirping",
  "wind-sounds": "Wind Sounds",
  "crackling-fire": "Crackling Fire",
  "synth-pads": "Synth Pads",
  "gentle-piano": "Gentle Piano",
  "cinematic-ambient": "Cinematic Ambient",
  "pink-noise": "Pink Noise",
  "brown-noise": "Brown Noise",
  "none": "None",
}

const MEDITATION_LABELS: Record<string, string> = {
  "mindfulness": "Mindfulness Meditation",
  "loving-kindness": "Loving-Kindness Meditation",
  "body-scan": "Body Scan Meditation",
  "spiritual": "Spiritual Meditation",
  "focused": "Focused Meditation",
  "mantra": "Mantra Meditation",
}

export function MeditationSession({ sessionId, config, onEnd, onComplete }: MeditationSessionProps) {
  const [timeRemaining, setTimeRemaining] = useState(config.duration * 60) // in seconds
  const [isPaused, setIsPaused] = useState(false)
  const [isSoundPlaying, setIsSoundPlaying] = useState(config.backgroundSound !== "none")
  const [masterVolume, setMasterVolume] = useState([config.masterVolume])
  const [backgroundVolume, setBackgroundVolume] = useState([config.backgroundVolume])
  const [playbackSpeed, setPlaybackSpeed] = useState([config.playbackSpeed])
  const [sessionComplete, setSessionComplete] = useState(false)
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const [calmnessData, setCalmnessData] = useState<any[]>([])
  const [allCalmnessData, setAllCalmnessData] = useState<any[]>([])
  const [isLive, setIsLive] = useState(true)
  const [viewIndex, setViewIndex] = useState(0) // Index for historical view

  // Timer logic
  useEffect(() => {
    if (isPaused || sessionComplete) return

    const interval = setInterval(() => {
      setTimeRemaining((prev) => {
        if (prev <= 1) {
          setSessionComplete(true)
          return 0
        }
        return prev - 1
      })
    }, 1000)

    return () => clearInterval(interval)
  }, [isPaused, sessionComplete])

  // Audio lifecycle management
  useEffect(() => {
    if (config.backgroundSound === "none") return

    const audio = new Audio(`/sounds/${config.backgroundSound}.mp3`)
    audio.loop = true
    audioRef.current = audio

    if (!isPaused && isSoundPlaying && !sessionComplete) {
      audio.play().catch(err => console.error("Audio playback failed:", err))
    }

    return () => {
      audio.pause()
      audio.src = ""
      audioRef.current = null
    }
  }, [config.backgroundSound])

  // Volume and Speed management
  useEffect(() => {
    const audio = audioRef.current
    if (!audio) return

    // Calculate effective volume (Master * Background %)
    const effectiveVolume = (masterVolume[0] / 100) * (backgroundVolume[0] / 100)
    audio.volume = effectiveVolume

    // Apply playback speed
    audio.playbackRate = playbackSpeed[0]

    if (isPaused || !isSoundPlaying || sessionComplete) {
      audio.pause()
    } else {
      audio.play().catch(err => console.error("Audio play failed:", err))
    }
  }, [masterVolume, backgroundVolume, isPaused, isSoundPlaying, sessionComplete, playbackSpeed])

  // Fetch real-time calmness data
  useEffect(() => {
    if (isPaused || sessionComplete) return

    const fetchCalmness = async () => {
      try {
        // Fetch ALL data for the session to allow scrolling
        const response = await fetch(`/api/calmness?sessionId=${sessionId}&all=true`)
        if (response.ok) {
          const data = await response.json()
          const formattedData = data.map((d: any) => ({
            ...d,
            time: new Date(d.timestamp).toLocaleTimeString([], { hour12: false, minute: '2-digit', second: '2-digit' })
          }))
          setAllCalmnessData(formattedData)
          
          if (isLive) {
            // Show latest 50
            setCalmnessData(formattedData.slice(-50))
            setViewIndex(Math.max(0, formattedData.length - 50))
          }
        }
      } catch (error) {
        console.error("Error fetching calmness data:", error)
      }
    }

    fetchCalmness()
    const interval = setInterval(fetchCalmness, 3000)
    return () => clearInterval(interval)
  }, [sessionId, isPaused, sessionComplete, isLive])

  // Handle manual scrolling
  const handleScroll = (direction: 'left' | 'right') => {
    setIsLive(false)
    const step = 10
    let newIndex = viewIndex
    
    if (direction === 'left') {
      newIndex = Math.max(0, viewIndex - step)
    } else {
      newIndex = Math.min(allCalmnessData.length - 50, viewIndex + step)
    }
    
    setViewIndex(newIndex)
    setCalmnessData(allCalmnessData.slice(newIndex, newIndex + 50))
  }

  const resetToLive = () => {
    setIsLive(true)
    setCalmnessData(allCalmnessData.slice(-50))
    setViewIndex(Math.max(0, allCalmnessData.length - 50))
  }

  // Format time as MM:SS
  const formatTime = useCallback((seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`
  }, [])

  // Calculate progress percentage
  const progressPercent = ((config.duration * 60 - timeRemaining) / (config.duration * 60)) * 100

  const togglePause = () => {
    setIsPaused(!isPaused)
  }

  const toggleSound = () => {
    setIsSoundPlaying(!isSoundPlaying)
  }

  const handleRestart = () => {
    setTimeRemaining(config.duration * 60)
    setIsPaused(false)
    setSessionComplete(false)
    setIsSoundPlaying(config.backgroundSound !== "none")
  }

  const SoundIcon = SOUND_ICONS[config.backgroundSound] || Music

  return (
    <div className="flex min-h-screen flex-col items-center justify-center px-4 py-8">
      {/* Session Info Header */}
      <div className="mb-8 text-center">
        <p className="text-sm text-muted-foreground">Welcome, {config.name}</p>
        <h2 className="mt-1 font-[family-name:var(--font-playfair)] text-2xl font-semibold text-foreground">
          {MEDITATION_LABELS[config.meditationType] || config.meditationType}
        </h2>
      </div>

      {/* Main Timer Card */}
      <Card className="w-full max-w-md border-border/50 bg-card/80 backdrop-blur-sm">
        <CardContent className="p-8">
          {/* Circular Timer Display */}
          <div className="relative mx-auto mb-8 flex h-64 w-64 items-center justify-center">
            {/* Background Circle */}
            <svg className="absolute h-full w-full -rotate-90">
              <circle
                cx="128"
                cy="128"
                r="120"
                fill="none"
                stroke="currentColor"
                strokeWidth="8"
                className="text-secondary/50"
              />
              {/* Progress Circle */}
              <circle
                cx="128"
                cy="128"
                r="120"
                fill="none"
                stroke="currentColor"
                strokeWidth="8"
                strokeLinecap="round"
                strokeDasharray={2 * Math.PI * 120}
                strokeDashoffset={2 * Math.PI * 120 * (1 - progressPercent / 100)}
                className="text-primary transition-all duration-1000"
              />
            </svg>
            
            {/* Timer Text */}
            <div className="relative z-10 text-center">
              <span className="font-[family-name:var(--font-playfair)] text-5xl font-bold text-foreground">
                {formatTime(timeRemaining)}
              </span>
              <p className="mt-2 text-sm text-muted-foreground">
                {sessionComplete ? "Session Complete" : isPaused ? "Paused" : "Remaining"}
              </p>
            </div>
          </div>

          {/* Session Status */}
          {sessionComplete ? (
            <div className="mb-6 rounded-lg bg-primary/20 p-4 text-center">
              <p className="font-medium text-primary">Congratulations!</p>
              <p className="mt-1 text-sm text-muted-foreground">
                You completed your {config.duration} minute session
              </p>
            </div>
          ) : (
            <div className="mb-6 flex items-center justify-center gap-2">
              <div className={`h-2 w-2 rounded-full ${isPaused ? "bg-amber-500" : "bg-emerald-500 animate-pulse"}`} />
              <span className="text-sm text-muted-foreground">
                {isPaused ? "Session Paused" : "Session Active"}
              </span>
            </div>
          )}

          {/* Main Controls */}
          <div className="mb-6 flex items-center justify-center gap-4">
            {!sessionComplete ? (
              <>
                <Button
                  variant="outline"
                  size="lg"
                  onClick={togglePause}
                  className="h-14 w-14 rounded-full border-border/50 bg-secondary/50 p-0"
                >
                  {isPaused ? (
                    <Play className="h-6 w-6" />
                  ) : (
                    <Pause className="h-6 w-6" />
                  )}
                </Button>
                <Button
                  variant="destructive"
                  size="lg"
                  onClick={onEnd}
                  className="h-14 px-6"
                >
                  <StopCircle className="mr-2 h-5 w-5" />
                  End Session
                </Button>
              </>
            ) : (
              <>
                <Button
                  variant="outline"
                  size="lg"
                  onClick={handleRestart}
                  className="h-14 px-6 border-border/50 bg-secondary/50"
                >
                  <RotateCcw className="mr-2 h-5 w-5" />
                  Restart
                </Button>
                <Button
                  size="lg"
                  onClick={onComplete}
                  className="h-14 px-6"
                >
                  Continue to Report
                </Button>
              </>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Real-time Calmness Chart */}
      <Card className="mt-6 w-full max-w-md border-border/50 bg-slate-950/90 backdrop-blur-md shadow-2xl">
        <CardContent className="p-4">
          <div className="mb-4 flex items-center justify-between px-2">
            <div className="flex items-center gap-2">
              <Activity className="h-4 w-4 text-primary" />
              <h3 className="text-sm font-semibold text-slate-200">Real-time Calmness Monitor</h3>
            </div>
            <div className="flex flex-col items-end">
              <div className="flex items-center gap-2">
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={() => isLive ? setIsLive(false) : resetToLive()}
                    className={`h-7 gap-1.5 px-3 text-[10px] font-semibold uppercase tracking-wider transition-colors ${!isLive ? 'border-primary bg-primary/10 text-primary' : 'border-border/50 bg-transparent text-slate-400'}`}
                  >
                    {!isLive ? <RotateCcw className="h-3 w-3" /> : <History className="h-3.5 w-3.5" />}
                    {isLive ? "View History" : "Back to Live"}
                  </Button>
                
                <div className="flex items-center gap-1.5 ml-1">
                  <span className="flex h-2 w-2 items-center justify-center">
                    <span className={`absolute h-2 w-2 rounded-full ${isLive ? "animate-ping bg-primary/40" : "bg-slate-700"}`} />
                    <span className={`relative h-1.5 w-1.5 rounded-full ${isLive ? "bg-primary" : "bg-slate-500"}`} />
                  </span>
                  <span className="text-[10px] font-medium uppercase tracking-wider text-slate-400">
                    {isLive ? "Live" : "Paused"}
                  </span>
                </div>
              </div>
              {calmnessData.length > 0 && (
                <div className="mt-0.5 text-lg font-bold text-primary">
                  {calmnessData[calmnessData.length - 1].score.toFixed(0)}%
                </div>
              )}
            </div>
          </div>
          
          <div className="relative h-[200px] w-full">
            {/* Scroll Buttons - More Visible */}
            <div className="absolute inset-y-0 -left-4 z-10 flex items-center">
              <Button
                variant="secondary"
                size="icon"
                onClick={() => handleScroll('left')}
                disabled={viewIndex === 0}
                className={`h-10 w-10 rounded-full border-2 border-primary/20 bg-slate-900 shadow-xl transition-all ${viewIndex === 0 ? 'opacity-20' : 'opacity-100 hover:scale-110 hover:border-primary'}`}
              >
                <ChevronLeft className="h-6 w-6 text-primary" />
              </Button>
            </div>
            <div className="absolute inset-y-0 -right-4 z-10 flex items-center">
              <Button
                variant="secondary"
                size="icon"
                onClick={() => handleScroll('right')}
                disabled={isLive || viewIndex >= allCalmnessData.length - 50}
                className={`h-10 w-10 rounded-full border-2 border-primary/20 bg-slate-900 shadow-xl transition-all ${isLive || viewIndex >= allCalmnessData.length - 50 ? 'opacity-20' : 'opacity-100 hover:scale-110 hover:border-primary'}`}
              >
                <ChevronRight className="h-6 w-6 text-primary" />
              </Button>
            </div>

            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={calmnessData}>
                <defs>
                  <linearGradient id="colorScore" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                <XAxis 
                  dataKey="timestamp" 
                  hide={false}
                  axisLine={false}
                  tickLine={false}
                  fontSize={8}
                  stroke="#475569"
                  interval="preserveStartEnd"
                  minTickGap={30}
                  tickFormatter={(ts) => new Date(ts).toLocaleTimeString([], { hour12: false, minute: '2-digit', second: '2-digit' })}
                />
                <YAxis 
                  domain={[0, 100]} 
                  stroke="#64748b" 
                  fontSize={10}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={(val) => `${val}%`}
                />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#020617', border: '1px solid #1e293b', borderRadius: '8px' }}
                  itemStyle={{ color: '#10b981' }}
                  labelStyle={{ color: '#64748b', fontSize: '10px' }}
                />
                <Area
                  type="monotone"
                  dataKey="score"
                  stroke="#10b981"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#colorScore)"
                  animationDuration={1000}
                  isAnimationActive={true}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          
          <div className="mt-2 flex justify-between px-2 text-[10px] font-medium text-slate-500 uppercase tracking-widest">
            <span>Session Start</span>
            <span>Real-time Flow</span>
          </div>
        </CardContent>
      </Card>

      {/* Audio Controls Card */}
      <Card className="mt-6 w-full max-w-md border-border/50 bg-card/80 backdrop-blur-sm">
        <CardContent className="p-6">
          {/* Background Sound Control */}
          {config.backgroundSound !== "none" && (
            <div className="mb-6">
              <div className="mb-3 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <SoundIcon className="h-4 w-4 text-primary" />
                  <span className="text-sm font-medium text-foreground">
                    {SOUND_LABELS[config.backgroundSound]}
                  </span>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={toggleSound}
                  className="h-8 w-8 p-0"
                >
                  {isSoundPlaying ? (
                    <Pause className="h-4 w-4" />
                  ) : (
                    <Play className="h-4 w-4" />
                  )}
                </Button>
              </div>
              <div className="flex items-center gap-2 rounded-lg bg-secondary/30 px-3 py-2">
                <span className={`text-xs ${isSoundPlaying ? "text-emerald-500" : "text-muted-foreground"}`}>
                  {isSoundPlaying ? "Playing" : "Paused"}
                </span>
              </div>
            </div>
          )}

          {/* Volume Controls */}
          <div className="space-y-4">
            <h3 className="flex items-center gap-2 text-sm font-medium text-foreground">
              <Volume2 className="h-4 w-4 text-primary" />
              Volume Controls
            </h3>

            {/* Master Volume */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label className="text-sm text-muted-foreground">Master Volume</Label>
                <span className="text-sm font-medium text-foreground">{masterVolume[0]}%</span>
              </div>
              <div className="flex items-center gap-3">
                <VolumeX className="h-4 w-4 text-muted-foreground" />
                <Slider
                  value={masterVolume}
                  onValueChange={setMasterVolume}
                  max={100}
                  step={1}
                  className="flex-1"
                />
                <Volume2 className="h-4 w-4 text-muted-foreground" />
              </div>
            </div>

            {/* Background Sound Volume */}
            {config.backgroundSound !== "none" && (
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label className="text-sm text-muted-foreground">Background Sound</Label>
                  <span className="text-sm font-medium text-foreground">{backgroundVolume[0]}%</span>
                </div>
                <div className="flex items-center gap-3">
                  <VolumeX className="h-4 w-4 text-muted-foreground" />
                  <Slider
                    value={backgroundVolume}
                    onValueChange={setBackgroundVolume}
                    max={100}
                    step={1}
                    disabled={!isSoundPlaying}
                    className="flex-1"
                  />
                  <Volume2 className="h-4 w-4 text-muted-foreground" />
                </div>
              </div>
            )}

            {/* Playback Speed */}
            {config.backgroundSound !== "none" && (
              <div className="space-y-2 pt-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Gauge className="h-3.5 w-3.5 text-primary" />
                    <Label className="text-sm text-muted-foreground">Playback Speed</Label>
                  </div>
                  <span className="text-sm font-medium text-foreground">{playbackSpeed[0].toFixed(1)}x</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-[10px] text-muted-foreground w-8">Slow</span>
                  <Slider
                    value={playbackSpeed}
                    onValueChange={setPlaybackSpeed}
                    min={0.5}
                    max={2.0}
                    step={0.1}
                    disabled={!isSoundPlaying}
                    className="flex-1"
                  />
                  <span className="text-[10px] text-muted-foreground w-8 text-right">Fast</span>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Breathing Guide Hint */}
      {!sessionComplete && !isPaused && (
        <div className="mt-8 text-center">
          <p className="text-sm text-muted-foreground">
            Breathe deeply and let go of your thoughts
          </p>
          <div className="mt-3 flex items-center justify-center gap-1">
            <span className="h-1 w-1 animate-pulse rounded-full bg-primary/60" style={{ animationDelay: "0ms" }} />
            <span className="h-1 w-1 animate-pulse rounded-full bg-primary/60" style={{ animationDelay: "200ms" }} />
            <span className="h-1 w-1 animate-pulse rounded-full bg-primary/60" style={{ animationDelay: "400ms" }} />
          </div>
        </div>
      )}
    </div>
  )
}
