import logging
from typing import Dict, List, Any, Optional

from app.schemas.plan import FarmProfile, CropPlan, PlanResponse
from app.schemas.what_if import WhatIfRequest, WhatIfResponse
from app.services.model_service import model_service, SUITABILITY_TO_YIELD_MAP
from app.services.mandi_service import mandi_service

logger = logging.getLogger(__name__)

# Post-harvest loss stages & percentages based on ICAR-CIPHET 2022 study
# (DataSets/post_harvest_loss_2022_haryana_punjab.csv)
POST_HARVEST_LOSS_PROFILES: Dict[str, Dict[str, Any]] = {
    "Bajra": {
        "total": 3.77,
        "stages": {"Harvesting": 0.69, "Collection": 0.29, "Threshing": 0.83, "Drying": 0.22, "Storage": 0.45, "Transport": 0.56, "Market": 0.73}
    },
    "Wheat": {
        "total": 4.37,
        "stages": {"Harvesting": 0.85, "Collection": 0.35, "Threshing": 0.95, "Drying": 0.30, "Storage": 0.62, "Transport": 0.50, "Market": 0.80}
    },
    "Cotton": {
        "total": 2.55,
        "stages": {"Harvesting": 1.70, "Collection": 0.20, "Drying": 0.05, "Storage": 0.04, "Transport": 0.33, "Market": 0.23}
    },
    "Cotton(lint)": {
        "total": 2.55,
        "stages": {"Harvesting": 1.70, "Collection": 0.20, "Drying": 0.05, "Storage": 0.04, "Transport": 0.33, "Market": 0.23}
    },
    "Sugarcane": {
        "total": 6.34,
        "stages": {"Harvesting": 2.10, "Field Handling": 1.14, "Transport": 1.50, "Milling Delay": 1.60}
    },
    "Potato": {
        "total": 5.57,
        "stages": {"Digging/Harvest": 1.80, "Sorting/Grading": 1.20, "Storage": 1.45, "Transport": 1.12}
    },
    "Rice": {
        "total": 4.20,
        "stages": {"Harvesting": 0.90, "Threshing": 0.85, "Drying": 0.45, "Storage": 0.75, "Transport": 0.55, "Milling": 0.70}
    },
    "Maize": {
        "total": 4.65,
        "stages": {"Harvesting": 1.10, "Shelling": 0.95, "Drying": 0.60, "Storage": 0.80, "Transport": 0.60, "Handling": 0.60}
    },
    "Mustard": {
        "total": 3.80,
        "stages": {"Harvesting": 1.05, "Threshing": 0.90, "Winnowing": 0.35, "Storage": 0.50, "Transport": 0.40, "Handling": 0.60}
    },
    "Rapeseed &Mustard": {
        "total": 3.80,
        "stages": {"Harvesting": 1.05, "Threshing": 0.90, "Winnowing": 0.35, "Storage": 0.50, "Transport": 0.40, "Handling": 0.60}
    },
    "Soyabean": {
        "total": 4.10,
        "stages": {"Harvesting": 1.20, "Threshing": 0.90, "Drying": 0.40, "Storage": 0.60, "Transport": 0.40, "Handling": 0.60}
    },
    "Gram": {
        "total": 4.50,
        "stages": {"Harvesting": 1.10, "Threshing": 0.90, "Winnowing": 0.40, "Storage": 0.90, "Transport": 0.50, "Handling": 0.70}
    },
    "Default": {
        "total": 4.00,
        "stages": {"Harvesting": 1.00, "Handling": 0.80, "Drying": 0.50, "Storage": 0.70, "Transport": 0.50, "Market": 0.50}
    }
}

# Cultivation operational costs per hectare (CACP Agricultural Price Commission Reports)
CULTIVATION_COST_PER_HA: Dict[str, float] = {
    "Rice": 45000.0,
    "Wheat": 35000.0,
    "Maize": 30000.0,
    "Cotton(lint)": 48000.0,
    "Cotton": 48000.0,
    "Bajra": 22000.0,
    "Rapeseed &Mustard": 25000.0,
    "Mustard": 25000.0,
    "Gram": 26000.0,
    "Soyabean": 28000.0,
    "Moong(Green Gram)": 24000.0,
    "Urad": 24000.0,
    "Arhar/Tur": 27000.0,
    "Barley": 26000.0,
    "Sugarcane": 85000.0,
    "Potato": 90000.0,
    "Onion": 75000.0,
    "Default": 30000.0
}

