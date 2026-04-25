"""Curated product, inventory, and recipe seed data for the demo POS baseline."""

from __future__ import annotations


BUSINESS_UNITS = (
    {
        "code": "gourmand",
        "name": "Gourmand Sutohaz es Kezmuves Cukraszat",
        "type": "bakery",
        "is_active": True,
    },
    {
        "code": "flow",
        "name": "Flow Music Club",
        "type": "music_club",
        "is_active": True,
    },
)

INGREDIENT_UNIT_COSTS = {
    "Liszt": "420",
    "Vaj": "2600",
    "Eleszto": "2200",
    "Tej": "390",
    "Tojas": "80",
    "So": "220",
    "Sajt": "2800",
    "Teperto": "2600",
    "Kaposzta": "450",
    "Olaj": "850",
    "Bacon": "3600",
    "Virsli": "220",
    "Napraforgomag": "1600",
    "Szezammag": "2400",
    "Leveles teszta": "1500",
    "Sonka": "3200",
    "Piskota": "1800",
    "Fondant": "1900",
    "Lekvar": "1400",
    "Csoki": "3200",
    "Dio": "4500",
    "Rum aroma": "3200",
    "Cukor": "420",
    "Csokiontet": "1800",
    "Kokusz": "1800",
    "Alma": "520",
    "Tejszin": "1600",
    "Vajkrem": "2200",
    "Karamell": "1800",
    "Eper": "1800",
    "Vanilia rud": "650",
    "Aroma": "2800",
    "Citrom": "120",
    "Viz": "30",
    "Kavebab": "7200",
    "Tortadoboz": "260",
}

UNITS_OF_MEASURE = (
    {"code": "pcs", "name": "Piece", "symbol": "pcs"},
    {"code": "kg", "name": "Kilogram", "symbol": "kg"},
    {"code": "g", "name": "Gram", "symbol": "g"},
    {"code": "l", "name": "Litre", "symbol": "l"},
    {"code": "ml", "name": "Millilitre", "symbol": "ml"},
    {"code": "portion", "name": "Portion", "symbol": "adag"},
    {"code": "scoop", "name": "Ice cream scoop", "symbol": "gomboc"},
)

LOCATIONS = (
    {
        "business_unit_code": "gourmand",
        "name": "Gourmand fo hely",
        "kind": "store",
        "is_active": True,
    },
    {
        "business_unit_code": "flow",
        "name": "Flow venue",
        "kind": "venue",
        "is_active": True,
    },
)

CATEGORIES = (
    {"business_unit_code": "gourmand", "name": "Sos sutemenyek"},
    {"business_unit_code": "gourmand", "name": "Edes sutemenyek"},
    {"business_unit_code": "gourmand", "name": "Tortak"},
    {"business_unit_code": "gourmand", "name": "Fagylaltok"},
    {"business_unit_code": "gourmand", "name": "Kavek"},
    {"business_unit_code": "gourmand", "name": "Uditok"},
    {"business_unit_code": "flow", "name": "Uditok"},
    {"business_unit_code": "flow", "name": "Sorok"},
    {"business_unit_code": "flow", "name": "Roviditalok"},
    {"business_unit_code": "flow", "name": "Long drinkek"},
    {"business_unit_code": "flow", "name": "Jegyek"},
)

