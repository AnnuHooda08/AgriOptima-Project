import pytest
from app.schemas.plan import FarmProfile
from app.services.planning_engine import planning_engine


def test_full_plan_generation_math():
    profile = FarmProfile(
        state="Haryana",
        district="Ambala",
        area_ha=3.0,
        season="Kharif",
        N=90.0,
        P=42.0,
        K=43.0,
        temperature=25.0,
        humidity=80.0,
        ph=6.5,
        rainfall=250.0,
        storage_months=0,
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
    expected_marketable = round(
        plan.gross_production_quintals * (1.0 - loss_fraction), 2
    )
    assert abs(plan.marketable_production_quintals - expected_marketable) < 0.05

    # 4. Gross revenue
    expected_revenue = round(
        plan.marketable_production_quintals * plan.applicable_price_per_quintal, 2
    )
    assert abs(plan.gross_revenue_rs - expected_revenue) < 0.05

    # 5. Cost summation
    expected_total_costs = round(
        plan.cultivation_cost_rs
        + plan.transport_cost_rs
        + plan.storage_cost_rs
        + plan.packaging_cost_rs,
        2,
    )
    assert abs(plan.total_costs_rs - expected_total_costs) < 0.05

    # 6. Net return = Gross Revenue - Total Costs
    expected_net_return = round(plan.gross_revenue_rs - plan.total_costs_rs, 2)
    assert abs(plan.net_return_rs - expected_net_return) < 0.05

    # 7. ROI % = (Net Return / Total Costs) * 100
    expected_roi = round((plan.net_return_rs / plan.total_costs_rs) * 100.0, 1)
    assert abs(plan.roi_percentage - expected_roi) < 0.1




def test_plan_never_invents_generic_yields_for_unsupported_crop_labels():
    from app.services.model_service import model_service

    response = planning_engine.generate_full_plan(FarmProfile())
    plans = [response.selected_plan, *response.alternative_plans]
    assert len({plan.crop for plan in plans}) == len(plans)
    assert all(plan.crop in model_service.supported_crops for plan in plans)
    assert all('generic benchmark' not in note.lower()
               for plan in plans for note in plan.feasibility_notes)


@pytest.mark.parametrize('state', ['Haryana', 'Punjab'])
def test_rice_is_not_recommended_for_rabi(state):
    from app.services.planning_engine import recorded_crop_seasons
    rabi = planning_engine.generate_full_plan(FarmProfile(state=state, district='Amritsar' if state == 'Punjab' else 'Ambala', season='Rabi'))
    kharif = planning_engine.generate_full_plan(FarmProfile(state=state, district='Amritsar' if state == 'Punjab' else 'Ambala', season='Kharif'))
    assert kharif.selected_plan.crop == 'Rice'
    assert rabi.selected_plan.crop != 'Rice'
    for plan in [rabi.selected_plan, *rabi.alternative_plans]:
        assert (state.lower(), plan.crop.lower(), 'rabi') in recorded_crop_seasons()
    assert 'rice' not in rabi.seasonal_suitability_labels


@pytest.mark.parametrize('state', ['Punjab', 'Haryana'])
def test_ambiguous_source_moong_labels_do_not_make_it_a_winter_crop(state):
    # Inputs that strongly predict mungbean must not bypass seasonal screening.
    profile = FarmProfile(state=state, district='Amritsar' if state == 'Punjab' else 'Ambala', season='Rabi', N=20, P=20, K=20,
                          temperature=27, humidity=85, rainfall=100, ph=6.5)
    result = planning_engine.generate_full_plan(profile)
    assert all(plan.crop != 'Moong(Green Gram)'
               for plan in [result.selected_plan, *result.alternative_plans])
    assert 'mungbean' not in result.seasonal_suitability_labels


def test_whole_year_reporting_label_is_not_a_third_planting_season():
    with pytest.raises(ValueError, match='reporting category'):
        planning_engine.generate_full_plan(FarmProfile(state='Punjab', season='Whole Year'))


def test_custom_offer_is_not_reused_for_other_crops():
    response = planning_engine.generate_full_plan(FarmProfile(user_price_override=7777))
    assert response.selected_plan.applicable_price_per_quintal == 7777
    assert response.alternative_plans
    assert all(plan.applicable_price_per_quintal != 7777 for plan in response.alternative_plans)




def test_invalid_state_district_pair_is_rejected():
    with pytest.raises(ValueError, match='district'):
        planning_engine.generate_full_plan(FarmProfile(state='Punjab', district='Ambala'))


def test_loss_comes_from_state_crop_study_totals():
    from app.services.planning_engine import dataset_loss
    haryana, _, source = dataset_loss('Wheat', 'Haryana')
    punjab, _, _ = dataset_loss('Wheat', 'Punjab')
    assert haryana == 4.37
    assert punjab == 4.55
    assert 'NABCONS' in source




def test_model_loss_is_used_when_selected_and_manual_override_wins():
    from app.services.loss_service import model_loss
    profile = FarmProfile(loss_estimation_method='model')
    plan = planning_engine.generate_full_plan(profile).selected_plan
    assert plan.total_loss_percentage == model_loss(plan.crop, profile.state)
    assert 'Random Forest' in plan.loss_source
    manual = planning_engine.generate_full_plan(profile.model_copy(update={'loss_override_pct': 2})).selected_plan
    assert manual.total_loss_percentage == 2
    assert manual.loss_source.startswith('User-entered')


def test_missing_market_price_does_not_break_yield(monkeypatch):
    from app.services.planning_engine import PlanningEngine
    from app.services.mandi_service import mandi_service
    from app.schemas.plan import FarmProfile
    def unavailable(**kwargs):
        raise ValueError('No recorded market price')
    monkeypatch.setattr(mandi_service,'get_mandi_analysis',unavailable)
    plan=PlanningEngine.generate_full_plan(FarmProfile())
    assert plan.selected_plan.predicted_yield_tonnes_per_ha > 0
    assert plan.selected_plan.applicable_price_per_quintal is None
    assert plan.selected_plan.net_return_rs is None