# Standard logistics and post-harvest operational unit rates
TRANSPORT_COST_PER_QUINTAL = 35.0   # Rs./quintal local farm-to-mandi cartage
STORAGE_COST_PER_QUINTAL_MONTH = 45.0 # Rs./quintal/month warehousing/cold-storage
PACKAGING_COST_PER_QUINTAL = 20.0   # Rs./quintal bagging and handling

class PlanningEngine:
    @staticmethod
    def generate_crop_plan(
        crop_name: str,
        profile: FarmProfile,
        suitability_rank: int = 1,
        is_suitable: bool = True
    ) -> CropPlan:
        """
        Builds a single connected crop plan incorporating:
        Yield model -> Production -> Unit Conversions -> Losses -> Mandi Price -> Financial Statement.
        """
        # Map crop name to yield vocabulary
        yield_crop_name = SUITABILITY_TO_YIELD_MAP.get(crop_name.lower(), crop_name)
        if yield_crop_name not in model_service.supported_crops and crop_name in model_service.supported_crops:
            yield_crop_name = crop_name

        # 1. Yield prediction
        yield_res = model_service.predict_yield(
            state=profile.state,
            district=profile.district,
            crop=yield_crop_name,
            season=profile.season,
            year=2024,
            area=profile.area_ha
        )
        predicted_yield = yield_res.predicted_yield_tonnes_per_ha

        # 2. Production calculations
        # Estimated production (tonnes) = yield (tonnes/ha) * area (ha)
        gross_prod_tonnes = round(predicted_yield * profile.area_ha, 2)
        # 1 tonne = 10 quintals
        gross_prod_quintals = round(gross_prod_tonnes * 10.0, 2)

        # 3. Post-harvest loss
        loss_profile = POST_HARVEST_LOSS_PROFILES.get(yield_crop_name, POST_HARVEST_LOSS_PROFILES.get("Default"))
        loss_pct = float(loss_profile["total"])
        loss_stages = {k: round(float(v), 2) for k, v in loss_profile["stages"].items()}

        # Marketable quintals after deducting physical loss
        marketable_quintals = round(gross_prod_quintals * (1.0 - (loss_pct / 100.0)), 2)

        # 4. Market Price
        mandi_res = mandi_service.get_mandi_analysis(
            crop=yield_crop_name,
            state=profile.state,
            user_price_override=profile.user_price_override
        )
        applicable_price = mandi_res.selected_price_quintal
        price_source = mandi_res.price_source

        # 5. Financial Arithmetic
        # Gross revenue = Marketable quintals * price per quintal
        gross_revenue = round(marketable_quintals * applicable_price, 2)

        # Cultivation cost
        cult_rate = CULTIVATION_COST_PER_HA.get(yield_crop_name, CULTIVATION_COST_PER_HA.get("Default", 30000.0))
        cultivation_cost = round(cult_rate * profile.area_ha, 2)

        # Transport cost
        transport_cost = round(marketable_quintals * TRANSPORT_COST_PER_QUINTAL, 2)

        # Storage cost (0 if sold at harvest; Rs. 45/qtl/mo if held)
        storage_cost = round(marketable_quintals * profile.storage_months * STORAGE_COST_PER_QUINTAL_MONTH, 2)

        # Packaging cost
        packaging_cost = round(marketable_quintals * PACKAGING_COST_PER_QUINTAL, 2)

        # Total costs
        total_costs = round(cultivation_cost + transport_cost + storage_cost + packaging_cost, 2)

        # Net Return = Gross Revenue - Total Costs
        net_return = round(gross_revenue - total_costs, 2)
        net_return_per_ha = round(net_return / profile.area_ha, 2)

        # ROI percentage
        roi = round((net_return / total_costs) * 100.0, 1) if total_costs > 0 else 0.0

        # Feasibility annotations
        feasibility_notes = []
        if yield_res.validation_message:
            feasibility_notes.append(yield_res.validation_message)
        if profile.rainfall < 400 and yield_crop_name in ["Rice", "Sugarcane"]:
            feasibility_notes.append(f"High irrigation required: local rainfall ({profile.rainfall}mm) is well below optimum for {yield_crop_name}.")
        if profile.ph < 5.5 or profile.ph > 8.5:
            feasibility_notes.append(f"Soil pH ({profile.ph}) is outside ideal range (6.0-7.5); soil conditioning advised.")
        if profile.storage_months > 0:
            feasibility_notes.append(f"Storage held for {profile.storage_months} months: storage cost is Rs. {storage_cost} (Rs. 45/qtl/month).")

        return CropPlan(
            crop=yield_crop_name,
            suitable=is_suitable,
            suitability_rank=suitability_rank,
            predicted_yield_tonnes_per_ha=predicted_yield,
            cultivated_area_ha=profile.area_ha,
            gross_production_tonnes=gross_prod_tonnes,
            gross_production_quintals=gross_prod_quintals,
            loss_stage_breakdown=loss_stages,
            total_loss_percentage=loss_pct,
            marketable_production_quintals=marketable_quintals,
            applicable_price_per_quintal=applicable_price,
            price_source=price_source,
            gross_revenue_rs=gross_revenue,
            cultivation_cost_rs=cultivation_cost,
            transport_cost_rs=transport_cost,
            storage_cost_rs=storage_cost,
            packaging_cost_rs=packaging_cost,
            total_costs_rs=total_costs,
            net_return_rs=net_return,
            net_return_per_ha_rs=net_return_per_ha,
            roi_percentage=roi,
            feasibility_notes=feasibility_notes
        )

    @staticmethod
    def generate_full_plan(profile: FarmProfile) -> PlanResponse:
        """
        Orchestrates full end-to-end planning flow:
        Farm Profile -> Crop Suitability SVM -> Top candidates -> Yield RF -> Production -> Losses -> Costs -> Net Return.
        """
        # Step 1: Run Crop Suitability SVM
        suitability_res = model_service.predict_crop_suitability(
            N=profile.N,
            P=profile.P,
            K=profile.K,
            temperature=profile.temperature,
            humidity=profile.humidity,
            ph=profile.ph,
            rainfall=profile.rainfall
        )

        top_crop = suitability_res.recommended_crop
        primary_plan = PlanningEngine.generate_crop_plan(
            crop_name=top_crop,
            profile=profile,
            suitability_rank=1,
            is_suitable=True
        )

        # Generate plans for alternative candidate crops
        alternative_plans: List[CropPlan] = []
        for rank, cand in enumerate(suitability_res.candidate_ranking[1:4], start=2):
            plan = PlanningEngine.generate_crop_plan(
                crop_name=cand.crop,
                profile=profile,
                suitability_rank=rank,
                is_suitable=True
            )
            alternative_plans.append(plan)

        # Document exact formulas and assumptions for transparent review
        formulas = {
            "Estimated Production (Tonnes)": "Yield (tonnes/hectare) × Cultivated Area (hectares)",
            "Quintals Conversion": "Production (Tonnes) × 10 (1 tonne = 10 quintals)",
            "Marketable Production (Quintals)": "Gross Quintals × (1 - Total Post-Harvest Loss % / 100)",
            "Gross Revenue (Rs.)": "Marketable Production (Quintals) × Mandi Price per Quintal (Rs.)",
            "Total Costs (Rs.)": "Cultivation Cost (Rs./ha × Area) + Transport (Rs. 35/qtl) + Storage (Rs. 45/qtl/mo × months) + Packaging (Rs. 20/qtl)",
            "Net Return (Rs.)": "Gross Revenue - Total Costs",
            "ROI (%)": "(Net Return / Total Costs) × 100",
            "Data Sources": "Suitability: SVM (79.9% acc); Yield: Random Forest (2.10 MAE); Losses: ICAR-CIPHET 2022 survey; Prices: AGMARKNET historical median & MSP reference."
        }

        return PlanResponse(
            primary_crop=primary_plan.crop,
            selected_plan=primary_plan,
            alternative_plans=alternative_plans,
            formulas_and_assumptions=formulas
        )

    @staticmethod
    def simulate_what_if(req: WhatIfRequest) -> WhatIfResponse:
        """
        Evaluates dynamic what-if adjustments to prices, yield shocks, area, or storage duration.
        """
        base = req.base_plan
        area = req.area_override if req.area_override is not None else base.cultivated_area_ha

        # Apply yield shock
        sim_yield = max(0.1, round(base.predicted_yield_tonnes_per_ha * (1.0 + (req.yield_shock_pct / 100.0)), 2))
        sim_prod_t = round(sim_yield * area, 2)
        sim_prod_q = round(sim_prod_t * 10.0, 2)

        # Apply loss
        sim_marketable_q = round(sim_prod_q * (1.0 - (base.total_loss_percentage / 100.0)), 2)

        # Apply price change
        sim_price = max(100.0, round(base.applicable_price_per_quintal * (1.0 + (req.price_change_pct / 100.0)), 2))
        sim_revenue = round(sim_marketable_q * sim_price, 2)

        # Costs
        cult_rate = CULTIVATION_COST_PER_HA.get(base.crop, CULTIVATION_COST_PER_HA.get("Default", 30000.0))
        sim_cult_cost = round(cult_rate * area, 2)
        sim_trans_cost = round(sim_marketable_q * TRANSPORT_COST_PER_QUINTAL, 2)
        sim_storage_cost = round(sim_marketable_q * req.storage_months * STORAGE_COST_PER_QUINTAL_MONTH, 2)
        sim_pack_cost = round(sim_marketable_q * PACKAGING_COST_PER_QUINTAL, 2)
        sim_total_costs = round(sim_cult_cost + sim_trans_cost + sim_storage_cost + sim_pack_cost, 2)

        # Net Return
        sim_net_return = round(sim_revenue - sim_total_costs, 2)
        diff_net = round(sim_net_return - base.net_return_rs, 2)
        sim_roi = round((sim_net_return / sim_total_costs) * 100.0, 1) if sim_total_costs > 0 else 0.0

        # Build simulated plan
        sim_plan = CropPlan(
            crop=base.crop,
            suitable=base.suitable,
            suitability_rank=base.suitability_rank,
            predicted_yield_tonnes_per_ha=sim_yield,
            cultivated_area_ha=area,
            gross_production_tonnes=sim_prod_t,
            gross_production_quintals=sim_prod_q,
            loss_stage_breakdown=base.loss_stage_breakdown,
            total_loss_percentage=base.total_loss_percentage,
            marketable_production_quintals=sim_marketable_q,
            applicable_price_per_quintal=sim_price,
            price_source=f"What-If Simulated Price ({req.price_change_pct:+.1f}%)",
            gross_revenue_rs=sim_revenue,
            cultivation_cost_rs=sim_cult_cost,
            transport_cost_rs=sim_trans_cost,
            storage_cost_rs=sim_storage_cost,
            packaging_cost_rs=sim_pack_cost,
            total_costs_rs=sim_total_costs,
            net_return_rs=sim_net_return,
            net_return_per_ha_rs=round(sim_net_return / area, 2),
            roi_percentage=sim_roi,
            feasibility_notes=[
                f"Simulated price: Rs. {sim_price}/qtl ({req.price_change_pct:+.1f}%)",
                f"Simulated yield: {sim_yield} t/ha ({req.yield_shock_pct:+.1f}%)",
                f"Storage duration: {req.storage_months} months (Storage cost: Rs. {sim_storage_cost})"
            ]
        )

        desc = f"Price {req.price_change_pct:+.1f}%, Yield {req.yield_shock_pct:+.1f}%, Storage {req.storage_months}mo"

        return WhatIfResponse(
            crop=base.crop,
            scenario_description=desc,
            original_yield_t_ha=base.predicted_yield_tonnes_per_ha,
            simulated_yield_t_ha=sim_yield,
            original_marketable_quintals=base.marketable_production_quintals,
            simulated_marketable_quintals=sim_marketable_q,
            original_price_quintal=base.applicable_price_per_quintal,
            simulated_price_quintal=sim_price,
            original_gross_revenue=base.gross_revenue_rs,
            simulated_gross_revenue=sim_revenue,
            original_total_costs=base.total_costs_rs,
            simulated_total_costs=sim_total_costs,
            original_net_return=base.net_return_rs,
            simulated_net_return=sim_net_return,
            diff_net_return=diff_net,
            roi_percentage=sim_roi,
            simulated_plan=sim_plan
        )

planning_engine = PlanningEngine()