GOURMAND_PRODUCTS = (
    ("G-SOS-001", "Sajtos pogacsa", "Sos sutemenyek", "finished_good", "180", None),
    ("G-SOS-002", "Sajtos rud", "Sos sutemenyek", "finished_good", "150", None),
    ("G-SOS-003", "Tepertos pogacsa", "Sos sutemenyek", "finished_good", "220", None),
    ("G-SOS-004", "Kaposztas pogacsa", "Sos sutemenyek", "finished_good", "200", None),
    ("G-SOS-005", "Baconos-sajtos csiga", "Sos sutemenyek", "finished_good", "300", None),
    ("G-SOS-006", "Virslis kifli", "Sos sutemenyek", "finished_good", "350", None),
    ("G-SOS-007", "Sos perec", "Sos sutemenyek", "finished_good", "250", None),
    ("G-SOS-008", "Magvas rud", "Sos sutemenyek", "finished_good", "200", None),
    ("G-SOS-009", "Sajtos taller", "Sos sutemenyek", "finished_good", "220", None),
    ("G-SOS-010", "Sonkas-sajtos haromszog", "Sos sutemenyek", "finished_good", "400", None),
    ("G-EDES-001", "Mignon", "Edes sutemenyek", "finished_good", "320", None),
    ("G-EDES-002", "Isler", "Edes sutemenyek", "finished_good", "350", None),
    ("G-EDES-003", "Zserbo szelet", "Edes sutemenyek", "finished_good", "450", None),
    ("G-EDES-004", "Puncs szelet", "Edes sutemenyek", "finished_good", "400", None),
    ("G-EDES-005", "Kremes", "Edes sutemenyek", "finished_good", "500", None),
    ("G-EDES-006", "Somloi galuska", "Edes sutemenyek", "finished_good", "600", None),
    ("G-EDES-007", "Kokuszkocka", "Edes sutemenyek", "finished_good", "300", None),
    ("G-EDES-008", "Almas pite", "Edes sutemenyek", "finished_good", "350", None),
    ("G-EDES-009", "Rigo Jancsi", "Edes sutemenyek", "finished_good", "550", None),
    ("G-EDES-010", "Dobos szelet", "Edes sutemenyek", "finished_good", "500", None),
    ("G-TORTA-001", "Dobostorta", "Tortak", "finished_good", "8500", None),
    ("G-TORTA-002", "Csokitorta", "Tortak", "finished_good", "9000", None),
    ("G-TORTA-003", "Epertorta", "Tortak", "finished_good", "9500", None),
    ("G-TORTA-004", "Oroszkrem torta", "Tortak", "finished_good", "8000", None),
    ("G-TORTA-005", "Sacher torta", "Tortak", "finished_good", "9000", None),
    ("G-FAGYI-001", "Csoki fagyi", "Fagylaltok", "finished_good", "500", None),
    ("G-FAGYI-002", "Vanilia fagyi", "Fagylaltok", "finished_good", "500", None),
    ("G-FAGYI-003", "Eper fagyi", "Fagylaltok", "finished_good", "550", None),
    ("G-FAGYI-004", "Puncs fagyi", "Fagylaltok", "finished_good", "500", None),
    ("G-FAGYI-005", "Citrom fagyi", "Fagylaltok", "finished_good", "500", None),
    ("G-KAVE-001", "Eszpresszo", "Kavek", "beverage", "450", None),
    ("G-KAVE-002", "Hosszukave", "Kavek", "beverage", "500", None),
    ("G-KAVE-003", "Cappuccino", "Kavek", "beverage", "650", None),
    ("G-KAVE-004", "Latte", "Kavek", "beverage", "750", None),
    ("G-KAVE-005", "Jeges kave", "Kavek", "beverage", "900", None),
)

SOFT_DRINKS = (
    ("Coca-Cola 0,5L", "300", "650", "900"),
    ("Coca-Cola Zero 0,5L", "300", "650", "900"),
    ("Fanta Narancs 0,5L", "300", "650", "900"),
    ("Sprite 0,5L", "300", "650", "900"),
    ("Kinley Tonic 0,5L", "350", "700", "950"),
    ("Nestea Citrom 0,5L", "350", "700", "950"),
    ("Cappy Narancsle 0,33L", "400", "750", "950"),
    ("Cappy Alma 0,33L", "400", "750", "950"),
    ("Asvanyviz szensavas 0,5L", "200", "450", "700"),
    ("Asvanyviz mentes 0,5L", "200", "450", "700"),
)

