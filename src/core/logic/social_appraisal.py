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
        """주변 타겟들과의 유대 관계를 바탕으로 각 목표 유형에 대한 가중치(Bias)를 반환합니다."""
        
        social_biases = {gt: 0.0 for gt in GoalType}
        
        for target in targets:
            if target.id == actor.id:
                continue
                
            bond = registry.get_bond(actor.id, target.id)
            
            # 1. Trust (신뢰): 동료 돕기 및 함께하기 유도
            if bond.trust > 0.5:
                # 높은 신뢰 관계: 사회적 상호작용 및 보호 유도
                social_biases[GoalType.SOCIAL] += bond.trust * 0.5
                social_biases[GoalType.GUARD] += bond.trust * 0.3
                
            # 2. Fear (공포): 회피 및 도망 유도
            if bond.fear > 0.6:
                # 높은 공포 관계: 위협 감지 시 도망치려는 성향 증가
                social_biases[GoalType.FLEE] += bond.fear * 1.5 # 공포는 매우 높은 비중
                
            # 3. Rivalry (라이벌): 경쟁 및 공격 유도
            if bond.rivalry > 0.6:
                # 높은 라이벌 관계: 전투 및 아이템 획득 경쟁 유도
                social_biases[GoalType.COMBAT] += bond.rivalry * 0.4
                social_biases[GoalType.LOOT] += bond.rivalry * 0.3
                
            # 4. Familiarity (친밀도): 친숙한 존재와 머무르는 성향
            if bond.familiarity > 0.4:
                social_biases[GoalType.SOCIAL] += bond.familiarity * 0.2
        
        return social_biases
