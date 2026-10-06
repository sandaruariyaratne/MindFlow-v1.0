"use client"

import { useState, useEffect, useRef } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { Slider } from "@/components/ui/slider"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  SelectGroup,
  SelectLabel,
  SelectSeparator,
} from "@/components/ui/select"
import {
  User,
  Brain,
  Clock,
  Award,
  Volume2,
  VolumeX,
  Headphones,
  Play,
  Loader2,
  Waves,
  CloudRain,
  TreePine,
  Bird,
  Wind,
  Flame,
  Music,
  Gauge,
} from "lucide-react"

const MEDITATION_TYPES = [
  { value: "mindfulness", label: "Mindfulness Meditation", icon: Brain },
  { value: "loving-kindness", label: "Loving-Kindness Meditation", icon: Brain },
  { value: "body-scan", label: "Body Scan Meditation", icon: Brain },
  { value: "spiritual", label: "Spiritual Meditation", icon: Brain },
  { value: "focused", label: "Focused Meditation", icon: Brain },
  { value: "mantra", label: "Mantra Meditation", icon: Brain },
]

const EXPERT_LEVELS = [
  { value: "beginner", label: "Beginner", description: "Just starting out" },
  { value: "intermediate", label: "Intermediate", description: "Some experience" },
  { value: "advanced", label: "Advanced", description: "Regular practitioner" },
  { value: "expert", label: "Expert", description: "Seasoned meditator" },
]

const DURATION_OPTIONS = [
  { value: 5, label: "5 min" },
  { value: 10, label: "10 min" },
  { value: 15, label: "15 min" },
  { value: 20, label: "20 min" },
  { value: 30, label: "30 min" },
  { value: 45, label: "45 min" },
  { value: 60, label: "60 min" },
]

const BACKGROUND_SOUNDS = {
  none: { label: "None", icon: VolumeX },
  nature: {
    label: "Nature Sounds",
    icon: TreePine,
    options: [
      { value: "ocean-waves", label: "Ocean Waves", icon: Waves },
      { value: "rain-sounds", label: "Rain Sounds", icon: CloudRain },
      { value: "waterfall", label: "Waterfalls", icon: Waves },
      { value: "forest-ambience", label: "Forest Ambience", icon: TreePine },
      { value: "birds-chirping", label: "Birds Chirping", icon: Bird },
      { value: "wind-sounds", label: "Wind Sounds", icon: Wind },
      { value: "crackling-fire", label: "Crackling Fire", icon: Flame },
    ],
  },
  ambient: {
    label: "Ambient Music",
    icon: Music,
    options: [
      { value: "synth-pads", label: "Synth Pads", icon: Music },
      { value: "gentle-piano", label: "Gentle Piano", icon: Music },
      { value: "cinematic-ambient", label: "Cinematic Ambient", icon: Music },
    ],
  },
  noise: {
    label: "Noise",
    icon: Headphones,
    options: [
      { value: "pink-noise", label: "Pink Noise", icon: Headphones },
      { value: "brown-noise", label: "Brown Noise", icon: Headphones },
    ],
  },
}

export interface SessionConfig {
  name: string
  age: string
  gender: string
  meditationType: string
  duration: number
  expertLevel: string
  backgroundSound: string
  masterVolume: number
  backgroundVolume: number
  playbackSpeed: number
}

interface MeditationFormProps {
  onStart: (config: SessionConfig) => void
  isStarting: boolean
}