FLOW_PRODUCTS = (
    ("F-SOR-001", "Heineken 0,5L", "Sorok", "beverage", "1200", "600"),
    ("F-SOR-002", "Dreher 0,5L", "Sorok", "beverage", "900", "450"),
    ("F-SOR-003", "Borsodi 0,5L", "Sorok", "beverage", "850", "400"),
    ("F-ROVID-001", "Finlandia Vodka", "Roviditalok", "beverage", "1500", "200"),
    ("F-ROVID-002", "Jack Daniel's Whiskey", "Roviditalok", "beverage", "1800", "250"),
    ("F-ROVID-003", "Jagermeister", "Roviditalok", "beverage", "1400", "225"),
    ("F-ROVID-004", "Tequila Silver", "Roviditalok", "beverage", "1600", "240"),
    ("F-LONG-001", "Vodka szoda", "Long drinkek", "beverage", "1800", "300"),
    ("F-LONG-002", "Whiskey cola", "Long drinkek", "beverage", "2000", "350"),
    ("F-LONG-003", "Gin tonic", "Long drinkek", "beverage", "2000", "350"),
    ("F-LONG-004", "Jager-narancs", "Long drinkek", "beverage", "1800", "300"),
    ("F-JEGY-001", "Normal belepo", "Jegyek", "ticket", "3000", "0"),
    ("F-JEGY-002", "VIP belepo", "Jegyek", "ticket", "8000", "500"),
    ("F-JEGY-003", "Early bird jegy", "Jegyek", "ticket", "2000", "0"),
    ("F-JEGY-004", "Paros jegy", "Jegyek", "ticket", "5000", "0"),
)

PRODUCTS = tuple(
    {
        "business_unit_code": "gourmand",
        "sku": sku,
        "name": name,
        "category_name": category,
        "product_type": product_type,
        "sale_price_gross": sale_price,
        "default_unit_cost": unit_cost,
        "sales_uom_code": "scoop" if sku.startswith("G-FAGYI") else "portion" if sku == "G-EDES-006" else "pcs",
    }
    for sku, name, category, product_type, sale_price, unit_cost in GOURMAND_PRODUCTS
) + tuple(
    {
        "business_unit_code": "gourmand",
        "sku": f"G-UDITO-{index:03d}",
        "name": name,
        "category_name": "Uditok",
        "product_type": "beverage",
        "sale_price_gross": gourmand_sale_price,
        "default_unit_cost": unit_cost,
        "sales_uom_code": "pcs",
    }
    for index, (name, unit_cost, gourmand_sale_price, _flow_sale_price) in enumerate(
        SOFT_DRINKS,
        start=1,
    )
) + tuple(
    {
        "business_unit_code": "flow",
        "sku": f"F-UDITO-{index:03d}",
        "name": name,
        "category_name": "Uditok",
        "product_type": "beverage",
        "sale_price_gross": flow_sale_price,
        "default_unit_cost": unit_cost,
        "sales_uom_code": "pcs",
    }
    for index, (name, unit_cost, _gourmand_sale_price, flow_sale_price) in enumerate(
        SOFT_DRINKS,
        start=1,
    )
) + tuple(
    {
        "business_unit_code": "flow",
        "sku": sku,
        "name": name,
        "category_name": category,
        "product_type": product_type,
        "sale_price_gross": sale_price,
        "default_unit_cost": unit_cost,
        "sales_uom_code": "pcs",
    }
    for sku, name, category, product_type, sale_price, unit_cost in FLOW_PRODUCTS
)

