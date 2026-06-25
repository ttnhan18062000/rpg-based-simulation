import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path.cwd()))

from src.api.engine_manager import V2EngineManager
from src.config.profiles import RuntimeProfile
from src.api.presenters.state_presenter import StatePresenter

from src.config.profiles import PROD_DEFAULT

def test_api_paged():
    profile = PROD_DEFAULT
    manager = V2EngineManager(profile, entities_count=50)
    try:
        # Test paged retrieval
        page1 = manager.get_entities_paged(offset=0, limit=10)
        print(f"Page 1 entities: {len(page1['entities'])}")
        assert len(page1['entities']) == 10
        assert page1['total'] == 50

        page2 = manager.get_entities_paged(offset=10, limit=10)
        print(f"Page 2 entities: {len(page2['entities'])}")
        assert len(page2['entities']) == 10

        # Verify no overlap in IDs
        ids1 = {e['id'] for e in page1['entities']}
        ids2 = {e['id'] for e in page2['entities']}
        assert ids1.isdisjoint(ids2)

        # Test single entity lookup
        eid = sorted(list(ids1))[0]
        entity = manager.get_entity(eid)
        print(f"Single entity lookup for {eid}: {entity['id'] if entity else 'None'}")
        assert entity is not None
        assert entity['id'] == eid

        print("API Paging Tests Passed!")
    finally:
        manager.stop()

if __name__ == "__main__":
    test_api_paged()
