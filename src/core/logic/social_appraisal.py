"""Social Appraisal Service — 사회적 유대감을 주관적 동기(Motives)로 변환합니다. [PHASE 1]

이 모듈은 주변 엔티티와의 사회적 관계(Trust, Fear, Rivalry)를 분석하여
AI의 목표 유틸리티에 대한 가중치(Bias)를 결정합니다.
"""

from typing import TYPE_CHECKING, Dict
from src.core.models.enums import GoalType

if TYPE_CHECKING:
    from src.core.entities.entity import Entity
    from src.core.models.social import SocialRegistry

class SocialAppraisalService:
    """사회적 관계를 기반으로 동기 가중치를 계산하는 서비스."""

    @staticmethod
    def calculate_social_motives(actor: 'Entity', targets: list['Entity'], registry: 'SocialRegistry') -> Dict[GoalType, float]:
        """주변 타겟들과의 유대 관계 및 글로벌 평판을 바탕으로 각 목표 유형에 대한 가중치(Bias)를 반환합니다."""
        
        social_biases = {gt: 0.0 for gt in GoalType}
        mind = actor.mind
        
        for target in targets:
            if target.id == actor.id:
                continue
                
            # Authoritative bond from registry (read-only: safe on frozen snapshots)
            bond = registry.get_bond_or_none(actor.id, target.id)
            
            # Reputation impact (Subjective: actor's caution affects how they view low reputation)
            reputation = registry.get_reputation(target.id)
            if reputation < -20:
                # Target is an outcast/villain: Increase caution/combat if we are cautious
                social_biases[GoalType.FLEE] += abs(reputation) * 0.01 * mind.decision.personality.caution
                social_biases[GoalType.COMBAT] += abs(reputation) * 0.005 * mind.decision.personality.aggression

            # 1. Trust (신뢰): 동료 돕기 및 함께하기 유도
            if bond and bond.trust > 0.5:
                # 높은 신뢰 관계: 사회적 상호작용 및 보호 유도
                social_biases[GoalType.SOCIAL] += bond.trust * 0.5
                social_biases[GoalType.GUARD] += bond.trust * 0.3
                
            # 2. Fear (공포): 회피 및 도망 유도
            if bond and bond.fear > 0.6:
                # 높은 공포 관계: 위협 감지 시 도망치려는 성향 증가
                social_biases[GoalType.FLEE] += bond.fear * 1.5 # 공포는 매우 높은 비중
                
            # 3. Rivalry (라이벌): 경쟁 및 공격 유도
            if bond and bond.rivalry > 0.6:
                # 높은 라이벌 관계: 전투 및 아이템 획득 경쟁 유도
                social_biases[GoalType.COMBAT] += bond.rivalry * 0.4
                social_biases[GoalType.LOOT] += bond.rivalry * 0.3
                
            # 4. Familiarity (친밀도): 친숙한 존재와 머무르는 성향
            if bond and bond.familiarity > 0.4:
                social_biases[GoalType.SOCIAL] += bond.familiarity * 0.2

            
            # --- [STAGE 5] Narrative Memory Influence ---
            # Search recent episodic memories for this target
            recent_memories = [m for m in mind.narrative.memory_log if getattr(m.details, "target_id", None) == target.id]
            for m in recent_memories[-10:]: # Look at last 10 relevant memories
                if m.type == "combat":
                    # Success breeds confidence
                    social_biases[GoalType.COMBAT] += m.impact * 0.1
                elif m.type == "trauma":
                    # Past pain breeds caution/fear
                    social_biases[GoalType.FLEE] += m.impact * 0.2
                elif m.type == "social":
                    # Positive social history increases rapport
                    social_biases[GoalType.SOCIAL] += m.impact * 0.1
        
        return social_biases
