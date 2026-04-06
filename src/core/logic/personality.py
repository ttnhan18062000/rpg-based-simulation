"""Personality Logic — OCEAN 기반의 행동 편향 및 유틸리티 조정을 처리합니다. [PHASE 1]

이 모듈은 엔티티의 성격 특성(Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism)을
AI의 목표 유틸리티 계산에 적용하는 무상태(stateless) 유틸리티 함수들을 제공합니다.
"""

from typing import TYPE_CHECKING
from src.core.models.enums import GoalType

if TYPE_CHECKING:
    from src.core.aspects.identity import IdentityAspect

class PersonalityLogic:
    """OCEAN 특성을 기반으로 목표 유틸리티를 조정하는 서비스."""

    @staticmethod
    def apply_motive_biases(goal_type: GoalType, base_utility: float, identity: 'IdentityAspect') -> float:
        """성격 특성에 따라 기본 유틸리티 점수에 가중치를 적용합니다."""
        
        multiplier = 1.0
        
        # 1. Openness (개방성): 새로운 지역 탐색 및 루틴 외 행동 선호
        if goal_type == GoalType.EXPLORE:
            multiplier += identity.openness * 0.5
            
        # 2. Conscientiousness (성실성): 루틴, 휴식, 의무 관련 목표 선호
        elif goal_type in [GoalType.REST, GoalType.SLEEP, GoalType.GUARD]:
            multiplier += identity.conscientiousness * 0.4
            
        # 3. Extraversion (외향성): 사회적 상호작용 및 그룹 활동 선호
        elif goal_type == GoalType.SOCIAL:
            multiplier += identity.extraversion * 0.6
            
        # 4. Agreeableness (우호성): 타인 돕기 선호 및 이기적 행동 감소
        elif goal_type == GoalType.LOOT:
            # 우호적인 엔티티는 공유되지 않은 전리품 획득에 덜 공격적일 수 있음
            multiplier -= identity.agreeableness * 0.3
            
        # 5. Neuroticism (신경증): 공포 및 위협에 대한 민감도
        elif goal_type == GoalType.FLEE:
            multiplier += identity.neuroticism * 0.7
            
        return max(0.0, base_utility * multiplier)
