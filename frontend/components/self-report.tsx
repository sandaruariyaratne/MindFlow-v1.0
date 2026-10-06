"use client"

import { useState } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import {
  Brain,
  Focus,
  Compass,
  Heart,
  Eye,
  Sparkles,
  Target,
  Smile,
  Waves,
  Star,
  ChevronRight,
  CheckCircle2,
} from "lucide-react"

interface SelfReportProps {
  onSubmit: (responses: ReportResponses, qualityScore: number) => void
  isSubmitting: boolean
  meditationType: string
}

export interface ReportResponses {
  calmness: number
  focus: number
  mindWandering: number
  emotionalBalance: number
  presence: number
  mentalRefreshment: number
  attentionEase: number
  bodyRelaxation: number
  meditationDepth: number
  overallSatisfaction: number
}

interface Question {
  id: keyof ReportResponses
  icon: React.ElementType
  question: string
  lowLabel: string
  highLabel: string
}

const QUESTIONS: Question[] = [
  {
    id: "calmness",
    icon: Waves,
    question: "How calm do you feel right now?",
    lowLabel: "Very stressed",
    highLabel: "Extremely calm",
  },
  {
    id: "focus",
    icon: Focus,
    question: "How focused were you during the meditation?",
    lowLabel: "Constantly distracted",
    highLabel: "Fully focused",
  },
  {
    id: "mindWandering",
    icon: Compass,
    question: "How often did your mind wander?",
    lowLabel: "Very often",
    highLabel: "Rarely wandered",
  },
  {
    id: "emotionalBalance",
    icon: Heart,
    question: "How emotionally balanced do you feel after the session?",
    lowLabel: "Emotionally unstable",
    highLabel: "Very balanced",
  },
  {
    id: "presence",
    icon: Eye,
    question: "How present or aware did you feel during the session?",
    lowLabel: "Not present",
    highLabel: "Fully present",
  },
  {
    id: "mentalRefreshment",
    icon: Sparkles,
    question: "How mentally refreshed do you feel now?",
    lowLabel: "Mentally exhausted",
    highLabel: "Fully refreshed",
  },
  {
    id: "attentionEase",
    icon: Target,
    question: "How easy was it to maintain your attention on the meditation object?",
    lowLabel: "Very difficult",
    highLabel: "Very easy",
  },
  {
    id: "bodyRelaxation",
    icon: Smile,
    question: "How relaxed did your body feel during the session?",
    lowLabel: "Very tense",
    highLabel: "Deeply relaxed",
  },
  {
    id: "meditationDepth",
    icon: Brain,
    question: "How deep did the meditation feel to you personally?",
    lowLabel: "Very shallow",
    highLabel: "Very deep",
  },
  {
    id: "overallSatisfaction",
    icon: Star,
    question: "Overall, how satisfied are you with this meditation session?",
    lowLabel: "Very dissatisfied",
    highLabel: "Extremely satisfied",
  },
]

export const WEIGHTING_PROFILES: Record<string, { wa: number; we: number; ws: number; wd: number }> = {
  focused: { wa: 0.4, we: 0.15, ws: 0.2, wd: 0.25 },
  mantra: { wa: 0.4, we: 0.15, ws: 0.2, wd: 0.25 },
  mindfulness: { wa: 0.25, we: 0.2, ws: 0.35, wd: 0.2 },
  "loving-kindness": { wa: 0.15, we: 0.45, ws: 0.15, wd: 0.25 },
  "body-scan": { wa: 0.15, we: 0.15, ws: 0.5, wd: 0.2 },
  spiritual: { wa: 0.2, we: 0.2, ws: 0.2, wd: 0.4 },
}

export function calculateQualityScore(responses: ReportResponses, meditationType: string) {
  const a = (responses.focus + responses.mindWandering + responses.attentionEase) / 3
  const e = (responses.calmness + responses.emotionalBalance + responses.mentalRefreshment) / 3
  const s = (responses.presence + responses.bodyRelaxation) / 3
  const d = (responses.meditationDepth + responses.overallSatisfaction) / 2

  const weights = WEIGHTING_PROFILES[meditationType] || WEIGHTING_PROFILES.mindfulness
  
  const score = (weights.wa * a) + (weights.we * e) + (weights.ws * s) + (weights.wd * d)
  return parseFloat(score.toFixed(2))
}

