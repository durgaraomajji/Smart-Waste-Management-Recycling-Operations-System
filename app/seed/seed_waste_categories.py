from sqlalchemy.orm import Session

from app.enums import RecyclabilityStatus as R
from app.models import SegregationRule, WasteCategory

CATEGORIES = [
    ("Organic Waste", "ORG", "Biodegradable", R.PARTIALLY_RECYCLABLE, False, "Compost or send to biogas plant.", "Green", "Keep food and garden waste separate from dry waste."),
    ("Plastic Waste", "PLS", "Dry", R.RECYCLABLE, False, "Rinse, sort by resin code and send to a plastics recycler.", "Blue", "Rinse containers; remove caps and labels where possible."),
    ("Paper Waste", "PPR", "Dry", R.RECYCLABLE, False, "Bale and send to a paper mill.", "Blue", "Keep paper dry and free of food residue."),
    ("Metal Waste", "MTL", "Dry", R.RECYCLABLE, False, "Sort ferrous / non-ferrous and send to a smelter.", "Blue", "Flatten cans; keep sharp scrap wrapped."),
    ("Glass Waste", "GLS", "Dry", R.RECYCLABLE, False, "Sort by colour and send to a glass recycler.", "Blue", "Never mix broken glass with other waste; wrap shards."),
    ("Electronic Waste", "EWS", "E-waste", R.PARTIALLY_RECYCLABLE, True, "Dismantle at an authorised e-waste facility.", "Red", "Do not break devices open; remove batteries."),
    ("Hazardous Waste", "HAZ", "Hazardous", R.HAZARDOUS, True, "Treat only at licensed hazardous-waste facilities.", "Black", "Use sealed, labelled containers; never mix with other waste."),
]


def seed_waste_categories(db: Session) -> int:
    created = 0
    for name, code, cls, rec, hazardous, disposal, colour, rule in CATEGORIES:
        if db.query(WasteCategory).filter_by(code=code).first():
            continue
        cat = WasteCategory(name=name, code=code, classification=cls, recyclability=rec, is_hazardous=hazardous, disposal_instructions=disposal)
        db.add(cat)
        db.flush()
        db.add(SegregationRule(waste_category_id=cat.id, title=f"{name} segregation", description=rule, container_color=colour))
        created += 1
    db.commit()
    return created
