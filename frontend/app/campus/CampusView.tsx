'use client';

import { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import Image from 'next/image';
import styles from './campus.module.css';
import {
  ROOMS,
  AGENTS,
  HOTSPOTS,
  loadAgentNameOverrides,
  saveAgentNameOverride,
  getAgentDisplayName,
  type RoomId,
  type AgentId,
  type AgentConfig,
} from './campus-config';
import {
  fetchAgent,
  fetchMissionControl,
  type Agent,
  type AgentDetail,
  type AgentRun,
  type CronEntry,
  type MissionControlResponse,
} from '@/lib/api';

const POLL_INTERVAL_MS = 120_000; // 2 minutes

type View = 'campus' | 'room' | 'functional';

interface CampusViewProps {
  initialAgents: Agent[];
  initialCron: CronEntry[];
  backendError: string | null;
}

// ── Helpers to derive UI values from backend data ──────────────────────────

function computeCases24h(detail: AgentDetail | null | undefined): number {
  if (!detail) return 0;
  const cutoff = Date.now() - 24 * 60 * 60 * 1000;
  return detail.recent_runs.filter(
    (r) => r.started_at && new Date(r.started_at).getTime() >= cutoff,
  ).length;
}

function computeCasesTouched(run: AgentRun): number {
  if (!run.database_records_created) return 0;
  return Object.values(run.database_records_created).reduce<number>(
    (sum, v) => sum + (typeof v === 'number' ? v : 0),
    0,
  );
}

function findNextRunForAgent(
  agentId: AgentId,
  cron: CronEntry[],
): CronEntry | null {
  // Heuristic match: parts of the agent_name appear in the cron command/source.
  const parts = agentId.split('_').filter((p) => p.length > 3);
  const match = cron.find((entry) => {
    const haystack = `${entry.command} ${entry.source}`.toLowerCase();
    return parts.some((p) => haystack.includes(p));
  });
  return match || null;
}

function formatRelativeFuture(iso: string): string {
  const d = new Date(iso);
  const diff = (d.getTime() - Date.now()) / 1000;
  if (diff < 60) return 'in under a minute';
  if (diff < 3600) return `in ${Math.floor(diff / 60)} min`;
  if (diff < 86400) return `in ${Math.floor(diff / 3600)} h`;
  return `in ${Math.floor(diff / 86400)} d`;
}

function formatTimestamp(iso: string | null | undefined): string {
  if (!iso) return '—';
  const d = new Date(iso);
  const diff = (Date.now() - d.getTime()) / 1000;
  if (diff < 60) return 'just now';
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

function deriveMessages(
  detail: AgentDetail | null | undefined,
): { type: 'info' | 'warning' | 'action'; text: string }[] {
  if (!detail) return [];
  const msgs: { type: 'info' | 'warning' | 'action'; text: string }[] = [];
  for (const w of detail.warnings || []) {
    msgs.push({ type: 'warning', text: w });
  }
  if (detail.recommended_next_action) {
    msgs.push({ type: 'action', text: detail.recommended_next_action });
  }
  if (detail.last_error) {
    msgs.push({ type: 'warning', text: `Last error: ${detail.last_error}` });
  }
  return msgs;
}

// ── Governance agent insights (fontana, weber, quality_sentinel, historian)
// These agents have no backend agent_name in the registry. Instead of leaving
// their panel empty, we derive useful aggregate information from the
// mission-control endpoint that summarizes ALL agents in the system.

interface GovernanceInsights {
  messages: { type: 'info' | 'warning' | 'action'; text: string }[];
  syntheticRuns: Array<{
    id: string;
    started_at: string | null;
    status: string;
    output_summary: string;
    task_name: string;
    casesTouched: number;
  }>;
  noticeText: string | null;
}

function deriveGovernanceInsights(
  agentId: AgentId,
  missionData: MissionControlResponse | null,
): GovernanceInsights {
  const empty: GovernanceInsights = { messages: [], syntheticRuns: [], noticeText: null };

  if (agentId === 'fontana') {
    if (!missionData) {
      return {
        ...empty,
        noticeText: 'CTO governance — mission-control data not yet loaded.',
      };
    }
    const total = missionData.agents.length;
    const active = missionData.agents.filter((a) => a.current_status === 'active').length;
    const withErrors = missionData.agents.filter((a) => a.failed_runs > 0).length;
    const totalRuns = missionData.agents.reduce((s, a) => s + a.total_runs, 0);
    const messages: GovernanceInsights['messages'] = [];
    if (withErrors > 0) {
      messages.push({
        type: 'warning',
        text: `${withErrors} agent${withErrors === 1 ? '' : 's'} have failed runs. Review root cause and propose an ADR if recurring.`,
      });
    }
    messages.push({
      type: 'info',
      text: `System overview: ${active}/${total} agents active · ${totalRuns} total runs · $${missionData.total_cost_usd.toFixed(4)} AI cost.`,
    });
    const syntheticRuns = missionData.agents
      .filter((a) => a.last_run)
      .sort((a, b) => (b.last_run || '').localeCompare(a.last_run || ''))
      .slice(0, 5)
      .map((a) => ({
        id: a.agent_name,
        started_at: a.last_run,
        status: a.failed_runs > 0 ? 'failed' : 'completed',
        output_summary: `${a.display_name} · ${a.total_runs} runs · ${a.failed_runs} failed`,
        task_name: a.agent_name,
        casesTouched: a.total_runs,
      }));
    return {
      messages,
      syntheticRuns,
      noticeText: 'CTO governance · aggregated from mission-control endpoint.',
    };
  }

  if (agentId === 'weber') {
    if (!missionData) {
      return {
        ...empty,
        noticeText: 'COO governance — mission-control data not yet loaded.',
      };
    }
    const messages: GovernanceInsights['messages'] = [];
    for (const a of missionData.agents) {
      if (a.recommended_next_action) {
        messages.push({
          type: 'action',
          text: `${a.display_name} → ${a.recommended_next_action}`,
        });
      }
      for (const w of a.warnings || []) {
        messages.push({ type: 'warning', text: `${a.display_name}: ${w}` });
      }
    }
    return {
      messages: messages.slice(0, 8),
      syntheticRuns: [],
      noticeText: 'COO governance · next manual actions aggregated from every agent.',
    };
  }

  if (agentId === 'quality_sentinel') {
    return {
      messages: [
        {
          type: 'info',
          text: 'Quality Sentinel is not yet wired into the runtime. Manual review remains mandatory for all promotions and publications. Implementation planned for a future sprint.',
        },
      ],
      syntheticRuns: [],
      noticeText: 'Awaiting first sprint implementation.',
    };
  }

  if (agentId === 'historian') {
    return {
      messages: [
        {
          type: 'info',
          text: 'Historical Archive is an exploration room. Pattern analogue matching happens on-demand from research cases via the "Historical analogues" panel.',
        },
      ],
      syntheticRuns: [],
      noticeText: 'On-demand only · no scheduled runs.',
    };
  }

  return empty;
}

// ── Main Component ─────────────────────────────────────────────────────────

export function CampusView({
  initialAgents: _initialAgents,
  initialCron,
  backendError,
}: CampusViewProps) {
  const [view, setView] = useState<View>('campus');
  const [roomId, setRoomId] = useState<RoomId | null>(null);
  const [agentId, setAgentId] = useState<AgentId | null>(null);
  const [agentDetails, setAgentDetails] = useState<
    Partial<Record<AgentId, AgentDetail | null>>
  >({});
  const [nameOverrides, setNameOverrides] = useState<
    Partial<Record<AgentId, string>>
  >({});
  const [isZooming, setIsZooming] = useState(false);
  const [stageHovering, setStageHovering] = useState(false);
  const [hoveredHotspotId, setHoveredHotspotId] = useState<RoomId | null>(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });
  const [flashMessage, setFlashMessage] = useState<string | null>(null);
  const [debugMode, setDebugMode] = useState(false);

  // Operations Center overlay state
  const [opsOpen, setOpsOpen] = useState(false);
  const [missionData, setMissionData] = useState<MissionControlResponse | null>(null);
  const [missionLoading, setMissionLoading] = useState(false);
  const [missionError, setMissionError] = useState<string | null>(null);

  // Last-updated tracking for the agent panel
  const [agentDetailUpdatedAt, setAgentDetailUpdatedAt] = useState<
    Partial<Record<AgentId, number>>
  >({});

  const stageRef = useRef<HTMLDivElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const flashTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pollTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Load persistent name overrides on mount
  useEffect(() => {
    setNameOverrides(loadAgentNameOverrides());
  }, []);

  // Always load mission-control once on mount — governance agents (fontana,
  // weber) derive their panel content from this aggregate even before the
  // Operations Center overlay is opened.
  useEffect(() => {
    let cancelled = false;
    fetchMissionControl()
      .then((data) => {
        if (!cancelled) setMissionData(data);
      })
      .catch(() => {
        // Silent: governance panels will show "data not loaded" notice.
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // Fetch agent detail when an agent gets selected (cached after first load).
  // Only agents with a backendAgentName are fetched; conceptual agents
  // (governance / exploration roles) show derived info from mission-control.
  useEffect(() => {
    if (!agentId) return;
    if (agentId in agentDetails) return;
    const agent = AGENTS[agentId];
    if (!agent.backendAgentName) {
      // Conceptual-only agent — mark as "no backend" and skip fetch.
      setAgentDetails((prev) => ({ ...prev, [agentId]: null }));
      return;
    }
    let cancelled = false;
    fetchAgent(agent.backendAgentName)
      .then((detail) => {
        if (!cancelled) {
          setAgentDetails((prev) => ({ ...prev, [agentId]: detail }));
          setAgentDetailUpdatedAt((prev) => ({ ...prev, [agentId]: Date.now() }));
        }
      })
      .catch(() => {
        if (!cancelled) {
          setAgentDetails((prev) => ({ ...prev, [agentId]: null }));
        }
      });
    return () => {
      cancelled = true;
    };
  }, [agentId, agentDetails]);

  // Poll the open agent every 2 min (only if it has a backend mapping)
  useEffect(() => {
    if (!agentId) return;
    const agent = AGENTS[agentId];
    if (!agent.backendAgentName) return;
    if (pollTimerRef.current) clearInterval(pollTimerRef.current);
    const backendName = agent.backendAgentName;
    pollTimerRef.current = setInterval(() => {
      fetchAgent(backendName)
        .then((detail) => {
          setAgentDetails((prev) => ({ ...prev, [agentId]: detail }));
          setAgentDetailUpdatedAt((prev) => ({ ...prev, [agentId]: Date.now() }));
        })
        .catch(() => {
          // Silent: keep showing whatever was last successful.
        });
    }, POLL_INTERVAL_MS);
    return () => {
      if (pollTimerRef.current) {
        clearInterval(pollTimerRef.current);
        pollTimerRef.current = null;
      }
    };
  }, [agentId]);

  // Fetch mission control data when the overlay opens
  useEffect(() => {
    if (!opsOpen) return;
    let cancelled = false;
    setMissionLoading(true);
    setMissionError(null);
    fetchMissionControl()
      .then((data) => {
        if (!cancelled) {
          setMissionData(data);
          setMissionLoading(false);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setMissionError(
            err instanceof Error ? err.message : 'Mission control unreachable',
          );
          setMissionLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [opsOpen]);

  // Esc key returns to campus or closes the panel/overlay
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== 'Escape') return;
      if (opsOpen) {
        setOpsOpen(false);
      } else if (agentId) {
        setAgentId(null);
      } else if (view === 'room') {
        backToCampus();
      } else if (view === 'functional') {
        setView('room');
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [agentId, view, opsOpen]);

  const flash = useCallback((msg: string) => {
    if (flashTimeoutRef.current) clearTimeout(flashTimeoutRef.current);
    setFlashMessage(msg);
    flashTimeoutRef.current = setTimeout(() => setFlashMessage(null), 2700);
  }, []);

  const enterRoom = useCallback(
    (rid: RoomId, originX = 50, originY = 50) => {
      const room = ROOMS[rid];
      if (room.isHub) {
        // Operations Center opens the mission-control overlay
        setOpsOpen(true);
        return;
      }
      if (room.noLink) {
        flash(`${room.displayName} · exploration room, coming soon`);
        return;
      }
      if (stageRef.current) {
        stageRef.current.style.transformOrigin = `${originX}% ${originY}%`;
      }
      setIsZooming(true);
      setHoveredHotspotId(null);
      setRoomId(rid);
      setTimeout(() => {
        setView('room');
        setIsZooming(false);
        if (stageRef.current) stageRef.current.style.transformOrigin = '';
      }, 420);
    },
    [flash],
  );

  const backToCampus = useCallback(() => {
    setView('campus');
    setRoomId(null);
    setAgentId(null);
  }, []);

  const handleHotspotHover = useCallback(
    (rid: RoomId, e: React.MouseEvent) => {
      setHoveredHotspotId(rid);
      setStageHovering(true);
      updateTooltipPos(e);
    },
    [],
  );

  const handleHotspotLeave = useCallback(() => {
    setHoveredHotspotId(null);
    setStageHovering(false);
  }, []);

  const updateTooltipPos = useCallback(
    (e: React.MouseEvent) => {
      if (!stageRef.current || !tooltipRef.current) return;
      const rect = stageRef.current.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      const tw = tooltipRef.current.offsetWidth;
      const th = tooltipRef.current.offsetHeight;
      let tx = x + 18;
      let ty = y + 18;
      if (tx + tw > rect.width - 12) tx = x - tw - 18;
      if (ty + th > rect.height - 12) ty = y - th - 18;
      setTooltipPos({ x: tx, y: ty });
    },
    [],
  );

  const handleHotspotClick = useCallback(
    (rid: RoomId, e: React.MouseEvent<SVGPolygonElement>) => {
      if (!stageRef.current) {
        enterRoom(rid);
        return;
      }
      const rect = stageRef.current.getBoundingClientRect();
      const ox = ((e.clientX - rect.left) / rect.width) * 100;
      const oy = ((e.clientY - rect.top) / rect.height) * 100;
      enterRoom(rid, ox, oy);
    },
    [enterRoom],
  );

  const handleNameChange = useCallback(
    (aid: AgentId, newName: string) => {
      const trimmed = newName.trim() || AGENTS[aid].defaultName;
      setNameOverrides((prev) => ({ ...prev, [aid]: trimmed }));
      saveAgentNameOverride(aid, trimmed);
    },
    [],
  );

  const currentRoom = roomId ? ROOMS[roomId] : null;
  const currentAgent = agentId ? AGENTS[agentId] : null;
  const currentDetail = agentId ? agentDetails[agentId] : null;

  return (
    <div
      className={styles.campus}
      data-debug={debugMode ? 'true' : undefined}
    >
      <div className={styles.brand}>
        <span className={styles.brandDot} />
        SWISSEDGE
      </div>

      {view !== 'campus' && (
        <button className={styles.backBtn} onClick={backToCampus}>
          ← Back
        </button>
      )}

      <button
        className={styles.debugToggle}
        onClick={() => setDebugMode((d) => !d)}
        title="Toggle hotspot debug overlay"
      >
        {debugMode ? 'Hide debug' : 'Debug hotspots'}
      </button>

      {backendError && (
        <div className={styles.backendError}>⚠ {backendError}</div>
      )}

      {/* ── Campus view ───────────────────────────────────── */}
      <section
        className={`${styles.view} ${view === 'campus' ? styles.isActive : ''}`}
      >
        <div
          ref={stageRef}
          className={`${styles.stage} ${isZooming ? styles.isZooming : ''} ${
            stageHovering ? styles.stageHover : ''
          }`}
          onMouseMove={hoveredHotspotId ? updateTooltipPos : undefined}
        >
          <Image
            src="/campus/campus.png"
            alt="SwissEdge Campus"
            fill
            priority
            className={styles.stageBg}
            sizes="(max-width: 1366px) 100vw, 1366px"
          />

          <svg
            className={styles.hotspotLayer}
            viewBox="0 0 100 100"
            preserveAspectRatio="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            {HOTSPOTS.map((h) => (
              <g key={h.roomId}>
                <polygon
                  className={styles.hotspot}
                  data-no-link={ROOMS[h.roomId].noLink ? 'true' : undefined}
                  points={h.points}
                  onMouseEnter={(e) => handleHotspotHover(h.roomId, e)}
                  onMouseLeave={handleHotspotLeave}
                  onClick={(e) => handleHotspotClick(h.roomId, e)}
                />
                <text
                  className={styles.hotspotLabel}
                  x={h.labelX}
                  y={h.labelY}
                >
                  {h.labelText}
                </text>
              </g>
            ))}
          </svg>

          <div
            ref={tooltipRef}
            className={`${styles.tooltip} ${
              hoveredHotspotId ? styles.isVisible : ''
            }`}
            style={{ left: tooltipPos.x, top: tooltipPos.y }}
            role="tooltip"
            aria-hidden={!hoveredHotspotId}
          >
            {hoveredHotspotId && (
              <>
                <div className={styles.tooltipName}>
                  {ROOMS[hoveredHotspotId].displayName}
                </div>
                <div className={styles.tooltipRole}>
                  {ROOMS[hoveredHotspotId].noLink
                    ? 'Exploration room · coming soon'
                    : ROOMS[hoveredHotspotId].subtitle}
                </div>
              </>
            )}
          </div>
        </div>
      </section>

      {/* ── Room view ────────────────────────────────────── */}
      <section
        className={`${styles.view} ${view === 'room' ? styles.isActive : ''}`}
      >
        {currentRoom && (
          <div className={styles.roomStage}>
            {currentRoom.image && (
              <Image
                src={currentRoom.image}
                alt={currentRoom.displayName}
                fill
                className={styles.roomBg}
                sizes="(max-width: 1366px) 100vw, 1366px"
              />
            )}

            <div className={styles.roomMeta}>
              <h1
                className={styles.roomName}
                onDoubleClick={() => setView('functional')}
                title="Double-click for the functional view"
              >
                {currentRoom.displayName}
              </h1>
              <div className={styles.roomSubtitle}>{currentRoom.subtitle}</div>
              <div className={styles.roomDescription}>
                {currentRoom.description}
              </div>
              {currentRoom.mainQuestion && (
                <div className={styles.roomQuestion}>
                  {currentRoom.mainQuestion}
                </div>
              )}
            </div>

            <div className={styles.agentsLayer}>
              {currentRoom.agentIds.map((aid) => {
                const agent = AGENTS[aid];
                const isSel = aid === agentId;
                return (
                  <button
                    key={aid}
                    className={`${styles.agentAvatar} ${
                      isSel ? styles.isSelected : ''
                    }`}
                    data-has-image="true"
                    style={{
                      left: `${agent.position.x}%`,
                      top: `${agent.position.y}%`,
                      backgroundImage: `url('/campus/agents/${aid}.png')`,
                    }}
                    onClick={() => setAgentId(aid)}
                    title={getAgentDisplayName(aid, nameOverrides)}
                    aria-label={getAgentDisplayName(aid, nameOverrides)}
                  >
                    <span className={styles.agentPulse} />
                  </button>
                );
              })}
            </div>

            {currentAgent && (
              <AgentPanel
                agent={currentAgent}
                detail={currentDetail}
                lastUpdatedTs={agentDetailUpdatedAt[agentId!] ?? null}
                displayName={getAgentDisplayName(agentId!, nameOverrides)}
                cron={initialCron}
                missionData={missionData}
                onClose={() => setAgentId(null)}
                onRename={(name) => handleNameChange(agentId!, name)}
              />
            )}
          </div>
        )}
      </section>

      {/* ── Functional view (Level 2) ──────────────────────── */}
      <section
        className={`${styles.view} ${
          view === 'functional' ? styles.isActive : ''
        }`}
      >
        <div className={styles.functionalView}>
          <div className={styles.functionalTitle}>
            {currentRoom?.displayName}
          </div>
          <div className={styles.functionalNote}>
            Functional view — coming soon. This will show the dense operational
            data for {currentRoom?.backend}: case queues, evidence tables,
            checklists, quality reviews, and logs.
          </div>
        </div>
      </section>

      {flashMessage && (
        <div className={styles.flash} key={flashMessage}>
          {flashMessage}
        </div>
      )}

      {opsOpen && (
        <OperationsOverlay
          data={missionData}
          loading={missionLoading}
          error={missionError}
          onClose={() => setOpsOpen(false)}
        />
      )}
    </div>
  );
}

// ── Operations Center Overlay (mission control aggregate) ─────────────────

interface OperationsOverlayProps {
  data: MissionControlResponse | null;
  loading: boolean;
  error: string | null;
  onClose: () => void;
}

function OperationsOverlay({
  data,
  loading,
  error,
  onClose,
}: OperationsOverlayProps) {
  const stats = useMemo(() => {
    if (!data) return null;
    const agents = data.agents;
    const total = agents.length;
    const active = agents.filter((a) => a.current_status === 'active').length;
    const withErrors = agents.filter((a) => a.failed_runs > 0).length;
    const totalRuns = agents.reduce((s, a) => s + a.total_runs, 0);
    return { total, active, withErrors, totalRuns };
  }, [data]);

  return (
    <div className={styles.opsBackdrop} onClick={onClose}>
      <div className={styles.opsCard} onClick={(e) => e.stopPropagation()}>
        <button
          className={styles.opsClose}
          onClick={onClose}
          aria-label="Close mission control"
        >
          ×
        </button>

        <div className={styles.opsHeader}>
          <div>
            <div className={styles.opsTitle}>Operations Center</div>
            <div className={styles.opsSubtitle}>
              Mission control · Live system overview
            </div>
          </div>
          {data && (
            <div className={styles.opsGeneratedAt}>
              Generated {new Date(data.generated_at).toLocaleTimeString()}
            </div>
          )}
        </div>

        {loading && (
          <div className={styles.opsEmpty}>Loading mission control…</div>
        )}

        {error && (
          <div className={styles.opsEmpty}>
            ⚠ {error}
            <br />
            Make sure the backend FastAPI is running.
          </div>
        )}

        {data && stats && (
          <>
            <div className={styles.opsStats}>
              <div className={styles.opsStat}>
                <div className={styles.opsStatValue}>{stats.total}</div>
                <div className={styles.opsStatLabel}>Registered agents</div>
              </div>
              <div className={styles.opsStat}>
                <div className={styles.opsStatValue}>{stats.active}</div>
                <div className={styles.opsStatLabel}>Active</div>
              </div>
              <div
                className={`${styles.opsStat} ${
                  stats.withErrors > 0 ? styles.opsStatAlert : ''
                }`}
              >
                <div className={styles.opsStatValue}>{stats.withErrors}</div>
                <div className={styles.opsStatLabel}>With failed runs</div>
              </div>
              <div className={styles.opsStat}>
                <div className={styles.opsStatValue}>{stats.totalRuns}</div>
                <div className={styles.opsStatLabel}>Total runs</div>
              </div>
            </div>

            <div>
              <div className={styles.opsSectionLabel}>All agents</div>
              {data.agents.length === 0 ? (
                <div className={styles.opsEmpty}>No agents registered.</div>
              ) : (
                <div className={styles.opsAgents}>
                  {data.agents.map((a) => (
                    <div key={a.agent_name} className={styles.opsAgentCard}>
                      <div className={styles.opsAgentName}>
                        <span
                          className={styles.opsStatusDot}
                          data-status={a.current_status}
                          title={a.current_status}
                        />
                        {a.display_name}
                      </div>
                      <div className={styles.opsAgentMeta}>
                        <span>
                          {a.total_runs} runs · {a.failed_runs} failed
                        </span>
                        <span>
                          {a.last_run
                            ? `Last: ${formatTimestamp(a.last_run)}`
                            : 'Never run'}
                        </span>
                      </div>
                      {a.last_error && (
                        <div className={styles.opsAgentError}>
                          {a.last_error.length > 80
                            ? a.last_error.slice(0, 80) + '…'
                            : a.last_error}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

// ── Agent Panel ───────────────────────────────────────────────────────────

interface AgentPanelProps {
  agent: AgentConfig;
  detail: AgentDetail | null | undefined;
  lastUpdatedTs: number | null;
  displayName: string;
  cron: CronEntry[];
  missionData: MissionControlResponse | null;
  onClose: () => void;
  onRename: (name: string) => void;
}

function AgentPanel({
  agent,
  detail,
  lastUpdatedTs,
  displayName,
  cron,
  missionData,
  onClose,
  onRename,
}: AgentPanelProps) {
  const nameRef = useRef<HTMLDivElement>(null);
  const [tickNow, setTickNow] = useState<number>(() => Date.now());

  // Sync the contentEditable when agentId or displayName changes
  useEffect(() => {
    if (nameRef.current && nameRef.current.textContent !== displayName) {
      nameRef.current.textContent = displayName;
    }
  }, [displayName, agent.id]);

  // Tick the "Xm ago" indicator every 30s without triggering a refetch
  useEffect(() => {
    const id = setInterval(() => setTickNow(Date.now()), 30_000);
    return () => clearInterval(id);
  }, []);

  const nextRunEntry = useMemo(
    () => findNextRunForAgent(agent.id, cron),
    [agent.id, cron],
  );

  const isConceptual = !agent.backendAgentName;
  const isLoading = !isConceptual && detail === undefined;
  const isError = !isConceptual && detail === null;
  const governance = isConceptual
    ? deriveGovernanceInsights(agent.id, missionData)
    : { messages: [], syntheticRuns: [], noticeText: null };
  const cases24h = computeCases24h(detail ?? null);
  const realLastRuns = (detail?.recent_runs ?? []).slice(0, 5);
  const lastRuns = isConceptual ? [] : realLastRuns;
  const realMessages = deriveMessages(detail ?? null);
  const messages = isConceptual ? governance.messages : realMessages;
  const lastUpdatedLabel =
    lastUpdatedTs == null
      ? null
      : (() => {
          const diff = Math.max(0, (tickNow - lastUpdatedTs) / 1000);
          if (diff < 60) return 'updated just now';
          if (diff < 3600) return `updated ${Math.floor(diff / 60)}m ago`;
          return `updated ${Math.floor(diff / 3600)}h ago`;
        })();

  return (
    <aside className={`${styles.agentPanel} ${styles.isVisible}`}>
      <button
        className={styles.panelClose}
        onClick={onClose}
        aria-label="Close panel"
      >
        ×
      </button>

      <div className={styles.agentHeader}>
        <div
          className={styles.agentAvatarLarge}
          data-has-image="true"
          style={{
            backgroundImage: `url('/campus/agents/${agent.id}.png')`,
            backgroundColor: 'rgba(126, 108, 176, 0.08)',
          }}
          aria-hidden="true"
        >
          {agent.initials}
        </div>
        <div className={styles.agentHeaderText}>
          <div
            ref={nameRef}
            className={styles.agentName}
            contentEditable
            suppressContentEditableWarning
            spellCheck={false}
            onBlur={(e) => onRename(e.currentTarget.textContent || '')}
          />
          <div className={styles.agentRole}>
            {agent.role}
            {lastUpdatedLabel && (
              <span className={styles.lastUpdated}> · {lastUpdatedLabel}</span>
            )}
          </div>
        </div>
      </div>

      {isError && (
        <div
          className={styles.agentSectionValue}
          style={{
            background: 'rgba(196, 82, 63, 0.08)',
            border: '1px solid rgba(196, 82, 63, 0.25)',
            borderRadius: 10,
            padding: '10px 12px',
            color: 'var(--ink)',
            fontSize: 12,
          }}
        >
          ⚠ Could not load live data. Backend may be offline. Showing the
          static profile from the config.
        </div>
      )}

      {isConceptual && governance.noticeText && (
        <div
          className={styles.agentSectionValue}
          style={{
            background: 'rgba(168, 213, 211, 0.14)',
            border: '1px solid rgba(168, 213, 211, 0.4)',
            borderRadius: 10,
            padding: '10px 12px',
            color: 'var(--ink)',
            fontSize: 12,
            fontStyle: 'italic',
          }}
        >
          ◇ {governance.noticeText}
        </div>
      )}

      <div className={styles.agentSection}>
        <div className={styles.agentSectionLabel}>Pipeline function</div>
        <div className={styles.agentPipeline}>
          <span
            className={styles.agentPipelineStep}
            data-empty={agent.pipeline.position == null ? 'true' : undefined}
          >
            {agent.pipeline.position ?? '—'}
          </span>
          <span className={styles.agentPipelineRoom}>
            {agent.pipeline.room}
          </span>
        </div>
        <div className={styles.agentSectionValue}>{agent.purpose}</div>
      </div>

      <div className={styles.agentSection}>
        <div className={styles.agentSectionLabel}>Skills</div>
        <ul className={styles.agentSkills}>
          {agent.skills.map((s) => (
            <li key={s}>{s}</li>
          ))}
        </ul>
      </div>

      <div className={styles.agentSection}>
        <div className={styles.agentSectionLabel}>Cases · last 24h</div>
        <div className={styles.agentCases}>
          <span className={styles.agentCasesValue}>
            {detail === undefined ? '…' : cases24h}
          </span>
          <span className={styles.agentCasesLabel}>
            {cases24h === 1 ? 'case touched' : 'cases touched'}
          </span>
        </div>
      </div>

      <div className={styles.agentSection}>
        <div className={styles.agentSectionLabel}>Next scheduled run</div>
        {nextRunEntry ? (
          <div className={styles.nextRun}>
            <span className={styles.nextRunWhen}>
              {formatRelativeFuture(nextRunEntry.scheduled_at)}
            </span>
            <span className={styles.nextRunTarget}>
              {nextRunEntry.schedule} · {nextRunEntry.command}
            </span>
          </div>
        ) : (
          <div className={styles.agentSectionValue} style={{ opacity: 0.6 }}>
            No scheduled run · on-demand only
          </div>
        )}
      </div>

      <div className={styles.agentSection}>
        <div className={styles.agentSectionLabel}>
          {isConceptual && governance.syntheticRuns.length > 0 ? 'System overview' : 'Last 5 runs'}
        </div>
        {isConceptual ? (
          governance.syntheticRuns.length === 0 ? (
            <div className={styles.agentSectionValue} style={{ opacity: 0.6 }}>
              No live runs · governance role
            </div>
          ) : (
            <ul className={styles.lastRuns}>
              {governance.syntheticRuns.map((r) => (
                <li key={r.id} className={styles.lastRunRow}>
                  <span
                    className={styles.lastRunDot}
                    data-status={r.status}
                    title={r.status}
                  />
                  <span className={styles.lastRunSummary}>{r.output_summary}</span>
                  <span className={styles.lastRunCases}>{r.casesTouched}</span>
                </li>
              ))}
            </ul>
          )
        ) : lastRuns.length === 0 ? (
          <div className={styles.agentSectionValue} style={{ opacity: 0.6 }}>
            {isLoading ? 'Loading…' : 'No runs yet'}
          </div>
        ) : (
          <ul className={styles.lastRuns}>
            {lastRuns.map((r) => (
              <li key={r.id} className={styles.lastRunRow}>
                <span
                  className={styles.lastRunDot}
                  data-status={r.status}
                  title={r.status}
                />
                <span className={styles.lastRunSummary}>
                  {r.output_summary || r.task_name || '—'}
                </span>
                <span className={styles.lastRunCases}>
                  {computeCasesTouched(r)}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className={styles.agentSection}>
        <div className={styles.agentSectionLabel}>Recent logs</div>
        {isConceptual ? (
          <div className={styles.agentSectionValue} style={{ opacity: 0.6, fontStyle: 'italic' }}>
            This agent does not produce its own run logs · see the messages below
          </div>
        ) : (detail?.recent_runs ?? []).length === 0 ? (
          <div className={styles.agentSectionValue} style={{ opacity: 0.6 }}>
            {isLoading ? 'Loading…' : 'No activity logged'}
          </div>
        ) : (
          <ul className={styles.agentLogs}>
            {(detail?.recent_runs ?? []).slice(0, 8).map((r) => (
              <li key={r.id} data-status={r.status}>
                <span className={styles.logTimestamp}>
                  {formatTimestamp(r.started_at)} · {r.status}
                </span>
                <span>
                  {r.output_summary ||
                    r.error_message ||
                    r.task_name ||
                    '—'}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className={styles.agentSection}>
        <div className={styles.agentSectionLabel}>Messages for you</div>
        {messages.length === 0 ? (
          <ul className={styles.agentMessages}>
            <li data-empty="true">◇ Nothing to flag</li>
          </ul>
        ) : (
          <ul className={styles.agentMessages}>
            {messages.map((m, i) => (
              <li key={i} data-type={m.type}>
                {m.text}
              </li>
            ))}
          </ul>
        )}
      </div>

      {agent.movieRef && (
        <div className={styles.agentMovie}>Inspired by {agent.movieRef}</div>
      )}
    </aside>
  );
}
