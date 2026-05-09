'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { fetchSources, toggleSourceActive, type InvestmentSource } from '@/lib/api';

interface CourseRef {
  playbook: string;
  primaryChapter: string;
  supportingChapters: string;
  minute: string;
  whyItMatters: string;
}

interface FutureSource {
  category: string;
  availability: 'automated' | 'manual' | 'unavailable';
  note: string;
  courseRefs: CourseRef[];
}

const PLACEHOLDER_COURSE_REFS: Record<string, CourseRef[]> = {
  'SEC EDGAR — Bankruptcy Chapter 11 (8-K Item 1.03)': [
    {
      playbook: 'Bankruptcy / Liquidation',
      primaryChapter: 'Ch. 10',
      supportingChapters: 'Ch. 2, 21',
      minute: 'Timestamp not available',
      whyItMatters: 'Chapter 11 8-K signals distressed situations. Ch. 10 covers detecting and evaluating bankruptcy and liquidation opportunities.',
    },
  ],
  'Reuters M&A News (placeholder)': [
    {
      playbook: 'Merger',
      primaryChapter: 'Ch. 7',
      supportingChapters: 'Ch. 9, 11, 20',
      minute: 'Timestamp not available',
      whyItMatters: 'News feeds act as an early-detection layer for merger announcements before EDGAR filings appear.',
    },
    {
      playbook: 'Merger Arbitrage',
      primaryChapter: 'Ch. 6',
      supportingChapters: 'Ch. 2, 8, 12',
      minute: 'Timestamp not available',
      whyItMatters: 'Real-time M&A news is a medium-reliability supplement to SEC filings for monitoring deal developments and competing bids.',
    },
  ],
  'Bloomberg Terminal API (placeholder)': [
    {
      playbook: 'Merger Arbitrage',
      primaryChapter: 'Ch. 6',
      supportingChapters: 'Ch. 8, 12, 13',
      minute: 'Timestamp not available',
      whyItMatters: 'Real-time stock prices and bond data are required to calculate deal spreads, IRR, and closing probability in arbitrage situations.',
    },
    {
      playbook: 'Spin-Off',
      primaryChapter: 'Ch. 11',
      supportingChapters: 'Ch. 3, 4',
      minute: 'Timestamp not available',
      whyItMatters: 'Bloomberg provides peer comparable multiples and real-time spinco trading prices needed for sum-of-parts valuation.',
    },
    {
      playbook: 'Bankruptcy / Liquidation',
      primaryChapter: 'Ch. 10',
      supportingChapters: 'Ch. 21',
      minute: 'Timestamp not available',
      whyItMatters: 'Credit rating feeds and bond price data are required for the distressed bond analysis path.',
    },
  ],
};

