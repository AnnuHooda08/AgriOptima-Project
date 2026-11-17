import logging
from functools import lru_cache
import pandas as pd
from app.core.config import DATASETS_DIR
from typing import Dict, List, Any, Optional

from app.schemas.plan import FarmProfile, CropPlan, PlanResponse
from app.services.model_service import model_service, SUITABILITY_TO_YIELD_MAP
from app.services.mandi_service import mandi_service
from app.services.loss_service import model_loss

logger = logging.getLogger(__name__)

@lru_cache(maxsize=1)
def recorded_crop_seasons():
    """Supported state/crop/season combinations in the project's yield source."""
    records = pd.read_csv(DATASETS_DIR / "Yield" / "crop_production_haryana_punjab_1997_2019.csv")
    valid = (pd.to_numeric(records["Area"], errors="coerce") > 0) & (pd.to_numeric(records["Yield"], errors="coerce") > 0)
    records = records.loc[valid, ["State", "Crop", "Season"]].dropna()
    return frozenset(tuple(str(value).strip().lower() for value in row)
                     for row in records.itertuples(index=False, name=None))


@lru_cache(maxsize=1)
def recorded_field_locations():
    records = pd.read_csv(DATASETS_DIR / "Yield" / "crop_production_haryana_punjab_1997_2019.csv", usecols=["State", "District"])
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
        # Missing market coverage must not block crop and yield predictions.
        try:
            mandi_res = mandi_service.get_mandi_analysis(
                crop=yield_crop_name, state=profile.state, district=profile.district,
                user_price_override=profile.user_price_override,
            )
            applicable_price = mandi_res.selected_price_quintal
            price_source = mandi_res.price_source
        except ValueError:
            applicable_price = None
            price_source = 'Market price unavailable for this crop. Revenue and net return cannot be calculated.'

        # 5. Financial Arithmetic
        # Gross revenue = Marketable quintals * price per quintal
        gross_revenue = round(marketable_quintals * applicable_price, 2) if applicable_price is not None else None

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
        net_return = round(gross_revenue - total_costs, 2) if gross_revenue is not None else None
        net_return_per_ha = round(net_return / profile.area_ha, 2) if net_return is not None else None

        # ROI percentage
        roi = (round((net_return / total_costs) * 100.0, 1) if total_costs > 0 else 0.0) if net_return is not None else None

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



planning_engine = PlanningEngine()
