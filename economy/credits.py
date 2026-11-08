"""
Firestarter - Economy & Credit System
Implements Section 5.1:
Credits = Integral( k_heat * T_core + k_eff * (Energy_Produced / Fuel_Consumed) ) dt
"""

from firestarter.config import CREDIT_K_HEAT, CREDIT_K_EFF

class CreditSystem:
    def __init__(self, starting_credits: float = 20.0):
        self.credits = starting_credits
        self.total_earned = starting_credits
        self.current_burn_rate_score = 0.0

    def update(
        self,
        dt: float,
        core_temp_c: float,
        energy_rate_watts: float,
        fuel_consumption_rate_kg_s: float
    ) -> float:
        """
        Integrates credit accumulation over dt.
        """
        # Only earn credits if fire is actively burning (> 120°C)
        if core_temp_c < 120.0 or energy_rate_watts < 10.0:
            self.current_burn_rate_score = 0.0
            return 0.0

        # Efficiency: Energy produced per kg fuel consumed
        eff = energy_rate_watts / max(1e-4, fuel_consumption_rate_kg_s * 1e6)
        
        # Credit rate = k_heat * T_core + k_eff * eff
        rate = CREDIT_K_HEAT * (core_temp_c / 100.0) + CREDIT_K_EFF * min(5.0, eff)
        earned = rate * dt
        
        self.credits += earned
        self.total_earned += earned
        self.current_burn_rate_score = rate
        return earned

    def can_afford(self, amount: float) -> bool:
        return self.credits >= amount

    def spend(self, amount: float) -> bool:
        if self.can_afford(amount):
            self.credits -= amount
            return True
        return False
