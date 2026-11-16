import logging
from functools import lru_cache
import pandas as pd
from app.core.config import DATASETS_DIR
from typing import Dict, List, Any, Optional

from app.schemas.plan import FarmProfile, CropPlan, PlanResponse
from app.schemas.what_if import WhatIfRequest, WhatIfResponse
from app.services.model_service import model_service, SUITABILITY_TO_YIELD_MAP
from app.services.mandi_service import mandi_service
from app.services.loss_service import model_loss

logger = logging.getLogger(__name__)

@lru_cache(maxsize=1)
def recorded_crop_seasons():
    """Supported state/crop/season combinations in the project's yield source."""
    records = pd.read_csv(DATASETS_DIR / "Yeild" / "crop_production_haryana_punjab_1997_2019.csv")
    valid = (pd.to_numeric(records["Area"], errors="coerce") > 0) & (pd.to_numeric(records["Yield"], errors="coerce") > 0)
    records = records.loc[valid, ["State", "Crop", "Season"]].dropna()
    return frozenset(tuple(str(value).strip().lower() for value in row)
                     for row in records.itertuples(index=False, name=None))


@lru_cache(maxsize=1)
def recorded_field_locations():
    records = pd.read_csv(DATASETS_DIR / "Yeild" / "crop_production_haryana_punjab_1997_2019.csv", usecols=["State", "District"])
    return frozenset((str(state).strip().lower(), str(district).strip().upper())
                     for state, district in records.dropna().itertuples(index=False, name=None))


@lru_cache(maxsize=1)
def published_loss_data():
    data = pd.read_csv(DATASETS_DIR / "Food Loss" / "post_harvest_loss_2022_state_stage.csv")
    data["loss_percentage"] = pd.to_numeric(data["loss_percentage"], errors="coerce")
    return data[data.loss_percentage.between(0, 100)].copy()


def dataset_loss(crop, state):
    aliases = {"Rice": "Paddy", "Gram": "Chickpea", "Arhar/Tur": "Pigeon Pea",
        "Moong(Green Gram)": "Green gram", "Urad": "Black gram", "Cotton(lint)": "Cottonseed",
        "Rapeseed &Mustard": "Mustard", "Soyabean": "Soybean", "Peas & beans (Pulses)": "Green Pea"}
    data = published_loss_data()
    data = data[~data.crop.str.contains("fish|meat|milk|poultry|egg", case=False, regex=True)]
    crop_rows = data[data.crop.str.casefold().eq(aliases.get(crop, crop).casefold())]
    local = crop_rows[crop_rows.state.str.casefold().eq(state.casefold())]
    scope, rows = state + ", " + crop, local
    totals = rows[rows.stage.eq("Overall total loss")]
    if totals.empty:
        rows, scope = crop_rows, crop + " across available study states"
        totals = rows[rows.stage.eq("Overall total loss")]
    if totals.empty:
        rows = data
        totals = data[data.stage.eq("Overall total loss")]
        scope = "Cross-crop study median proxy; no crop-specific overall total available"
    # Overall totals already include stages. Never add subtotal records again.
    stage_rows = rows[~rows.stage.str.contains("total", case=False)]
    stages = stage_rows.groupby(["loss_type", "stage"]).loss_percentage.median()
    return float(totals.loss_percentage.median()), {f"{kind}: {stage}": round(float(value), 2)
        for (kind, stage), value in stages.items()}, "Published NABCONS study extract: " + scope + ". Stage medians are reference values, not additive totals."


