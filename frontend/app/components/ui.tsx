'use client';

import Link from 'next/link';
import React from 'react';

// ─── PageHeader ────────────────────────────────────────────────────────────

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  backHref?: string;
  backLabel?: string;
  badge?: React.ReactNode;
  actions?: React.ReactNode;
}

export function PageHeader({ title, subtitle, backHref, backLabel, badge, actions }: PageHeaderProps) {
  return (
    <div className="page-header">
      {backHref && (
        <div className="mb-4">
          <Link href={backHref} className="nav-back">
            ← {backLabel ?? 'Back'}
          </Link>
        </div>
      )}
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="page-title">{title}</h1>
            {badge}
          </div>
          {subtitle && <p className="page-subtitle mt-1">{subtitle}</p>}
        </div>
        {actions && <div className="flex items-center gap-2 flex-shrink-0">{actions}</div>}
      </div>
    </div>
  );
}

// ─── SectionCard ───────────────────────────────────────────────────────────

interface SectionCardProps {
  title?: string;
  children: React.ReactNode;
  className?: string;
  accent?: boolean;
}

export function SectionCard({ title, children, className = '', accent }: SectionCardProps) {
  return (
    <div className={`card ${accent ? 'card-accent' : ''} ${className}`}>
      {title && (
        <div className="section-header" style={{ marginBottom: '16px' }}>
          <span className="section-title">{title}</span>
          <div className="section-line" />
        </div>
      )}
      {children}
    </div>
  );
}

// ─── StatusBadge ───────────────────────────────────────────────────────────

const BADGE_MAP: Record<string, string> = {
  // workflow
  detected:             'status-badge--readonly',
  reviewing:            'status-badge--partial',
  watchlist:            'status-badge--active',
  ignored:              'status-badge--readonly',
  archived:             'status-badge--readonly',
  published:            'status-badge--active',
  // research case status
  brief_generated:      'status-badge--partial',
  under_investigation:  'status-badge--manual',
  documented:           'status-badge--active',
  // readiness
  monitor:              'status-badge--preview',
  not_actionable:       'status-badge--readonly',
  needs_more_work:      'status-badge--preview',
  candidate:            'status-badge--active',
  // playbook
  evaluator_ready:      'status-badge--active',
  partial:              'status-badge--preview',
  detection_only:       'status-badge--readonly',
  // recommendation
  deep_research:        'status-badge--manual',
  human_review_required:'status-badge--preview',
  // evaluator
  v1:                   'status-badge--readonly',
  v2:                   'status-badge--partial',
  // agent ops
  active:               'status-badge--active',
  planned:              'status-badge--readonly',
  observer:             'status-badge--readonly',
  manual:               'status-badge--manual',
  placeholder:          'status-badge--readonly',
  deferred:             'status-badge--readonly',
  // historical cases
  seed:                 'status-badge--readonly',
  reconstructed:        'status-badge--partial',
  lessons_extracted:    'status-badge--active',
  source_intel_applied: 'status-badge--manual',
  // source intel
  proposed:             'status-badge--preview',
  approved:             'status-badge--active',
  rejected:             'status-badge--readonly',
  // public drafts
  draft:                'status-badge--readonly',
  in_review:            'status-badge--preview',
  // system aliases (hyphenated forms)
  'read-only':          'status-badge--readonly',
};

interface StatusBadgeProps {
  value: string;
  label?: string;
}

export function StatusBadge({ value, label }: StatusBadgeProps) {
  const key = value.toLowerCase().replace(/ /g, '_');
  const cls = BADGE_MAP[key] ?? 'status-badge--readonly';
  const display = label ?? value.replace(/_/g, ' ');
  return (
    <span className={`status-badge ${cls}`}>{display}</span>
  );
}

// ─── EmptyState ────────────────────────────────────────────────────────────

interface EmptyStateProps {
  icon?: string;
  title: string;
  description?: string;
  children?: React.ReactNode;
}

export function EmptyState({ icon, title, description, children }: EmptyStateProps) {
  return (
    <div className="empty-state">
      {icon && <div className="empty-state-icon">{icon}</div>}
      <div className="empty-state-title">{title}</div>
      {description && <div className="empty-state-desc">{description}</div>}
      {children}
    </div>
  );
}

// ─── LoadingState ──────────────────────────────────────────────────────────

export function LoadingState({ label = 'Loading…' }: { label?: string }) {
  return (
    <div className="loading-state">
      <div className="loading-spinner" />
      <span>{label}</span>
    </div>
  );
}

// ─── ErrorBanner ───────────────────────────────────────────────────────────

export function ErrorBanner({ message }: { message: string }) {
  return (
    <div style={{
      padding: '12px 16px',
      background: '#fff8f8',
      border: '1px solid #f5c6cb',
      borderRadius: '8px',
      fontFamily: 'var(--font-mono)',
      fontSize: '12px',
      color: '#8b2020',
      marginBottom: '24px',
    }}>
      Error: {message}
    </div>
  );
}

// ─── InfoBanner ────────────────────────────────────────────────────────────

interface InfoBannerProps {
  children: React.ReactNode;
  variant?: 'info' | 'warning' | 'guardrail';
}

export function InfoBanner({ children, variant = 'info' }: InfoBannerProps) {
  const styles: Record<string, React.CSSProperties> = {
    info: {
      background: 'var(--bg-subtle)',
      border: '1px solid var(--border-default)',
      color: 'var(--text-secondary)',
    },
    warning: {
      background: '#fffbf0',
      border: '1px solid #f0d080',
      color: '#7a5a00',
    },
    guardrail: {
      background: '#f5f4f1',
      border: '1px solid var(--border-strong)',
      color: 'var(--text-muted)',
    },
  };
  return (
    <div style={{
      ...styles[variant],
      padding: '10px 14px',
      borderRadius: '8px',
      fontFamily: 'var(--font-mono)',
      fontSize: '11px',
      lineHeight: '1.5',
      marginBottom: '24px',
    }}>
      {children}
    </div>
  );
}

// ─── MetricRow ─────────────────────────────────────────────────────────────

export function MetricRow({ items }: { items: { label: string; value: string | number }[] }) {
  return (
    <div className="card-metrics">
      {items.map(({ label, value }) => (
        <div key={label} className="metric-pill">
          <div className="metric-value">{value}</div>
          <div className="metric-label">{label}</div>
        </div>
      ))}
    </div>
  );
}
