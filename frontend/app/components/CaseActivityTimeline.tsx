'use client';

import type { CaseActivityEvent } from '@/lib/api';
import type React from 'react';
import { EmptyState, SectionCard, StatusBadge } from './ui';

function formatTime(value: string | null): string {
  if (!value) return 'Current state - timestamp unavailable';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function eventTypeLabel(value: string): string {
  return value.replace(/_/g, ' ');
}

function originLabel(value: string): string {
  return value.replace(/_/g, ' ');
}

function eventTone(status: string): React.CSSProperties {
  if (status === 'needs_attention' || status === 'manual_review_required') {
    return { borderColor: '#f0d080', background: '#fffbf0' };
  }
  if (status === 'evidence_found' || status === 'completed') {
    return { borderColor: '#b8d8c0', background: '#f6fbf7' };
  }
  if (status === 'rejected') {
    return { borderColor: '#e0c2c2', background: '#fff8f8' };
  }
  return {};
}

function TimelineRow({ event, compact }: { event: CaseActivityEvent; compact?: boolean }) {
  return (
    <div
      className="rounded-md border border-[var(--border-default)] bg-white p-3"
      style={eventTone(event.status)}
    >
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <StatusBadge value={event.event_type} label={eventTypeLabel(event.event_type)} />
            <StatusBadge value={event.status} />
            {event.agent_name && <span className="status-badge status-badge--manual">{event.agent_name}</span>}
          </div>
          <h3 className="mt-2 text-sm font-semibold text-slate-950">{event.title}</h3>
        </div>
        <span className="font-mono text-[11px] text-slate-500">{formatTime(event.timestamp)}</span>
      </div>
      {!compact && (
        <>
          <p className="mt-2 text-sm leading-6 text-slate-700">{event.description}</p>
          <div className="mt-3 flex flex-wrap gap-2 text-[11px] font-mono text-slate-500">
            <span>Origin: {originLabel(event.origin)}</span>
            <span>Entity: {event.related_entity_type}</span>
            {event.metadata_only && <span>Metadata-only</span>}
            {event.link_url && (
              <a className="text-emerald-700 underline" href={event.link_url} target="_blank" rel="noreferrer">
                Open stored link
              </a>
            )}
          </div>
        </>
      )}
    </div>
  );
}

export function CaseActivityTimeline({
  title = 'Case Activity Log',
  events,
  error,
  compact = false,
  limit,
}: {
  title?: string;
  events: CaseActivityEvent[];
  error?: string | null;
  compact?: boolean;
  limit?: number;
}) {
  const visibleEvents = typeof limit === 'number' ? events.slice(0, limit) : events;
  const timestamped = visibleEvents.filter((event) => event.timestamp);
  const currentState = visibleEvents.filter((event) => !event.timestamp);
  const needsAttention = events.filter((event) => event.status === 'needs_attention' || event.status === 'manual_review_required').length;

  return (
    <SectionCard title={title} accent={!compact}>
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <StatusBadge value="read-only" label="Derived timeline" />
        <StatusBadge value="manual" label="Manual review" />
        {needsAttention > 0 && <StatusBadge value="needs_attention" label={`${needsAttention} need attention`} />}
      </div>
      <p className="mb-4 text-xs leading-5 text-slate-500">
        Derived timeline - not a persisted audit log yet. Derived from current case state; does not trigger autonomous runs and does not fetch document bodies.
      </p>
      {error && (
        <div className="mb-4 rounded-md border border-red-200 bg-red-50 p-3 text-xs text-red-700">
          {error}
        </div>
      )}
      {!visibleEvents.length ? (
        <EmptyState title="No timeline entries yet" description="The case has no derived activity entries available from stored metadata." />
      ) : (
        <div className="space-y-4">
          {timestamped.length > 0 && (
            <div className="space-y-3">
              {!compact && <div className="font-mono text-xs uppercase text-slate-500">Timestamped activity</div>}
              {timestamped.map((event) => <TimelineRow key={event.id} event={event} compact={compact} />)}
            </div>
          )}
          {currentState.length > 0 && (
            <div className="space-y-3">
              {!compact && <div className="font-mono text-xs uppercase text-slate-500">Current state - timestamp unavailable</div>}
              {currentState.map((event) => <TimelineRow key={event.id} event={event} compact={compact} />)}
            </div>
          )}
        </div>
      )}
    </SectionCard>
  );
}