GOURMAND_INGREDIENTS = (
    ("Liszt", "raw_material", "kg", True),
    ("Vaj", "raw_material", "kg", True),
    ("Eleszto", "raw_material", "kg", True),
    ("Tej", "raw_material", "l", True),
    ("Tojas", "raw_material", "pcs", True),
    ("So", "raw_material", "kg", True),
    ("Sajt", "raw_material", "kg", True),
    ("Teperto", "raw_material", "kg", True),
    ("Kaposzta", "raw_material", "kg", True),
    ("Olaj", "raw_material", "l", True),
    ("Bacon", "raw_material", "kg", True),
    ("Virsli", "raw_material", "pcs", True),
    ("Napraforgomag", "raw_material", "kg", True),
    ("Szezammag", "raw_material", "kg", True),
    ("Leveles teszta", "raw_material", "kg", True),
    ("Sonka", "raw_material", "kg", True),
    ("Piskota", "semi_finished", "kg", True),
    ("Fondant", "raw_material", "kg", True),
    ("Lekvar", "raw_material", "kg", True),
    ("Csoki", "raw_material", "kg", True),
    ("Dio", "raw_material", "kg", True),
    ("Rum aroma", "raw_material", "l", True),
    ("Cukor", "raw_material", "kg", True),
    ("Csokiontet", "raw_material", "l", True),
    ("Kokusz", "raw_material", "kg", True),
    ("Alma", "raw_material", "kg", True),
    ("Tejszin", "raw_material", "l", True),
    ("Vajkrem", "raw_material", "kg", True),
    ("Karamell", "raw_material", "kg", True),
    ("Eper", "raw_material", "kg", True),
    ("Vanilia rud", "raw_material", "pcs", True),
    ("Aroma", "raw_material", "l", True),
    ("Citrom", "raw_material", "pcs", True),
    ("Viz", "raw_material", "l", True),
    ("Kavebab", "raw_material", "kg", True),
    ("Tortadoboz", "packaging", "pcs", True),
) + tuple((name, "finished_good", "pcs", True) for name, *_ in SOFT_DRINKS)

FLOW_INVENTORY = tuple((name, "finished_good", "pcs", True) for name, *_ in SOFT_DRINKS) + (
    ("Heineken 0,5L", "finished_good", "pcs", True),
    ("Dreher 0,5L", "finished_good", "pcs", True),
    ("Borsodi 0,5L", "finished_good", "pcs", True),
    ("Finlandia Vodka", "finished_good", "l", True),
    ("Jack Daniel's Whiskey", "finished_good", "l", True),
    ("Jagermeister", "finished_good", "l", True),
    ("Tequila Silver", "finished_good", "l", True),
    ("Vodka szoda", "finished_good", "pcs", False),
    ("Whiskey cola", "finished_good", "pcs", False),
    ("Gin tonic", "finished_good", "pcs", False),
    ("Jager-narancs", "finished_good", "pcs", False),
    ("Normal belepo", "service", "pcs", False),
    ("VIP belepo", "service", "pcs", False),
    ("Early bird jegy", "service", "pcs", False),
    ("Paros jegy", "service", "pcs", False),
    ("Muanyag pohar", "packaging", "pcs", True),
)

INVENTORY_ITEMS = tuple(
    {
        "business_unit_code": "gourmand",
        "name": name,
        "item_type": item_type,
        "uom_code": uom_code,
        "track_stock": track_stock,
        "default_unit_cost": INGREDIENT_UNIT_COSTS.get(name, unit_cost if (unit_cost := next((cost for drink_name, cost, *_ in SOFT_DRINKS if drink_name == name), None)) else None),
        "estimated_stock_quantity": None,
        "is_active": True,
    }
    for name, item_type, uom_code, track_stock in GOURMAND_INGREDIENTS
) + tuple(
    {
        "business_unit_code": "flow",
        "name": name,
        "item_type": item_type,
        "uom_code": uom_code,
        "track_stock": track_stock,
        "default_unit_cost": next((cost for drink_name, cost, *_ in SOFT_DRINKS if drink_name == name), None),
        "estimated_stock_quantity": None,
        "is_active": True,
    }
    for name, item_type, uom_code, track_stock in FLOW_INVENTORY
)

