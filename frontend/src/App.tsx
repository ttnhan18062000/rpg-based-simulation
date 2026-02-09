import { useState, useCallback } from 'react';
import { useSimulation } from '@/hooks/useSimulation';
import { Header } from '@/components/Header';
import { GameCanvas } from '@/components/GameCanvas';
import { Sidebar } from '@/components/Sidebar';
import type { Building, GroundItem } from '@/types/api';

function App() {
  const sim = useSimulation();
  const [inspectedLoot, setInspectedLoot] = useState<GroundItem | null>(null);
  const [selectedBuilding, setSelectedBuilding] = useState<Building | null>(null);

  const handleBuildingClick = useCallback((building: Building) => {
    setSelectedBuilding(building);
    setInspectedLoot(null);
    sim.selectEntity(null);
  }, [sim.selectEntity]);

  const handleGroundItemClick = useCallback((x: number, y: number) => {
    const gi = sim.groundItems.find(g => g.x === x && g.y === y);
    setInspectedLoot(gi || null);
    setSelectedBuilding(null);
  }, [sim.groundItems]);

  const handleSelectEntity = useCallback((id: number | null) => {
    sim.selectEntity(id);
    if (id !== null) {
      setInspectedLoot(null);
      setSelectedBuilding(null);
    }
  }, [sim.selectEntity]);

  return (
    <div className="h-screen flex flex-col overflow-hidden">
      <Header
        tick={sim.tick}
        aliveCount={sim.aliveCount}
        totalSpawned={sim.totalSpawned}
        totalDeaths={sim.totalDeaths}
        status={sim.status}
      />
      <div className="flex flex-1 min-h-0">
        <GameCanvas
          mapData={sim.mapData}
          entities={sim.entities}
          groundItems={sim.groundItems}
          buildings={sim.buildings}
          resourceNodes={sim.resourceNodes}
          selectedEntityId={sim.selectedEntityId}
          onEntityClick={handleSelectEntity}
          onGroundItemClick={handleGroundItemClick}
          onBuildingClick={handleBuildingClick}
        />
        <Sidebar
          entities={sim.entities}
          events={sim.events}
          mapData={sim.mapData}
          selectedEntityId={sim.selectedEntityId}
          onSelectEntity={handleSelectEntity}
          sendControl={sim.sendControl}
          setSpeed={sim.setSpeed}
          inspectedLoot={inspectedLoot}
          onClearLoot={() => setInspectedLoot(null)}
          selectedBuilding={selectedBuilding}
          onClearBuilding={() => setSelectedBuilding(null)}
          clearEvents={sim.clearEvents}
        />
      </div>
    </div>
  );
}

export default App;
