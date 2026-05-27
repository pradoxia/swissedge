import { fetchAgents, fetchCronUpcoming, type Agent, type CronEntry } from '@/lib/api';
import { CampusView } from './CampusView';

// Render dynamically — observability data should always be fresh.
export const dynamic = 'force-dynamic';

export const metadata = {
  title: 'SwissEdge — Operations Campus',
  description: 'Visual operations campus for the SwissEdge agent pipeline.',
};

export default async function CampusPage() {
  let agents: Agent[] = [];
  let cron: CronEntry[] = [];
  let backendError: string | null = null;

  try {
    const [agentsResponse, cronResponse] = await Promise.all([
      fetchAgents(),
      fetchCronUpcoming(1),
    ]);
    agents = agentsResponse.agents;
    cron = cronResponse.entries;
  } catch (err) {
    backendError =
      err instanceof Error
        ? err.message
        : 'Backend unreachable — using cached/empty state.';
  }

  return (
    <CampusView
      initialAgents={agents}
      initialCron={cron}
      backendError={backendError}
    />
  );
}