class PlanningEngine:
    @staticmethod
    def generate_crop_plan(
        crop_name: str,
        profile: FarmProfile,
        suitability_rank: int = 1,
        is_suitable: bool = True,
    ) -> CropPlan:
        """
        Builds a single connected crop plan incorporating:
        Yield model -> Production -> Unit Conversions -> Losses -> Mandi Price -> Financial Statement.
        """
        # Map crop name to yield vocabulary
        yield_crop_name = SUITABILITY_TO_YIELD_MAP.get(crop_name.lower(), crop_name)
        if (
            yield_crop_name not in model_service.supported_crops
            and crop_name in model_service.supported_crops
        ):
            yield_crop_name = crop_name

        # 1. Yield prediction
        yield_res = model_service.predict_yield(
            state=profile.state,
            district=profile.district,
            crop=yield_crop_name,
            season=profile.season,
            year=2024,
            area=profile.area_ha,
        )
        predicted_yield = yield_res.predicted_yield_tonnes_per_ha

        # 2. Production calculations
        # Estimated production (tonnes) = yield (tonnes/ha) * area (ha)
        gross_prod_tonnes = round(predicted_yield * profile.area_ha, 2)
        # 1 tonne = 10 quintals
        gross_prod_quintals = round(gross_prod_tonnes * 10.0, 2)

        # 3. Post-harvest loss
        loss_pct, loss_stages, loss_source = dataset_loss(yield_crop_name, profile.state)
        if profile.loss_estimation_method == "model":
            estimate = model_loss(yield_crop_name, profile.state)
            if estimate is not None:
                loss_pct, loss_stages = estimate, {}
                loss_source = "Random Forest estimate of the published overall loss. Historical research model, not a measured farm loss."
            else:
                loss_source += " Model input unsupported; using the published reference instead."
        if profile.loss_override_pct is not None:
            loss_pct, loss_stages = profile.loss_override_pct, {}
            loss_source = "User-entered expected loss percentage."

        # Marketable quintals after deducting physical loss
        marketable_quintals = round(gross_prod_quintals * (1.0 - (loss_pct / 100.0)), 2)

        # 4. Market Price
        mandi_res = mandi_service.get_mandi_analysis(
            crop=yield_crop_name,
            state=profile.state,
            district=profile.district,
            user_price_override=profile.user_price_override,
        )
        applicable_price = mandi_res.selected_price_quintal
        price_source = mandi_res.price_source

        # 5. Financial Arithmetic
        # Gross revenue = Marketable quintals * price per quintal
        gross_revenue = round(marketable_quintals * applicable_price, 2)

        # Cultivation cost
        cult_rate = profile.cultivation_cost_per_ha
        cultivation_cost = round(cult_rate * profile.area_ha, 2)

        # Transport cost
        transport_cost = round(marketable_quintals * profile.transport_cost_per_quintal, 2)

        # Storage cost (0 if sold at harvest; entered storage rate if held)
        storage_cost = round(
            marketable_quintals
            * profile.storage_months
            * profile.storage_cost_per_quintal_month,
            2,
        )

        # Packaging cost
        packaging_cost = round(marketable_quintals * profile.packaging_cost_per_quintal, 2)

        # Total costs
        total_costs = round(
            cultivation_cost + transport_cost + storage_cost + packaging_cost, 2
        )

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
            feasibility_notes.append(
                f"High irrigation required: local rainfall ({profile.rainfall}mm) is well below optimum for {yield_crop_name}."
            )
        if profile.ph < 5.5 or profile.ph > 8.5:
            feasibility_notes.append(
                f"Soil pH ({profile.ph}) is outside ideal range (6.0-7.5); soil conditioning advised."
            )
        if profile.storage_months > 0:
            feasibility_notes.append(
                f"Storage held for {profile.storage_months} months: storage cost is Rs. {storage_cost} (user-entered rate per quintal per month)."
            )

        return CropPlan(
            crop=yield_crop_name,
            suitable=is_suitable,
            suitability_rank=suitability_rank,
            predicted_yield_tonnes_per_ha=predicted_yield,
            cultivated_area_ha=profile.area_ha,
            gross_production_tonnes=gross_prod_tonnes,
            gross_production_quintals=gross_prod_quintals,
            loss_source=loss_source,
            cultivation_cost_per_ha=profile.cultivation_cost_per_ha,
            transport_cost_per_quintal=profile.transport_cost_per_quintal,
            storage_cost_per_quintal_month=profile.storage_cost_per_quintal_month,
            packaging_cost_per_quintal=profile.packaging_cost_per_quintal,
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
            feasibility_notes=feasibility_notes,
        )

    @staticmethod
    def generate_full_plan(profile: FarmProfile) -> PlanResponse:
        """
        Orchestrates full end-to-end planning flow:
        Farm Profile -> Crop Suitability SVM -> Top candidates -> Yield RF -> Production -> Losses -> Costs -> Net Return.
        """
        # "Whole Year" is an aggregate source reporting category, not a
        # planting season. Summer cannot be inferred from those records.
        if profile.season not in {"Kharif", "Rabi"}:
            raise ValueError("Choose Kharif or Rabi for a planting plan. 'Whole Year' is a source reporting category, not a sowing season; separate summer data is not available.")
        if (profile.state.lower(), profile.district.strip().upper()) not in recorded_field_locations():
            raise ValueError("This district does not belong to the selected state in the supported dataset. Choose a supported state/district pair.")
        # Step 1: Run Crop Suitability SVM
        suitability_res = model_service.predict_crop_suitability(
            N=profile.N,
            P=profile.P,
            K=profile.K,
            temperature=profile.temperature,
            humidity=profile.humidity,
            ph=profile.ph,
            rainfall=profile.rainfall,
        )

        # Only compare crops represented in the regional yield model. An unrelated
        # crop label must not become a profitable-looking plan via a generic yield.
        aliases = {name.lower(): value for name, value in SUITABILITY_TO_YIELD_MAP.items()}
        vocabulary = {name.lower(): name for name in model_service.supported_crops}
        eligible = []
        seasonal_labels = []
        observed = recorded_crop_seasons()
        seen = set()
        for rank, candidate in enumerate(suitability_res.candidate_ranking, start=1):
            mapped = aliases.get(candidate.crop.lower(), candidate.crop)
            canonical = vocabulary.get(mapped.lower())
            # Punjab/North-West-zone guidance distinguishes summer moong
            # from winter Rabi. Do not reinterpret the source's Rabi/annual
            # labels as a validated local planting calendar.
            # Sources: pau.edu/content/ccil/pf/pp_kharif.pdf and
            # dpd.gov.in/Pulses%20in%20India-Final.pdf (Mung & Urd, NWPZ).
            if canonical == "Moong(Green Gram)" and profile.season == "Rabi":
                continue
            if canonical and canonical not in seen and (profile.state.strip().lower(), canonical.lower(), profile.season.strip().lower()) in observed:
                eligible.append((rank, canonical))
                seen.add(canonical)
                seasonal_labels.append(candidate.crop)
        if not eligible:
            raise ValueError("No ranked crops have yield records for this state and season. Review the field inputs or choose another season.")
        plans = []
        for index, (rank, crop) in enumerate(eligible[:4]):
            # The farmer's local offer is for the chosen crop, not every crop.
            crop_profile = profile if index == 0 else profile.model_copy(update={"user_price_override": None})
            plans.append(PlanningEngine.generate_crop_plan(
                crop_name=crop, profile=crop_profile, suitability_rank=rank, is_suitable=True
            ))
        primary_plan = plans[0]
        primary_plan.feasibility_notes.append(
            "The planning crop is the highest-ranked suitability candidate with recorded yield data for the selected state and season; it is not an independently verified agronomic recommendation."
        )
        alternative_plans = plans[1:]

        # Document exact formulas and assumptions for transparent review
        formulas = {
            "Estimated Production (Tonnes)": "Yield (tonnes/hectare) × Cultivated Area (hectares)",
            "Quintals Conversion": "Production (Tonnes) × 10 (1 tonne = 10 quintals)",
            "Marketable Production (Quintals)": "Gross Quintals × (1 - Total Post-Harvest Loss % / 100)",
            "Gross Revenue (Rs.)": "Marketable Production (Quintals) × Mandi Price per Quintal (Rs.)",
            "Total Costs (Rs.)": "Cultivation Cost (Rs./ha × Area) + Transport (entered transport rate) + Storage (entered storage rate × months) + Packaging (entered packaging rate)",
            "Net Return (Rs.)": "Gross Revenue - Total Costs",
            "ROI (%)": "(Net Return / Total Costs) × 100",
            "Data Sources": "Suitability: SVM (79.9% acc); Yield: Random Forest (2.10 MAE); Losses: published NABCONS extract or user override; Costs: editable user inputs; Prices: historical crop dataset or user offer.",
        }

        return PlanResponse(
            primary_crop=primary_plan.crop,
            selected_plan=primary_plan,
            alternative_plans=alternative_plans,
            seasonal_suitability_labels=seasonal_labels,
            formulas_and_assumptions=formulas,
        )

    @staticmethod
    def simulate_what_if(req: WhatIfRequest) -> WhatIfResponse:
        """
        Evaluates dynamic what-if adjustments to prices, yield shocks, area, or storage duration.
        """
        base = req.base_plan
        area = (
            req.area_override
            if req.area_override is not None
            else base.cultivated_area_ha
        )

        # Apply yield shock
        sim_yield = max(
            0.0,
            round(
                base.predicted_yield_tonnes_per_ha
                * (1.0 + (req.yield_shock_pct / 100.0)),
                2,
            ),
        )
        sim_prod_t = round(sim_yield * area, 2)
        sim_prod_q = round(sim_prod_t * 10.0, 2)

        # Apply loss
        sim_marketable_q = round(
            sim_prod_q * (1.0 - (base.total_loss_percentage / 100.0)), 2
        )

        # Apply price change
        sim_price = max(
            0.0,
            round(
                base.applicable_price_per_quintal
                * (1.0 + (req.price_change_pct / 100.0)),
                2,
            ),
        )
        sim_revenue = round(sim_marketable_q * sim_price, 2)

        # Costs
        cult_rate = base.cultivation_cost_per_ha
        sim_cult_cost = round(cult_rate * area, 2)
        sim_trans_cost = round(sim_marketable_q * base.transport_cost_per_quintal, 2)
        sim_storage_cost = round(
            sim_marketable_q * req.storage_months * base.storage_cost_per_quintal_month, 2
        )
        sim_pack_cost = round(sim_marketable_q * base.packaging_cost_per_quintal, 2)
        sim_total_costs = round(
            sim_cult_cost + sim_trans_cost + sim_storage_cost + sim_pack_cost, 2
        )

        # Net Return
        sim_net_return = round(sim_revenue - sim_total_costs, 2)
        diff_net = round(sim_net_return - base.net_return_rs, 2)
        sim_roi = (
            round((sim_net_return / sim_total_costs) * 100.0, 1)
            if sim_total_costs > 0
            else 0.0
        )

        # Build simulated plan
        sim_plan = CropPlan(
            crop=base.crop,
            suitable=base.suitable,
            suitability_rank=base.suitability_rank,
            predicted_yield_tonnes_per_ha=sim_yield,
            cultivated_area_ha=area,
            gross_production_tonnes=sim_prod_t,
            gross_production_quintals=sim_prod_q,
            loss_source=base.loss_source,
            cultivation_cost_per_ha=base.cultivation_cost_per_ha,
            transport_cost_per_quintal=base.transport_cost_per_quintal,
            storage_cost_per_quintal_month=base.storage_cost_per_quintal_month,
            packaging_cost_per_quintal=base.packaging_cost_per_quintal,
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
                f"Storage duration: {req.storage_months} months (Storage cost: Rs. {sim_storage_cost})",
            ],
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
            simulated_plan=sim_plan,
        )


planning_engine = PlanningEngine()