const FUTURE_SOURCES: FutureSource[] = [
  {
    category: 'Market Data — Stock Prices',
    availability: 'automated',
    note: 'Exchange APIs, brokerage platforms; required for spread/valuation analysis',
    courseRefs: [
      {
        playbook: 'Merger Arbitrage',
        primaryChapter: 'Ch. 6',
        supportingChapters: 'Ch. 8, 12',
        minute: 'Timestamp not available',
        whyItMatters: 'Current target price is the first data point in calculating the deal spread and annualised IRR.',
      },
    ],
  },
  {
    category: 'Market Data — Bond Prices (TRACE)',
    availability: 'automated',
    note: 'Public TRACE data; required for distressed bond situations',
    courseRefs: [
      {
        playbook: 'Bankruptcy / Liquidation',
        primaryChapter: 'Ch. 10',
        supportingChapters: 'Ch. 2, 21',
        minute: 'Timestamp not available',
        whyItMatters: 'Publicly available TRACE bond prices are essential for the distressed bond analysis path without requiring a Bloomberg subscription.',
      },
    ],
  },
  {
    category: 'Institutional Holdings (13F)',
    availability: 'automated',
    note: 'SEC EDGAR 13F filings; quarterly with 45-day lag; blocking risk analysis',
    courseRefs: [
      {
        playbook: 'Merger Arbitrage',
        primaryChapter: 'Ch. 6',
        supportingChapters: 'Ch. 2, 8',
        minute: 'Timestamp not available',
        whyItMatters: 'Large-holder 13F positions reveal potential blocking risk if a shareholder controls enough votes to oppose the deal.',
      },
      {
        playbook: 'Spin-Off',
        primaryChapter: 'Ch. 11',
        supportingChapters: 'Ch. 3, 4',
        minute: 'Timestamp not available',
        whyItMatters: 'Fund category classification from 13F data predicts forced selling of the spinco by index funds and mandate-constrained holders.',
      },
    ],
  },
  {
    category: 'Financial News & Press Releases',
    availability: 'manual',
    note: 'Google Alerts, company IR sites, Reuters/Bloomberg; medium reliability',
    courseRefs: [
      {
        playbook: 'Merger',
        primaryChapter: 'Ch. 7',
        supportingChapters: 'Ch. 9, 11, 20',
        minute: 'Timestamp not available',
        whyItMatters: 'News and IR alerts often surface merger rumors and strategic-alternatives disclosures before EDGAR filings, enabling faster detection.',
      },
      {
        playbook: 'Proxy Fight',
        primaryChapter: 'Ch. 19',
        supportingChapters: '—',
        minute: 'Timestamp not available',
        whyItMatters: 'Activist public letters and media coverage are primary inputs for proxy fight monitoring alongside SC 13D filings.',
      },
    ],
  },
  {
    category: 'Activist & Proxy Materials',
    availability: 'manual',
    note: 'SC 13D filings, dissident proxy letters, ISS/Glass Lewis reports',
    courseRefs: [
      {
        playbook: 'Proxy Fight',
        primaryChapter: 'Ch. 19',
        supportingChapters: '—',
        minute: 'Timestamp not available',
        whyItMatters: 'SC 13D filings and DFAN14A dissident proxies are the primary detection signals; ISS/Glass Lewis recommendations influence vote outcomes but are not on EDGAR.',
      },
    ],
  },
  {
    category: 'Credit Ratings',
    availability: 'manual',
    note: "Moody's, S&P, Fitch; subscription or 10-K disclosure; distressed bond path",
    courseRefs: [
      {
        playbook: 'Bankruptcy / Liquidation',
        primaryChapter: 'Ch. 10',
        supportingChapters: 'Ch. 21',
        minute: 'Timestamp not available',
        whyItMatters: 'Credit rating downgrades are a key entry signal for the distressed bond path; ratings may be disclosed in 10-K filings without a subscription.',
      },
    ],
  },
  {
    category: 'Peer Comparable Data',
    availability: 'manual',
    note: 'EBITDA multiples, deal premiums; FactSet/Bloomberg/CapIQ; spin-off valuation',
    courseRefs: [
      {
        playbook: 'Spin-Off',
        primaryChapter: 'Ch. 11',
        supportingChapters: 'Ch. 3, 4',
        minute: 'Timestamp not available',
        whyItMatters: 'Sum-of-parts valuation for a spin-off requires sector peer EBITDA multiples; these are not derivable from public filings alone.',
      },
      {
        playbook: 'Merger Arbitrage',
        primaryChapter: 'Ch. 6',
        supportingChapters: 'Ch. 12, 13',
        minute: 'Timestamp not available',
        whyItMatters: 'Sector M&A deal premiums provide a benchmark for assessing whether a proposed deal price is fair value.',
      },
    ],
  },
  {
    category: 'Broker Participation',
    availability: 'unavailable',
    note: 'Tender offer & rights offering broker confirmation; not disclosed in SEC filings',
    courseRefs: [
      {
        playbook: 'Tender Offer',
        primaryChapter: 'Ch. 8',
        supportingChapters: 'Ch. 9, 20',
        minute: 'Timestamp not available',
        whyItMatters: 'Broker participation and internal deadlines are not disclosed in SC TO-I filings; direct broker confirmation is required to execute a tender.',
      },
      {
        playbook: 'Rights Offering',
        primaryChapter: 'Ch. 18',
        supportingChapters: '—',
        minute: 'Timestamp not available',
        whyItMatters: 'Rights offering subscriptions depend on broker support for rights distribution; not all brokers support these transactions.',
      },
    ],
  },
];