export function SelfReport({ onSubmit, isSubmitting, meditationType }: SelfReportProps) {
  const [responses, setResponses] = useState<ReportResponses>({
    calmness: 5,
    focus: 5,
    mindWandering: 5,
    emotionalBalance: 5,
    presence: 5,
    mentalRefreshment: 5,
    attentionEase: 5,
    bodyRelaxation: 5,
    meditationDepth: 5,
    overallSatisfaction: 5,
  })

  const handleRatingChange = (questionId: keyof ReportResponses, value: number) => {
    setResponses((prev) => ({
      ...prev,
      [questionId]: value,
    }))
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const qualityScore = calculateQualityScore(responses, meditationType)
    onSubmit(responses, qualityScore)
  }

  const getScoreColor = (score: number) => {
    if (score <= 3) return "bg-red-500/80"
    if (score <= 5) return "bg-amber-500/80"
    if (score <= 7) return "bg-emerald-500/80"
    return "bg-primary"
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-start px-4 py-8">
      {/* Header */}
      <div className="mb-8 text-center">
        <div className="mb-4 flex items-center justify-center gap-2">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/20">
            <CheckCircle2 className="h-6 w-6 text-primary" />
          </div>
        </div>
        <h1 className="font-[family-name:var(--font-playfair)] text-3xl font-semibold tracking-tight text-foreground md:text-4xl">
          Session Reflection
        </h1>
        <p className="mt-2 max-w-md text-muted-foreground">
          Take a moment to reflect on your meditation experience. Your responses help track your progress.
        </p>
      </div>

      {/* Report Form */}
      <form onSubmit={handleSubmit} className="w-full max-w-2xl">
        <Card className="border-border/50 bg-card/80 backdrop-blur-sm">
          <CardContent className="p-6 md:p-8">
            <div className="space-y-8">
              {QUESTIONS.map((q, index) => {
                const Icon = q.icon
                const currentValue = responses[q.id]
                
                return (
                  <div key={q.id} className="space-y-4">
                    {/* Question Header */}
                    <div className="flex items-start gap-3">
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary/10">
                        <Icon className="h-4 w-4 text-primary" />
                      </div>
                      <div className="flex-1">
                        <Label className="text-base font-medium text-foreground">
                          <span className="mr-2 text-muted-foreground">{index + 1}.</span>
                          {q.question}
                        </Label>
                      </div>
                    </div>

                    {/* Rating Scale */}
                    <div className="pl-11">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs text-muted-foreground">{q.lowLabel}</span>
                        <span className="text-xs text-muted-foreground">{q.highLabel}</span>
                      </div>
                      
                      {/* Rating Buttons */}
                      <div className="flex gap-1 sm:gap-2">
                        {Array.from({ length: 10 }, (_, i) => i + 1).map((num) => (
                          <button
                            key={num}
                            type="button"
                            onClick={() => handleRatingChange(q.id, num)}
                            className={`
                              relative flex h-10 w-full items-center justify-center rounded-lg text-sm font-medium transition-all
                              ${currentValue === num
                                ? `${getScoreColor(num)} text-white shadow-md scale-105`
                                : "bg-secondary/50 text-muted-foreground hover:bg-secondary hover:text-foreground"
                              }
                            `}
                          >
                            {num}
                          </button>
                        ))}
                      </div>

                      {/* Current Selection Indicator */}
                      <div className="mt-2 flex items-center justify-center">
                        <span className={`text-sm font-medium ${getScoreColor(currentValue).replace('bg-', 'text-').replace('/80', '')}`}>
                          {currentValue}/10
                        </span>
                      </div>
                    </div>

                    {/* Divider */}
                    {index < QUESTIONS.length - 1 && (
                      <div className="border-t border-border/30 pt-4" />
                    )}
                  </div>
                )
              })}
            </div>

            {/* Submit Button */}
            <div className="mt-10 flex justify-center">
              <Button
                type="submit"
                size="lg"
                disabled={isSubmitting}
                className="h-14 min-w-[200px] text-base"
              >
                {isSubmitting ? (
                  <span className="flex items-center gap-2">
                    <span className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                    Submitting...
                  </span>
                ) : (
                  <span className="flex items-center gap-2">
                    Submit Report
                    <ChevronRight className="h-5 w-5" />
                  </span>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Progress Summary */}
        <div className="mt-6 rounded-xl border border-border/50 bg-card/60 p-4 backdrop-blur-sm">
          <h3 className="mb-3 text-sm font-medium text-foreground">Quick Summary</h3>
          <div className="grid grid-cols-5 gap-2 sm:grid-cols-10">
            {QUESTIONS.map((q) => {
              const Icon = q.icon
              const value = responses[q.id]
              return (
                <div
                  key={q.id}
                  className="flex flex-col items-center gap-1 rounded-lg bg-secondary/30 p-2"
                  title={q.question}
                >
                  <Icon className="h-4 w-4 text-muted-foreground" />
                  <span className={`text-xs font-semibold ${getScoreColor(value).replace('bg-', 'text-').replace('/80', '')}`}>
                    {value}
                  </span>
                </div>
              )
            })}
          </div>
          <div className="mt-3 flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Average Score</span>
            <span className="font-semibold text-foreground">
              {(Object.values(responses).reduce((a, b) => a + b, 0) / 10).toFixed(1)}/10
            </span>
          </div>
        </div>
      </form>
    </div>
  )
}
