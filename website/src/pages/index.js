import React from 'react';
import Layout from '@theme/Layout';

const STATS = { docs: 255, tickets: 657, artifacts: 469 };

export default function Home() {
  return (
    <Layout title="RPG Simulation Docs" description="Project documentation hub">
      <main style={{padding: '2rem', maxWidth: '900px', margin: '0 auto'}}>
        <h1>RPG Simulation Documentation</h1>
        <p style={{color: '#666'}}>
          {STATS.docs} documents · {STATS.tickets} closed tickets · {STATS.artifacts} artifact sets
        </p>
        <h2>Quick Links — Authoritative Docs (P0)</h2>
        <ul>
          <li><a href="/docs/mechanics/01-entity-anatomy">Entity Anatomy</a> — Core attributes and biological pressures</li>
          <li><a href="/docs/mechanics/02-combat-laws">Combat Laws</a> — Damage formula and tactical modifiers</li>
          <li><a href="/docs/mechanics/03-economic-laws">Economic Laws</a> — Atomic conservation and trade</li>
          <li><a href="/docs/mechanics/04-strategic-cognition">Strategic Cognition</a> — Goal hierarchy and perception</li>
          <li><a href="/docs/mechanics/05-world-evolution">World Evolution</a> — Tick-to-day time and ecology</li>
          <li><a href="/docs/mechanics/06-worldbuilding-foundation">Worldbuilding Foundation</a> — Declarative topology</li>
        </ul>
        <h2>Content Sections</h2>
        <ul>
          <li><a href="/docs/">Docs</a> — Mechanics, engine contracts, architecture, guidelines</li>
          <li><a href="/tickets/">Tickets</a> — Closed ticket history ({STATS.tickets} tickets)</li>
          <li><a href="/artifacts/">Artifacts</a> — Investigation, plan, and test_plan files per ticket</li>
          <li><a href="/docs/archive/">Archive</a> — Historical docs and design specs</li>
        </ul>
        <p style={{marginTop: '2rem', fontSize: '0.9em', color: '#888'}}>
          Run <code>make docs-serve</code> to start this site locally. Run <code>make docs-registry</code> to regenerate the doc registry.
        </p>
      </main>
    </Layout>
  );
}