const AVAILABILITY_STYLE: Record<FutureSource['availability'], { badge: string; label: string }> = {
  automated: { badge: 'status-badge status-badge--active', label: 'AUTOMATED' },
  manual: { badge: 'status-badge status-badge--manual', label: 'MANUAL' },
  unavailable: { badge: 'status-badge status-badge--readonly', label: 'UNAVAILABLE' },
};

function CourseRefPanel({ refs }: { refs: CourseRef[] }) {
  const capped = refs.slice(0, 3);
  return (
    <div className="course-ref-panel">
      <p className="course-ref-eyebrow">COURSE REFERENCE</p>
      {capped.map((r, i) => (
        <div key={i} className={i > 0 ? 'course-ref-item course-ref-item--divided' : 'course-ref-item'}>
          <div className="course-ref-grid">
            <span className="course-ref-key">Playbook</span>
            <span className="course-ref-val">{r.playbook}</span>
            <span className="course-ref-key">Chapter</span>
            <span className="course-ref-val">{r.primaryChapter}{r.supportingChapters && r.supportingChapters !== '—' ? ` (also: ${r.supportingChapters})` : ''}</span>
            <span className="course-ref-key">Minute</span>
            <span className="course-ref-val course-ref-val--muted">{r.minute}</span>
            <span className="course-ref-key">Why</span>
            <span className="course-ref-val course-ref-val--body">{r.whyItMatters}</span>
          </div>
        </div>
      ))}
    </div>
  );
}

