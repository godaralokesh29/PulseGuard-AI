'use client'

import { useEffect, useMemo, useRef, useState } from 'react'
import { ArrowRight, CircleDot, Lightning, ServerCog, ShieldCheck, Slack, Sparkles } from 'lucide-react'
import { Area, AreaChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardAction, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

type EventMessage = {
  type: string
  tenant_id?: string
  service_name?: string
  error_type?: string
  spike_percentage?: number
  metric_name?: string
  data?: any
  message?: string
}

type WsStats = {
  active_connections: number
  client_ids: string[]
  slack_enabled: boolean
  timestamp: string
}

type DecisionSummary = {
  id: string
  matched_incident: string
  recommended_action: string
  confidence_score: number
  latency_ms: number
  generated_at: string
}

const sampleAnomaly = {
  tenant_id: 'payment_service',
  service_name: 'checkout',
  error_type: 'database_timeout',
  metric_name: 'db_connection_pool',
  baseline_value: 60,
  current_value: 330,
  spike_percentage: 450,
  window_minutes: 5,
}

const sampleAnalyze = {
  error_type: 'database_timeout',
  metric_name: 'db_query_latency_ms',
  spike_percentage: 450,
  tenant_id: 'payment_service',
  service_name: 'checkout',
  window_minutes: 5,
  top_k: 5,
}

export default function DashboardPage() {
  const [connected, setConnected] = useState(false)
  const [stats, setStats] = useState<WsStats>({
    active_connections: 0,
    client_ids: [],
    slack_enabled: false,
    timestamp: '',
  })
  const [events, setEvents] = useState<EventMessage[]>([])
  const [decisions, setDecisions] = useState<DecisionSummary[]>([])
  const [error, setError] = useState<string | null>(null)
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    setConnected(true)
    addEvent({ type: 'connected', message: 'Connected to incident stream (Mocked)' })

    return () => {
      setConnected(false)
    }
  }, [])

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const json: WsStats = {
          active_connections: Math.floor(Math.random() * 10) + 1,
          client_ids: ['client-1'],
          slack_enabled: true,
          timestamp: new Date().toISOString()
        }
        setStats(json)
      } catch (err) {
        console.error(err)
      }
    }

    fetchStats()
    const interval = window.setInterval(fetchStats, 10000)
    return () => window.clearInterval(interval)
  }, [])

  const addEvent = (event: EventMessage) => {
    setEvents((current) => [event, ...current].slice(0, 20))
  }

  const confidenceSeries = useMemo(
    () =>
      decisions.map((decision, index) => ({
        name: `#${index + 1}`,
        confidence: Math.round(decision.confidence_score * 100),
        latency: decision.latency_ms,
      })),
    [decisions],
  )

  const handleSendSampleAnomaly = async () => {
    try {
      const result = { status: 'success', message: 'Mocked anomaly processed' }
      addEvent({ type: 'anomaly', message: 'Sample anomaly reported (Mocked)', data: result })
    } catch (err: any) {
      setError(err.message || 'Sample anomaly failed')
    }
  }

  const handleAnalyzeSample = async () => {
    try {
      const result = {
        id: 'mock-' + Date.now(),
        matched_incident: 'Database Timeout Cascading Failure (Mocked)',
        recommended_action: 'Scale up database connections and check slow queries on checkout service.',
        confidence_score: 0.96,
        latency_ms: Math.floor(Math.random() * 100) + 50,
        generated_at: new Date().toISOString()
      }
      const decision: DecisionSummary = {
        id: result.id,
        matched_incident: result.matched_incident,
        recommended_action: result.recommended_action,
        confidence_score: result.confidence_score,
        latency_ms: result.latency_ms,
        generated_at: result.generated_at,
      }
      setDecisions((current) => [decision, ...current].slice(0, 10))
      addEvent({ type: 'decision', message: 'Sample decision generated', data: decision })
    } catch (err: any) {
      setError(err.message || 'Analyze request failed')
    }
  }

  return (
    <main className="min-h-screen bg-background px-6 py-8 text-foreground">
      <div className="mx-auto flex max-w-7xl flex-col gap-8">
        <section className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
          <article className="space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <p className="mb-2 text-sm uppercase tracking-[0.24em] text-muted-foreground">PulseGuard AI</p>
                <h1 className="text-4xl font-semibold tracking-tight">Active Incident Response Command Center</h1>
                <p className="max-w-2xl text-sm leading-6 text-muted-foreground">
                  Monitor live telemetry anomalies, AI-generated root cause analyses, and streaming WebSocket alerts. Use the simulation controls to trigger a demo anomaly pipeline.
                </p>
              </div>
              <div className="flex flex-wrap items-center gap-3">
                <Badge variant={stats.slack_enabled ? 'default' : 'outline'}>
                  {stats.slack_enabled ? 'Slack enabled' : 'Slack disabled'}
                </Badge>
                <Badge variant={connected ? 'default' : 'outline'}>
                  {connected ? 'Live connected' : 'Disconnected'}
                </Badge>
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              <Card>
                <CardHeader>
                  <CardTitle>Connected Clients</CardTitle>
                  <CardDescription className="text-foreground/70">Active WebSocket clients</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="text-5xl font-semibold">{stats.active_connections}</div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Live Events</CardTitle>
                  <CardDescription className="text-foreground/70">Recent incident feed</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="text-5xl font-semibold">{events.length}</div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Latest Decision</CardTitle>
                  <CardDescription className="text-foreground/70">From RAG AI engine</CardDescription>
                </CardHeader>
                <CardContent>
                  {decisions[0] ? (
                    <div className="space-y-2">
                      <p className="text-lg font-semibold">{decisions[0].matched_incident}</p>
                      <p className="text-sm text-muted-foreground">{decisions[0].recommended_action}</p>
                      <p className="text-sm text-muted-foreground">Confidence {Math.round(decisions[0].confidence_score * 100)}%</p>
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">No decision generated yet.</p>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Health Check</CardTitle>
                  <CardDescription className="text-foreground/70">Backend and WebSocket status</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <p className="text-sm">WebSocket: {connected ? 'Connected' : 'Disconnected'}</p>
                    <p className="text-sm">Last updated: {stats.timestamp || 'Pending'}</p>
                    {error ? <p className="text-sm text-destructive">{error}</p> : null}
                  </div>
                </CardContent>
              </Card>
            </div>

            <section className="grid gap-6 xl:grid-cols-[0.7fr_1.3fr]">
              <Card>
                <CardHeader>
                  <div>
                    <CardTitle>Live confidence trend</CardTitle>
                    <CardDescription className="text-foreground/70">
                      Confidence percentage and response latency from recent decisions.
                    </CardDescription>
                  </div>
                  <CardAction>
                    <Badge variant="secondary">Real-time</Badge>
                  </CardAction>
                </CardHeader>
                <CardContent>
                  {confidenceSeries.length > 0 ? (
                    <ResponsiveContainer width="100%" height={280}>
                      <AreaChart data={confidenceSeries} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                        <defs>
                          <linearGradient id="confidenceGradient" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#4f46e5" stopOpacity={0.8} />
                            <stop offset="95%" stopColor="#4f46e5" stopOpacity={0.05} />
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.2)" />
                        <XAxis dataKey="name" stroke="rgba(148,163,184,0.8)" />
                        <YAxis stroke="rgba(148,163,184,0.8)" domain={[0, 100]} />
                        <Tooltip />
                        <Area type="monotone" dataKey="confidence" stroke="#4f46e5" fill="url(#confidenceGradient)" />
                      </AreaChart>
                    </ResponsiveContainer>
                  ) : (
                    <p className="text-sm text-muted-foreground">Generate a decision to populate the chart.</p>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Simulation Controls</CardTitle>
                  <CardDescription className="text-foreground/70">Trigger a simulated anomaly or run a manual AI diagnosis.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-3 rounded-xl border border-border bg-muted p-4">
                    <div className="flex items-center justify-between gap-4">
                      <div>
                        <p className="text-sm font-medium">Test Incident</p>
                        <p className="text-xs text-muted-foreground">Database timeout cascading failure</p>
                      </div>
                      <Badge variant="outline">Simulation</Badge>
                    </div>
                    <div className="grid gap-2 text-sm text-muted-foreground">
                      <p>Tenant: payment_service</p>
                      <p>Service: checkout</p>
                      <p>Spike: 450%</p>
                    </div>
                  </div>

                  <div className="flex flex-col gap-3 sm:flex-row">
                    <Button onClick={handleSendSampleAnomaly} className="w-full" variant="default">
                      Simulate Flink Anomaly
                    </Button>
                    <Button onClick={handleAnalyzeSample} className="w-full" variant="secondary">
                      Run Manual AI Diagnosis
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </section>
          </article>

          <aside className="space-y-6">
            <Card>
              <CardHeader>
                <div>
                  <CardTitle>Live incident feed</CardTitle>
                  <CardDescription className="text-foreground/70">
                    Latest decisions and anomaly events from the WebSocket stream.
                  </CardDescription>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {events.length === 0 ? (
                    <p className="text-sm text-muted-foreground">Waiting for live events...</p>
                  ) : (
                    events.map((event, index) => (
                      <div key={`${event.type}-${index}`} className="rounded-lg border border-border bg-background p-3">
                        <div className="flex items-center justify-between gap-2">
                          <span className="text-sm font-semibold capitalize">{event.type}</span>
                          <Badge variant={event.type === 'decision' ? 'default' : event.type === 'anomaly' ? 'destructive' : 'outline'}>
                            {event.type}
                          </Badge>
                        </div>
                        <p className="mt-2 text-sm text-muted-foreground">{event.message || JSON.stringify(event.data || {})}</p>
                      </div>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <div>
                  <CardTitle>Recent decisions</CardTitle>
                  <CardDescription className="text-foreground/70">
                    Most recent AI recommendations generated by the system.
                  </CardDescription>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {decisions.length === 0 ? (
                    <p className="text-sm text-muted-foreground">No decisions yet. Run a sample analyze request.</p>
                  ) : (
                    decisions.map((decision) => (
                      <div key={decision.id} className="rounded-lg border border-border p-4">
                        <div className="flex items-center justify-between gap-2">
                          <span className="text-sm font-semibold">{decision.matched_incident}</span>
                          <span className="text-xs text-muted-foreground">{decision.generated_at?.slice(0, 19).replace('T', ' ')}</span>
                        </div>
                        <p className="mt-2 text-sm text-muted-foreground">{decision.recommended_action}</p>
                        <div className="mt-3 flex items-center gap-2 text-xs text-muted-foreground">
                          <span>Confidence: {Math.round(decision.confidence_score * 100)}%</span>
                          <span>Latency: {decision.latency_ms}ms</span>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>
          </aside>
        </section>
      </div>
    </main>
  )
}
