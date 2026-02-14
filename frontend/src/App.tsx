import { useState, useCallback } from 'react';
import { useSimulation } from '@/hooks/useSimulation';
import { Header, type PageView } from '@/components/Header';
import { GameCanvas } from '@/components/GameCanvas';
import { Sidebar } from '@/components/Sidebar';
import { ApiDocsPage } from '@/components/ApiDocsPage';
import type { Building, GroundItem } from '@/types/api';

function App() {
  const sim = useSimulation();
  const [inspectedLoot, setInspectedLoot] = useState<GroundItem | null>(null);
  const [selectedBuilding, setSelectedBuilding] = useState<Building | null>(null);
  const [currentPage, setCurrentPage] = useState<PageView>('simulation');

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
        currentPage={currentPage}
        onPageChange={setCurrentPage}
      />
      {currentPage === 'simulation' ? (
        <div className="flex flex-1 min-h-0">
          <GameCanvas
            mapData={sim.mapData}
            entities={sim.entities}
            selectedEntity={sim.selectedEntity}
            groundItems={sim.groundItems}
            buildings={sim.buildings}
            resourceNodes={sim.resourceNodes}
            regions={sim.regions}
            selectedEntityId={sim.selectedEntityId}
            onEntityClick={handleSelectEntity}
            onGroundItemClick={handleGroundItemClick}
            onBuildingClick={handleBuildingClick}
          />
          <Sidebar
            entities={sim.entities}
            selectedEntity={sim.selectedEntity}
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
      ) : (
        <ApiDocsPage />
      )}
    </div>
  );
}

export default App;