function SourceTable({
  sources,
  togglingId,
  onToggle,
  formatDate,
}: {
  sources: InvestmentSource[];
  togglingId: string | null;
  onToggle: (s: InvestmentSource) => void;
  formatDate: (v: string | null) => string;
}) {
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  const toggle = (id: string) =>
    setExpanded(prev => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });

  return (
    <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
      <div style={{ overflowX: 'auto' }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Type</th>
              <th>Market</th>
              <th>Priority</th>
              <th>Freq (h)</th>
              <th>Last Checked</th>
              <th>Last Error</th>
              <th style={{ textAlign: 'center' }}>Status</th>
              <th style={{ textAlign: 'center' }}>Action</th>
            </tr>
          </thead>
          <tbody>
            {sources.map((source) => {
              const refs = PLACEHOLDER_COURSE_REFS[source.name];
              const isExpanded = expanded.has(source.id);
              return (
                <>
                  <tr key={source.id}>
                    <td>
                      <div style={{ fontWeight: 500, color: 'var(--text-primary)', fontSize: 13 }}>{source.name}</div>
                      {source.description && (
                        <div className="card-desc" style={{ marginTop: 2, maxWidth: 220, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={source.description}>
                          {source.description}
                        </div>
                      )}
                      {source.url && (
                        <a
                          href={source.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="card-desc"
                          style={{ marginTop: 2, maxWidth: 220, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', display: 'block', color: 'var(--text-muted)', textDecoration: 'none' }}
                          title={source.url}
                        >
                          {source.url}
                        </a>
                      )}
                      {refs && (
                        <button
                          onClick={() => toggle(source.id)}
                          className="course-ref-toggle"
                        >
                          {isExpanded ? '▾ COURSE REF' : '▸ COURSE REF'}
                        </button>
                      )}
                    </td>
                    <td>{source.source_type ?? '-'}</td>
                    <td>{source.market ?? '-'}</td>
                    <td>{source.priority}</td>
                    <td>{source.check_frequency_hours}</td>
                    <td style={{ color: 'var(--text-muted)' }}>{formatDate(source.last_checked)}</td>
                    <td style={{ maxWidth: 160 }}>
                      {source.last_error ? (
                        <span style={{ color: 'var(--status-preview-text)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', display: 'block' }} title={source.last_error}>
                          {source.last_error}
                        </span>
                      ) : (
                        <span style={{ color: 'var(--text-faint)' }}>—</span>
                      )}
                    </td>
                    <td style={{ textAlign: 'center' }}>
                      <span className={`status-badge ${source.active ? 'status-badge--active' : 'status-badge--readonly'}`}>
                        {source.active ? 'ACTIVE' : 'INACTIVE'}
                      </span>
                    </td>
                    <td style={{ textAlign: 'center' }}>
                      <button
                        onClick={() => onToggle(source)}
                        disabled={togglingId === source.id}
                        className={`btn btn--sm ${source.active ? 'btn--secondary' : 'btn--primary'}`}
                        style={{ opacity: togglingId === source.id ? 0.5 : 1 }}
                      >
                        {togglingId === source.id ? '...' : source.active ? 'Disable' : 'Enable'}
                      </button>
                    </td>
                  </tr>
                  {refs && isExpanded && (
                    <tr key={`${source.id}-ref`} style={{ background: 'var(--bg-subtle)' }}>
                      <td colSpan={9} style={{ paddingTop: 0 }}>
                        <CourseRefPanel refs={refs} />
                      </td>
                    </tr>
                  )}
                </>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default function SourcesPage() {
  const [sources, setSources] = useState<InvestmentSource[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [togglingId, setTogglingId] = useState<string | null>(null);
  const [actionMessage, setActionMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);
  const [expandedFuture, setExpandedFuture] = useState<Set<string>>(new Set());

  async function load() {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchSources();
      setSources(data.sources);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load sources');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  const showAction = (text: string, type: 'success' | 'error') => {
    setActionMessage({ text, type });
    setTimeout(() => setActionMessage(null), 3000);
  };

  const handleToggle = async (source: InvestmentSource) => {
    setTogglingId(source.id);
    try {
      const updated = await toggleSourceActive(source.id, !source.active);
      setSources(prev => prev.map(s => s.id === updated.id ? updated : s));
      showAction(`${updated.name} ${updated.active ? 'enabled' : 'disabled'} in registry only; scanner coverage is unchanged`, 'success');
    } catch (err) {
      showAction(err instanceof Error ? err.message : 'Failed to update source', 'error');
    } finally {
      setTogglingId(null);
    }
  };

  const formatDate = (val: string | null) => {
    if (!val) return '-';
    return new Date(val).toLocaleString();
  };

  const toggleFuture = (key: string) =>
    setExpandedFuture(prev => {
      const next = new Set(prev);
      next.has(key) ? next.delete(key) : next.add(key);
      return next;
    });

  const operational = sources.filter(s => s.active);
  const placeholder = sources.filter(s => !s.active);

  return (
    <div className="page-container--wide animate-fade-in">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 32 }}>
        <Link href="/" className="nav-back">← Mission Control</Link>
        <Link href="/investment/evaluations" className="nav-back">Evaluation Queue →</Link>
      </div>

      <div className="page-header">
        <h1 className="page-title">Investment Sources</h1>
        <p className="page-subtitle">Source registry — enable / disable only, no scan triggered</p>
      </div>

      <div className="card card-accent" style={{ marginBottom: 24, borderLeftColor: 'var(--status-preview-border)' }}>
        <p className="card-desc" style={{ color: 'var(--status-preview-text)', marginBottom: 6 }}>
          Operational warning: current scheduled investment scans do not read this registry yet.
        </p>
        <p className="card-desc">
          Enable/disable changes are saved to `investment_sources`, but scanner coverage remains the hardcoded SEC EDGAR adapter until the source-driven intake sprint wires it in.
        </p>
      </div>

      {actionMessage && (
        <div className="card card-accent" style={{ marginBottom: 24, padding: '12px 16px', borderLeftColor: actionMessage.type === 'success' ? 'var(--status-active-border)' : 'var(--status-preview-border)' }}>
          <p className="card-desc" style={{ color: actionMessage.type === 'success' ? 'var(--status-active-text)' : 'var(--status-preview-text)' }}>
            {actionMessage.type === 'success' ? '✓' : '⚠'} {actionMessage.text}
          </p>
        </div>
      )}

      <div className="top-bar" style={{ marginBottom: 40 }}>
        <div className="top-bar-stat">
          <span className="top-bar-label">Registry Active</span>
          <span className="top-bar-value">{loading ? '—' : operational.length} active</span>
        </div>
        <div className="top-bar-stat">
          <span className="top-bar-label">Registry Inactive</span>
          <span className="top-bar-value">{loading ? '—' : placeholder.length} inactive</span>
        </div>
        <div className="top-bar-stat">
          <span className="top-bar-label">Future Methodology</span>
          <span className="top-bar-value">{FUTURE_SOURCES.length} categories</span>
        </div>
      </div>

      {loading && (
        <div className="loading-state">
          <div className="loading-spinner" />
          Loading sources...
        </div>
      )}

      {error && (
        <div className="card card-accent" style={{ marginBottom: 24, borderLeftColor: 'var(--status-preview-border)' }}>
          <p className="card-desc" style={{ color: 'var(--status-preview-text)' }}>⚠ {error}</p>
        </div>
      )}

      {!loading && !error && (
        <>
          <div style={{ marginBottom: 40 }}>
            <div className="section-header">
              <span className="section-title">A — Registry Active</span>
              <span className="status-badge status-badge--active">{operational.length} active</span>
              <span className="section-count">Live DB rows — not scanner control yet</span>
              <div className="section-line" />
            </div>
            {operational.length === 0 ? (
              <div className="empty-state">
                <div className="empty-state-title">No active sources</div>
                <div className="empty-state-desc">Enable a source from the placeholder section below.</div>
              </div>
            ) : (
              <SourceTable sources={operational} togglingId={togglingId} onToggle={handleToggle} formatDate={formatDate} />
            )}
          </div>

          <div style={{ marginBottom: 40 }}>
            <div className="section-header">
              <span className="section-title">B — Placeholder</span>
              <span className="status-badge status-badge--preview">{placeholder.length} inactive</span>
              <span className="section-count">Configured but disabled</span>
              <div className="section-line" />
            </div>
            {placeholder.length === 0 ? (
              <div className="empty-state">
                <div className="empty-state-title">No inactive sources</div>
                <div className="empty-state-desc">All configured sources are currently active.</div>
              </div>
            ) : (
              <SourceTable sources={placeholder} togglingId={togglingId} onToggle={handleToggle} formatDate={formatDate} />
            )}
          </div>

          <div style={{ marginBottom: 24 }}>
            <div className="section-header">
              <span className="section-title">C — Future Methodology</span>
              <span className="status-badge status-badge--readonly">{FUTURE_SOURCES.length} categories</span>
              <span className="section-count">Source map v1.0 — not yet in DB</span>
              <div className="section-line" />
            </div>
            <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
              <div style={{ padding: '10px 16px', borderBottom: '1px solid var(--border-subtle)', background: 'var(--bg-subtle)' }}>
                <p className="card-desc">Data requirements derived from course methodology source map. Not inserted into DB — reference only.</p>
              </div>
              <div>
                {FUTURE_SOURCES.map((fs, idx) => {
                  const style = AVAILABILITY_STYLE[fs.availability];
                  const isExpanded = expandedFuture.has(fs.category);
                  return (
                    <div key={fs.category} style={{ borderTop: idx === 0 ? 'none' : '1px solid var(--border-subtle)', padding: '12px 16px' }}>
                      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
                        <span className={style.badge}>{style.label}</span>
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <p style={{ fontFamily: 'var(--font-mono)', fontSize: 13, fontWeight: 500, color: 'var(--text-primary)', margin: 0 }}>{fs.category}</p>
                          <p className="card-desc" style={{ marginTop: 2 }}>{fs.note}</p>
                          {fs.courseRefs.length > 0 && (
                            <button
                              onClick={() => toggleFuture(fs.category)}
                              className="course-ref-toggle"
                            >
                              {isExpanded ? '▾ COURSE REF' : '▸ COURSE REF'}
                            </button>
                          )}
                          {isExpanded && <CourseRefPanel refs={fs.courseRefs} />}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
              <div style={{ padding: '10px 16px', borderTop: '1px solid var(--border-subtle)', background: 'var(--bg-subtle)' }}>
                <p className="card-desc">AUTOMATED = API integration feasible · MANUAL = subscription or human review required · UNAVAILABLE = not disclosed in public filings</p>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