RECIPES = (
    {
        "sku": "G-SOS-001",
        "yield_quantity": "100",
        "yield_uom_code": "pcs",
        "ingredients": (("Liszt", "1", "kg"), ("Vaj", "0.4", "kg"), ("Eleszto", "0.05", "kg"), ("Tej", "0.3", "l"), ("Tojas", "3", "pcs"), ("So", "0.02", "kg"), ("Sajt", "0.2", "kg")),
    },
    {
        "sku": "G-SOS-002",
        "yield_quantity": "120",
        "yield_uom_code": "pcs",
        "ingredients": (("Liszt", "1", "kg"), ("Vaj", "0.3", "kg"), ("Tojas", "2", "pcs"), ("So", "0.02", "kg"), ("Sajt", "0.25", "kg")),
    },
    {
        "sku": "G-SOS-003",
        "yield_quantity": "90",
        "yield_uom_code": "pcs",
        "ingredients": (("Liszt", "1", "kg"), ("Teperto", "0.4", "kg"), ("Tej", "0.2", "l"), ("Eleszto", "0.05", "kg"), ("So", "0.02", "kg")),
    },
    {
        "sku": "G-SOS-004",
        "yield_quantity": "100",
        "yield_uom_code": "pcs",
        "ingredients": (("Liszt", "1", "kg"), ("Kaposzta", "0.5", "kg"), ("Olaj", "0.1", "l"), ("So", "0.02", "kg")),
    },
    {
        "sku": "G-SOS-005",
        "yield_quantity": "60",
        "yield_uom_code": "pcs",
        "ingredients": (("Liszt", "1", "kg"), ("Eleszto", "0.05", "kg"), ("Tej", "0.3", "l"), ("Bacon", "0.3", "kg"), ("Sajt", "0.3", "kg")),
    },
    {
        "sku": "G-SOS-006",
        "yield_quantity": "40",
        "yield_uom_code": "pcs",
        "ingredients": (("Liszt", "1", "kg"), ("Virsli", "10", "pcs"), ("Eleszto", "0.05", "kg"), ("Tej", "0.3", "l")),
    },
    {
        "sku": "G-SOS-007",
        "yield_quantity": "50",
        "yield_uom_code": "pcs",
        "ingredients": (("Liszt", "1", "kg"), ("Vaj", "0.2", "kg"), ("So", "0.03", "kg"), ("Tojas", "2", "pcs")),
    },
    {
        "sku": "G-SOS-008",
        "yield_quantity": "100",
        "yield_uom_code": "pcs",
        "ingredients": (("Liszt", "1", "kg"), ("Napraforgomag", "0.2", "kg"), ("Szezammag", "0.1", "kg"), ("Olaj", "0.1", "l")),
    },
    {
        "sku": "G-SOS-009",
        "yield_quantity": "80",
        "yield_uom_code": "pcs",
        "ingredients": (("Liszt", "1", "kg"), ("Sajt", "0.4", "kg"), ("Vaj", "0.3", "kg")),
    },
    {
        "sku": "G-SOS-010",
        "yield_quantity": "30",
        "yield_uom_code": "pcs",
        "ingredients": (("Leveles teszta", "1", "kg"), ("Sonka", "0.3", "kg"), ("Sajt", "0.3", "kg")),
    },
    {
        "sku": "G-EDES-001",
        "yield_quantity": "80",
        "yield_uom_code": "pcs",
        "ingredients": (("Piskota", "1", "kg"), ("Fondant", "0.5", "kg"), ("Lekvar", "0.2", "kg")),
    },
    {
        "sku": "G-EDES-002",
        "yield_quantity": "50",
        "yield_uom_code": "pcs",
        "ingredients": (("Liszt", "0.5", "kg"), ("Vaj", "0.3", "kg"), ("Csoki", "0.3", "kg"), ("Lekvar", "0.2", "kg")),
    },
    {
        "sku": "G-EDES-003",
        "yield_quantity": "40",
        "yield_uom_code": "pcs",
        "ingredients": (("Liszt", "1", "kg"), ("Dio", "0.4", "kg"), ("Lekvar", "0.4", "kg")),
    },
    {
        "sku": "G-EDES-004",
        "yield_quantity": "50",
        "yield_uom_code": "pcs",
        "ingredients": (("Piskota", "1", "kg"), ("Rum aroma", "0.1", "l"), ("Cukor", "0.3", "kg")),
    },
    {
        "sku": "G-EDES-005",
        "yield_quantity": "30",
        "yield_uom_code": "pcs",
        "ingredients": (("Leveles teszta", "1", "kg"), ("Tej", "1", "l"), ("Tojas", "5", "pcs")),
    },
    {
        "sku": "G-EDES-006",
        "yield_quantity": "25",
        "yield_uom_code": "portion",
        "ingredients": (("Piskota", "1", "kg"), ("Dio", "0.3", "kg"), ("Csokiontet", "0.2", "l")),
    },
    {
        "sku": "G-EDES-007",
        "yield_quantity": "50",
        "yield_uom_code": "pcs",
        "ingredients": (("Liszt", "0.5", "kg"), ("Kokusz", "0.2", "kg"), ("Csoki", "0.2", "kg")),
    },
    {
        "sku": "G-EDES-008",
        "yield_quantity": "40",
        "yield_uom_code": "pcs",
        "ingredients": (("Liszt", "1", "kg"), ("Alma", "1", "kg"), ("Cukor", "0.3", "kg")),
    },
    {
        "sku": "G-EDES-009",
        "yield_quantity": "30",
        "yield_uom_code": "pcs",
        "ingredients": (("Piskota", "1", "kg"), ("Tejszin", "0.5", "l"), ("Csoki", "0.3", "kg")),
    },
    {
        "sku": "G-EDES-010",
        "yield_quantity": "35",
        "yield_uom_code": "pcs",
        "ingredients": (("Piskota", "1", "kg"), ("Vajkrem", "0.5", "kg"), ("Karamell", "0.2", "kg")),
    },
    {
        "sku": "G-TORTA-001",
        "yield_quantity": "12",
        "yield_uom_code": "pcs",
        "ingredients": (("Tojas", "10", "pcs"), ("Liszt", "0.3", "kg"), ("Vaj", "0.5", "kg"), ("Cukor", "0.5", "kg")),
    },
    {
        "sku": "G-TORTA-002",
        "yield_quantity": "12",
        "yield_uom_code": "pcs",
        "ingredients": (("Csoki", "0.6", "kg"), ("Tejszin", "0.5", "l"), ("Liszt", "0.3", "kg")),
    },
    {
        "sku": "G-TORTA-003",
        "yield_quantity": "12",
        "yield_uom_code": "pcs",
        "ingredients": (("Eper", "0.5", "kg"), ("Tejszin", "0.5", "l"), ("Piskota", "1", "kg")),
    },
    {
        "sku": "G-TORTA-004",
        "yield_quantity": "12",
        "yield_uom_code": "pcs",
        "ingredients": (("Tej", "1", "l"), ("Tojas", "6", "pcs"), ("Tejszin", "0.5", "l")),
    },
    {
        "sku": "G-TORTA-005",
        "yield_quantity": "12",
        "yield_uom_code": "pcs",
        "ingredients": (("Csoki", "0.5", "kg"), ("Vaj", "0.4", "kg"), ("Lekvar", "0.3", "kg")),
    },
    {
        "sku": "G-FAGYI-001",
        "yield_quantity": "40",
        "yield_uom_code": "scoop",
        "ingredients": (("Tej", "1", "l"), ("Csoki", "0.2", "kg"), ("Cukor", "0.2", "kg")),
    },
    {
        "sku": "G-FAGYI-002",
        "yield_quantity": "40",
        "yield_uom_code": "scoop",
        "ingredients": (("Tej", "1", "l"), ("Vanilia rud", "1", "pcs"), ("Cukor", "0.2", "kg")),
    },
    {
        "sku": "G-FAGYI-003",
        "yield_quantity": "35",
        "yield_uom_code": "scoop",
        "ingredients": (("Eper", "0.5", "kg"), ("Tej", "0.5", "l"), ("Cukor", "0.2", "kg")),
    },
    {
        "sku": "G-FAGYI-004",
        "yield_quantity": "40",
        "yield_uom_code": "scoop",
        "ingredients": (("Tej", "1", "l"), ("Aroma", "0.1", "l"), ("Cukor", "0.2", "kg")),
    },
    {
        "sku": "G-FAGYI-005",
        "yield_quantity": "35",
        "yield_uom_code": "scoop",
        "ingredients": (("Citrom", "10", "pcs"), ("Viz", "0.5", "l"), ("Cukor", "0.3", "kg")),
    },
)
