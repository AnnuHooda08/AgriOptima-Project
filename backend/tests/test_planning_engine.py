import pytest
from app.schemas.plan import FarmProfile
from app.schemas.what_if import WhatIfRequest
from app.services.planning_engine import planning_engine

def test_full_plan_generation_math():
    profile = FarmProfile(
        state="Haryana",
        district="Ambala",
        area_ha=3.0,
        season="Kharif",
        N=90.0, P=42.0, K=43.0,
        temperature=25.0, humidity=80.0,
        ph=6.5, rainfall=250.0,
        storage_months=0
    )

    plan_res = planning_engine.generate_full_plan(profile)
    plan = plan_res.selected_plan

    # 1. Production math
    expected_tonnes = round(plan.predicted_yield_tonnes_per_ha * 3.0, 2)
    assert abs(plan.gross_production_tonnes - expected_tonnes) < 0.05

    # 2. Quintal conversion: 1 tonne = 10 quintals
    expected_quintals = round(plan.gross_production_tonnes * 10.0, 2)
    assert abs(plan.gross_production_quintals - expected_quintals) < 0.05

    # 3. Post-harvest loss applied exactly once
    loss_fraction = plan.total_loss_percentage / 100.0
    expected_marketable = round(plan.gross_production_quintals * (1.0 - loss_fraction), 2)
    assert abs(plan.marketable_production_quintals - expected_marketable) < 0.05

    # 4. Gross revenue
    expected_revenue = round(plan.marketable_production_quintals * plan.applicable_price_per_quintal, 2)
    assert abs(plan.gross_revenue_rs - expected_revenue) < 0.05

    # 5. Cost summation
    expected_total_costs = round(
        plan.cultivation_cost_rs + plan.transport_cost_rs + plan.storage_cost_rs + plan.packaging_cost_rs, 2
    )
    assert abs(plan.total_costs_rs - expected_total_costs) < 0.05

    # 6. Net return = Gross Revenue - Total Costs
    expected_net_return = round(plan.gross_revenue_rs - plan.total_costs_rs, 2)
    assert abs(plan.net_return_rs - expected_net_return) < 0.05

    # 7. ROI % = (Net Return / Total Costs) * 100
    expected_roi = round((plan.net_return_rs / plan.total_costs_rs) * 100.0, 1)
    assert abs(plan.roi_percentage - expected_roi) < 0.1

def test_what_if_price_and_yield_shocks():
    profile = FarmProfile(
        state="Haryana",
        district="Ambala",
        area_ha=2.0,
        season="Kharif",
        N=90.0, P=42.0, K=43.0,
        temperature=25.0, humidity=80.0,
        ph=6.5, rainfall=250.0,
        storage_months=0
    )
    base_plan = planning_engine.generate_full_plan(profile).selected_plan

    # Scenario: +20% price increase, 0% yield shock, 2 months storage
    req = WhatIfRequest(
        base_plan=base_plan,
        price_change_pct=20.0,
        yield_shock_pct=0.0,
        storage_months=2
    )

    sim_res = planning_engine.simulate_what_if(req)
    
    # Simulated price should be exactly 1.20 * base price
    expected_sim_price = round(base_plan.applicable_price_per_quintal * 1.20, 2)
    assert abs(sim_res.simulated_price_quintal - expected_sim_price) < 0.05

    # Storage cost should reflect 2 months of warehousing
    assert sim_res.simulated_plan.storage_cost_rs > 0
    assert sim_res.simulated_plan.storage_cost_rs == round(sim_res.simulated_marketable_quintals * 2 * 45.0, 2)

    # Net return diff should equal simulated net return - original net return
    expected_diff = round(sim_res.simulated_net_return - base_plan.net_return_rs, 2)
    assert abs(sim_res.diff_net_return - expected_diff) < 0.05