export function MeditationForm({ onStart, isStarting }: MeditationFormProps) {
  const [name, setName] = useState("")
  const [age, setAge] = useState("")
  const [gender, setGender] = useState("")
  const [meditationType, setMeditationType] = useState("")
  const [duration, setDuration] = useState<number | null>(15)
  const [customDuration, setCustomDuration] = useState("")
  const [isCustomDuration, setIsCustomDuration] = useState(false)
  const [expertLevel, setExpertLevel] = useState("")
  const [backgroundSound, setBackgroundSound] = useState("none")
  const [masterVolume, setMasterVolume] = useState([70])
  const [backgroundVolume, setBackgroundVolume] = useState([50])
  const [playbackSpeed, setPlaybackSpeed] = useState([1.0])
  const previewAudioRef = useRef<HTMLAudioElement | null>(null)

  const effectiveDuration = isCustomDuration ? parseInt(customDuration) || 0 : duration
  const isFormValid = name && age && gender && meditationType && expertLevel && effectiveDuration > 0

  // Sound Preview Logic
  useEffect(() => {
    // Cleanup previous audio
    if (previewAudioRef.current) {
      previewAudioRef.current.pause()
      previewAudioRef.current.src = ""
      previewAudioRef.current = null
    }

    if (backgroundSound === "none" || isStarting) return

    const audio = new Audio(`/sounds/${backgroundSound}.mp3`)
    audio.loop = true
    previewAudioRef.current = audio
    
    // Apply current settings to preview
    audio.volume = (masterVolume[0] / 100) * (backgroundVolume[0] / 100)
    audio.playbackRate = playbackSpeed[0]
    
    audio.play().catch(err => console.error("Preview failed:", err))

    return () => {
      audio.pause()
      audio.src = ""
    }
  }, [backgroundSound, isStarting])

  // Update preview volume/speed in real-time
  useEffect(() => {
    if (previewAudioRef.current) {
      previewAudioRef.current.volume = (masterVolume[0] / 100) * (backgroundVolume[0] / 100)
      previewAudioRef.current.playbackRate = playbackSpeed[0]
    }
  }, [masterVolume, backgroundVolume, playbackSpeed])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (isFormValid && effectiveDuration) {
      onStart({
        name,
        age,
        gender,
        meditationType,
        duration: effectiveDuration,
        expertLevel,
        backgroundSound,
        masterVolume: masterVolume[0],
        backgroundVolume: backgroundVolume[0],
        playbackSpeed: playbackSpeed[0],
      })
    }
  }

  return (
    <Card className="w-full max-w-2xl border-border/50 bg-card/80 backdrop-blur-sm">
      <CardHeader className="text-center">
        <CardTitle className="text-xl text-foreground">Configure Your Session</CardTitle>
        <CardDescription>
          Customize your meditation experience for optimal quality measurement
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Personal Information */}
          <div className="space-y-4">
            <h3 className="flex items-center gap-2 text-sm font-medium text-foreground">
              <User className="h-4 w-4 text-primary" />
              Personal Information
            </h3>
            <div className="grid gap-4 sm:grid-cols-3">
              {/* Name */}
              <div className="space-y-2">
                <Label htmlFor="name" className="text-sm text-muted-foreground">
                  Name
                </Label>
                <Input
                  id="name"
                  placeholder="Your name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="bg-input/50 border-border/50 text-foreground placeholder:text-muted-foreground"
                />
              </div>

              {/* Age */}
              <div className="space-y-2">
                <Label htmlFor="age" className="text-sm text-muted-foreground">
                  Age
                </Label>
                <Input
                  id="age"
                  type="number"
                  placeholder="Age"
                  min={1}
                  max={120}
                  value={age}
                  onChange={(e) => setAge(e.target.value)}
                  className="bg-input/50 border-border/50 text-foreground placeholder:text-muted-foreground"
                />
              </div>

              {/* Gender */}
              <div className="space-y-2">
                <Label className="text-sm text-muted-foreground">
                  Gender
                </Label>
                <Select value={gender} onValueChange={setGender}>
                  <SelectTrigger className="w-full bg-input/50 border-border/50 text-foreground">
                    <SelectValue placeholder="Select" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="male">Male</SelectItem>
                    <SelectItem value="female">Female</SelectItem>
                    <SelectItem value="non-binary">Non-binary</SelectItem>
                    <SelectItem value="prefer-not-to-say">Prefer not to say</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>

          {/* Meditation Type & Duration Row */}
          <div className="grid gap-4 sm:grid-cols-2">
            {/* Meditation Type */}
            <div className="space-y-2">
              <Label className="flex items-center gap-2 text-foreground">
                <Brain className="h-4 w-4 text-primary" />
                Meditation Type
              </Label>
              <Select value={meditationType} onValueChange={setMeditationType}>
                <SelectTrigger className="w-full bg-input/50 border-border/50 text-foreground">
                  <SelectValue placeholder="Select type" />
                </SelectTrigger>
                <SelectContent>
                  {MEDITATION_TYPES.map((type) => (
                    <SelectItem key={type.value} value={type.value}>
                      {type.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Expert Level */}
            <div className="space-y-2">
              <Label className="flex items-center gap-2 text-foreground">
                <Award className="h-4 w-4 text-primary" />
                Experience Level
              </Label>
              <Select value={expertLevel} onValueChange={setExpertLevel}>
                <SelectTrigger className="w-full bg-input/50 border-border/50 text-foreground">
                  <SelectValue placeholder="Select level" />
                </SelectTrigger>
                <SelectContent>
                  {EXPERT_LEVELS.map((level) => (
                    <SelectItem key={level.value} value={level.value}>
                      <div className="flex flex-col">
                        <span>{level.label}</span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Session Duration */}
          <div className="space-y-3">
            <Label className="flex items-center gap-2 text-foreground">
              <Clock className="h-4 w-4 text-primary" />
              Session Duration
            </Label>
            <div className="flex flex-wrap gap-2">
              {DURATION_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => {
                    setDuration(opt.value)
                    setIsCustomDuration(false)
                    setCustomDuration("")
                  }}
                  className={`rounded-lg px-4 py-2 text-sm font-medium transition-all ${
                    !isCustomDuration && duration === opt.value
                      ? "bg-primary text-primary-foreground shadow-md"
                      : "bg-secondary/50 text-secondary-foreground hover:bg-secondary"
                  }`}
                >
                  {opt.label}
                </button>
              ))}
              <button
                type="button"
                onClick={() => {
                  setIsCustomDuration(true)
                  setDuration(null)
                }}
                className={`rounded-lg px-4 py-2 text-sm font-medium transition-all ${
                  isCustomDuration
                    ? "bg-primary text-primary-foreground shadow-md"
                    : "bg-secondary/50 text-secondary-foreground hover:bg-secondary"
                }`}
              >
                Custom
              </button>
            </div>
            
            {isCustomDuration && (
              <div className="flex items-center gap-3 pt-2">
                <Input
                  type="number"
                  placeholder="Enter duration"
                  min={1}
                  max={180}
                  value={customDuration}
                  onChange={(e) => setCustomDuration(e.target.value)}
                  className="w-32 bg-input/50 border-border/50 text-foreground placeholder:text-muted-foreground"
                />
                <span className="text-sm text-muted-foreground">minutes</span>
              </div>
            )}
          </div>

          {/* Background Sound */}
          <div className="space-y-3">
            <Label className="flex items-center gap-2 text-foreground">
              <Headphones className="h-4 w-4 text-primary" />
              Background Sound
            </Label>
            <Select value={backgroundSound} onValueChange={setBackgroundSound}>
              <SelectTrigger className="w-full bg-input/50 border-border/50 text-foreground">
                <SelectValue placeholder="Select background sound" />
              </SelectTrigger>
              <SelectContent className="max-h-[300px]">
                <SelectItem value="none">
                  <span className="flex items-center gap-2">
                    <VolumeX className="h-4 w-4" />
                    None
                  </span>
                </SelectItem>
                <SelectSeparator />
                
                <SelectGroup>
                  <SelectLabel className="flex items-center gap-2">
                    <TreePine className="h-3 w-3" />
                    Nature Sounds
                  </SelectLabel>
                  {BACKGROUND_SOUNDS.nature.options.map((sound) => (
                    <SelectItem key={sound.value} value={sound.value}>
                      <span className="flex items-center gap-2">
                        <sound.icon className="h-4 w-4" />
                        {sound.label}
                      </span>
                    </SelectItem>
                  ))}
                </SelectGroup>
                <SelectSeparator />
                
                <SelectGroup>
                  <SelectLabel className="flex items-center gap-2">
                    <Music className="h-3 w-3" />
                    Ambient Music
                  </SelectLabel>
                  {BACKGROUND_SOUNDS.ambient.options.map((sound) => (
                    <SelectItem key={sound.value} value={sound.value}>
                      <span className="flex items-center gap-2">
                        <sound.icon className="h-4 w-4" />
                        {sound.label}
                      </span>
                    </SelectItem>
                  ))}
                </SelectGroup>
                <SelectSeparator />
                
                <SelectGroup>
                  <SelectLabel className="flex items-center gap-2">
                    <Headphones className="h-3 w-3" />
                    Noise
                  </SelectLabel>
                  {BACKGROUND_SOUNDS.noise.options.map((sound) => (
                    <SelectItem key={sound.value} value={sound.value}>
                      <span className="flex items-center gap-2">
                        <sound.icon className="h-4 w-4" />
                        {sound.label}
                      </span>
                    </SelectItem>
                  ))}
                </SelectGroup>
              </SelectContent>
            </Select>
          </div>

          {/* Volume Controls */}
          <div className="space-y-4 rounded-lg bg-secondary/30 p-4">
            <h3 className="flex items-center gap-2 text-sm font-medium text-foreground">
              <Volume2 className="h-4 w-4 text-primary" />
              Volume Controls
            </h3>
            
            <div className="space-y-4">
              {/* Master Volume */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label className="text-sm text-muted-foreground">Master Volume</Label>
                  <span className="text-sm font-medium text-foreground">{masterVolume[0]}%</span>
                </div>
                <Slider
                  value={masterVolume}
                  onValueChange={setMasterVolume}
                  max={100}
                  step={1}
                  className="w-full"
                />
              </div>

              {/* Background Sound Volume */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label className="text-sm text-muted-foreground">Background Sound</Label>
                  <span className="text-sm font-medium text-foreground">{backgroundVolume[0]}%</span>
                </div>
                <Slider
                  value={backgroundVolume}
                  onValueChange={setBackgroundVolume}
                  max={100}
                  step={1}
                  disabled={backgroundSound === "none"}
                  className="w-full"
                />
              </div>

              {/* Playback Speed */}
              <div className="space-y-2 pt-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Gauge className="h-3.5 w-3.5 text-primary" />
                    <Label className="text-sm text-muted-foreground">Playback Speed</Label>
                  </div>
                  <span className="text-sm font-medium text-foreground">{playbackSpeed[0].toFixed(1)}x</span>
                </div>
                <Slider
                  value={playbackSpeed}
                  onValueChange={setPlaybackSpeed}
                  min={0.5}
                  max={2.0}
                  step={0.1}
                  disabled={backgroundSound === "none"}
                  className="w-full"
                />
                <div className="flex justify-between px-1 text-[10px] text-muted-foreground">
                  <span>Slower</span>
                  <span>Normal</span>
                  <span>Faster</span>
                </div>
              </div>
            </div>
          </div>

          {/* Start Button */}
          <Button
            type="submit"
            size="lg"
            className="w-full gap-2 text-base font-semibold"
            disabled={!isFormValid || isStarting}
          >
            {isStarting ? (
              <>
                <Loader2 className="h-5 w-5 animate-spin" />
                Preparing Session...
              </>
            ) : (
              <>
                <Play className="h-5 w-5" />
                Start Meditation
              </>
            )}
          </Button>

          {!isFormValid && (
            <p className="text-center text-sm text-muted-foreground">
              Please fill in all required fields to begin
            </p>
          )}
        </form>
      </CardContent>
    </Card>
  )
}
