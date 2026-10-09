"""Disease knowledge base for the AI Urban Farming Assistant.

The keys of ``DISEASE_INFO`` are exactly the 38 class labels produced by the
PlantVillage dataset (the canonical New Plant Diseases Dataset on Kaggle).
``train.py`` reads these keys to build ``labels.json`` so the ordering is always
reproducible, and the API uses the same dict to attach treatment / prevention
advice to a prediction.

Every entry contains:
    crop          -> human readable crop name
    disease       -> human readable disease name ("Healthy" for healthy classes)
    healthy       -> bool, True when the class is a healthy plant
    severity      -> "None" | "Low" | "Moderate" | "High"
    symptoms      -> list[str]
    treatment     -> list[str]
    prevention    -> list[str]
    explanation   -> short explanation used by the "explainable AI" panel

Dataset source / license
------------------------
PlantVillage / "New Plant Diseases Dataset":
    https://www.kaggle.com/datasets/vipoooool/new-plant-diseases-dataset
Original PlantVillage paper (Hughes & Salathe, 2015):
    https://arxiv.org/abs/1511.08060
    Released under CC0 1.0 / public domain for the leaf images.
Always re-check the license on the dataset page before redistribution.
"""

from __future__ import annotations


def _entry(
    crop: str,
    disease: str,
    healthy: bool,
    severity: str,
    symptoms: list[str],
    treatment: list[str],
    prevention: list[str],
    explanation: str,
) -> dict:
    return {
        "crop": crop,
        "disease": disease,
        "healthy": healthy,
        "severity": severity,
        "symptoms": symptoms,
        "treatment": treatment,
        "prevention": prevention,
        "explanation": explanation,
    }


_GENERIC_CARE = [
    "Space plants so air can move freely between leaves",
    "Water at the base to keep the foliage dry",
    "Remove and dispose of infected plant debris",
    "Rotate crops each season where possible",
]

DISEASE_INFO: dict[str, dict] = {
    # ---------------------------------------------------------------- Apple
    "Apple___Apple_scab": _entry(
        "Apple", "Apple Scab", False, "Moderate",
        ["Olive-green to black velvety spots on leaves", "Leaves curl and drop early", "Scabby lesions on fruit"],
        ["Rake and destroy fallen infected leaves", "Apply a fungicide (captan or myclobutanil) at bud break", "Prune to improve airflow"],
        ["Plant scab-resistant cultivars", "Avoid overhead irrigation", "Apply preventative fungicide in spring"],
        "Dark velvet-textured lesions are the classic signature of Venturia inaequalis (apple scab).",
    ),
    "Apple___Black_rot": _entry(
        "Apple", "Black Rot", False, "High",
        ["Purple spots that enlarge into brown 'frogeye' lesions", "Fruit rots into black mummies", "Cankers on branches"],
        ["Remove mummified fruit and cankered wood", "Apply fungicide from bud break through midsummer", "Sterilise pruning tools"],
        ["Prune out dead wood yearly", "Keep the orchard floor clear of fallen fruit", "Maintain tree vigour"],
        "Frogeye leaf spots and black fruit mummies indicate the fungal pathogen Botryosphaeria obtusa.",
    ),
    "Apple___Cedar_apple_rust": _entry(
        "Apple", "Cedar Apple Rust", False, "Moderate",
        ["Bright orange-yellow spots with red halos on leaves", "Raised spore tubes on leaf undersides", "Premature defoliation"],
        ["Apply fungicide during the spring infection window", "Remove nearby juniper / cedar hosts if feasible"],
        ["Plant resistant apple varieties", "Start a preventative spray program at bud break"],
        "Orange rusty lesions in spring point to Gymnosporangium rusts that alternate on junipers.",
    ),
    "Apple___healthy": _entry(
        "Apple", "Healthy", True, "None",
        ["Uniform green leaves", "No spots, lesions or discoloration", "Strong new growth"],
        _GENERIC_CARE,
        ["Continue routine monitoring", "Keep consistent watering and feeding"],
        "Leaf colour and texture fall within the healthy range for apple.",
    ),
    # ------------------------------------------------------------ Blueberry
    "Blueberry___healthy": _entry(
        "Blueberry", "Healthy", True, "None",
        ["Glossy green foliage", "No lesions", "Healthy fruit set"],
        _GENERIC_CARE,
        ["Grow in acidic, well-drained soil (pH 4.5-5.5)", "Mulch to retain moisture"],
        "No disease indicators were found on this blueberry leaf.",
    ),
    # ---------------------------------------------------------------- Cherry
    "Cherry_(including_sour)___Powdery_mildew": _entry(
        "Cherry", "Powdery Mildew", False, "Moderate",
        ["White powdery coating on leaves", "Leaf curling and distortion", "Stunted shoot growth"],
        ["Apply sulfur or potassium-bicarbonate spray", "Improve air circulation by pruning", "Remove infected shoots"],
        ["Avoid excess nitrogen", "Plant in full sun with good airflow", "Water at the base"],
        "A white powdery film is the hallmark of Podosphaera fungal infections.",
    ),
    "Cherry_(including_sour)___healthy": _entry(
        "Cherry", "Healthy", True, "None",
        ["Clean green leaves", "No powder or spots", "Normal leaf shape"],
        _GENERIC_CARE,
        ["Monitor for aphids and fungal spots", "Prune for airflow"],
        "This cherry leaf shows no signs of infection.",
    ),
    # ------------------------------------------------------------------ Corn
    "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot": _entry(
        "Corn", "Gray Leaf Spot", False, "High",
        ["Long rectangular grey-brown lesions between veins", "Lesions run parallel to the leaf", "Severe blighting in humid weather"],
        ["Apply a strobilurin fungicide", "Improve field airflow", "Remove crop residue after harvest"],
        ["Use resistant hybrids", "Rotate away from corn", "Avoid overhead irrigation"],
        "Rectangular lesions bounded by leaf veins are typical of Cercospora zeae-maydis.",
    ),
    "Corn_(maize)___Common_rust_": _entry(
        "Corn", "Common Rust", False, "Moderate",
        ["Small cinnamon-brown pustules on leaves", "Pustules on both leaf surfaces", "Yellowing around pustules"],
        ["Apply fungicide if infection is early", "Destroy volunteer corn", "Manage humidity"],
        ["Plant rust-resistant hybrids", "Monitor fields in cool, humid weather"],
        "Cinnamon-brown powdery pustules indicate Puccinia sorghi (common rust).",
    ),
    "Corn_(maize)___Northern_Leaf_Blight": _entry(
        "Corn", "Northern Leaf Blight", False, "High",
        ["Long cigar-shaped grey-green lesions", "Lesions 2-15 cm long", "Blighting from lower leaves up"],
        ["Apply fungicide at early symptom stage", "Incorporate crop residue", "Rotate crops"],
        ["Grow resistant hybrids", "Practice crop rotation", "Reduce plant density"],
        "Cigar-shaped grey lesions are the signature of Exserohilum turcicum.",
    ),
    "Corn_(maize)___healthy": _entry(
        "Corn", "Healthy", True, "None",
        ["Uniform green leaves", "No pustules or lesions", "Vigorous growth"],
        _GENERIC_CARE,
        ["Scout weekly during humid periods"],
        "No disease indicators were found on this corn leaf.",
    ),
    # ----------------------------------------------------------------- Grape
    "Grape___Black_rot": _entry(
        "Grape", "Black Rot", False, "High",
        ["Brown circular leaf spots with dark borders", "Fruit shrivels into black mummies", "Tiny black pycnidia in spots"],
        ["Remove mummified berries and infected canes", "Apply fungicide from bud break", "Improve canopy airflow"],
        ["Train vines for open canopy", "Sanitation of fallen debris", "Preventative fungicide program"],
        "Brown leaf spots with black fruiting bodies indicate Guignardia bidwellii.",
    ),
    "Grape___Esca_(Black_Measles)": _entry(
        "Grape", "Esca (Black Measles)", False, "High",
        ["Tiger-stripe chlorosis between veins", "Marginal leaf scorch", "Dark spots on berries"],
        ["No chemical cure - remove heavily infected vines", "Prune affected wood well below symptoms", "Seal large pruning wounds"],
        ["Avoid large pruning wounds", "Delay pruning to late winter", "Maintain vine vigour"],
        "Interveinal chlorosis and scorch are consistent with the Esca trunk-disease complex.",
    ),
    "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)": _entry(
        "Grape", "Leaf Blight (Isariopsis Leaf Spot)", False, "Moderate",
        ["Irregular brown spots on leaves", "Spots coalesce causing blight", "Leaf drop in severe cases"],
        ["Remove infected leaves", "Apply fungicide", "Improve air circulation"],
        ["Canopy management", "Avoid overhead irrigation", "Routine fungicide schedule"],
        "Irregular brown lesions are associated with Pseudocercospora (Isariopsis) leaf spot.",
    ),
    "Grape___healthy": _entry(
        "Grape", "Healthy", True, "None",
        ["Clean green leaves", "No spots or scorch", "Even canopy"],
        _GENERIC_CARE,
        ["Monitor during warm, humid weather"],
        "This grape leaf is free of visible disease.",
    ),
    # ---------------------------------------------------------------- Orange
    "Orange___Haunglongbing_(Citrus_greening)": _entry(
        "Orange", "Huanglongbing (Citrus Greening)", False, "High",
        ["Blotchy mottled yellow leaves", "Asymmetric yellowing across the midrib", "Small lopsided bitter fruit"],
        ["There is no cure - remove infected trees", "Control the Asian citrus psyllid vector", "Report to local agriculture authority"],
        ["Use certified disease-free nursery stock", "Monitor and manage psyllid populations", "Quarantine new trees"],
        "Blotchy asymmetric mottling is a strong indicator of Candidatus Liberibacter (citrus greening).",
    ),
    # ----------------------------------------------------------------- Peach
    "Peach___Bacterial_spot": _entry(
        "Peach", "Bacterial Spot", False, "Moderate",
        ["Small water-soaked spots on leaves", "Spots turn purple-brown and drop out", "Cracked, pitted fruit"],
        ["Apply copper or oxytetracycline spray", "Remove severely infected fruit", "Avoid overhead watering"],
        ["Plant resistant cultivars", "Use windbreaks to reduce spread", "Copper spray during dormancy"],
        "Angular purple-brown leaf spots point to Xanthomonas campestris pv. pruni.",
    ),
    "Peach___healthy": _entry(
        "Peach", "Healthy", True, "None",
        ["Smooth green leaves", "No spots or shot-holes", "Even colour"],
        _GENERIC_CARE,
        ["Thin fruit for airflow", "Monitor in wet springs"],
        "No bacterial spot indicators were detected on this peach leaf.",
    ),
    # ------------------------------------------------------------ Bell pepper
    "Pepper,_bell___Bacterial_spot": _entry(
        "Pepper, bell", "Bacterial Spot", False, "High",
        ["Small water-soaked leaf spots", "Spots turn dark brown with yellow halos", "Scabby raised spots on fruit"],
        ["Apply copper-based bactericide", "Remove infected plants in severe cases", "Avoid working in wet foliage"],
        ["Use disease-free seed", "Rotate crops", "Avoid overhead irrigation"],
        "Water-soaked dark spots with halos indicate Xanthomonas bacterial spot.",
    ),
    "Pepper,_bell___healthy": _entry(
        "Pepper, bell", "Healthy", True, "None",
        ["Dark green glossy leaves", "No spotting", "Healthy fruit set"],
        _GENERIC_CARE,
        ["Keep soil evenly moist, not waterlogged"],
        "This bell pepper leaf shows no disease.",
    ),
    # ---------------------------------------------------------------- Potato
    "Potato___Early_blight": _entry(
        "Potato", "Early Blight", False, "Moderate",
        ["Dark brown target-like concentric spots", "Yellowing around lesions", "Lower leaves affected first"],
        ["Remove infected foliage", "Apply chlorothalonil or mancozeb fungicide", "Ensure balanced fertilisation"],
        ["Rotate away from solanaceous crops", "Mulch to prevent soil splash", "Water at the base"],
        "Concentric 'target' lesions are characteristic of Alternaria solani (early blight).",
    ),
    "Potato___Late_blight": _entry(
        "Potato", "Late Blight", False, "High",
        ["Large water-soaked grey-green lesions", "White fuzzy growth on leaf undersides", "Rapid collapse in cool, wet weather"],
        ["Apply fungicide immediately", "Destroy severely infected plants", "Harvest tubers promptly if tops die"],
        ["Plant certified seed potatoes", "Improve airflow and drainage", "Monitor weather for blight risk"],
        "Water-soaked spreading lesions with white sporulation suggest Phytophthora infestans (late blight).",
    ),
    "Potato___healthy": _entry(
        "Potato", "Healthy", True, "None",
        ["Vigorous green foliage", "No lesions", "Uniform leaf colour"],
        _GENERIC_CARE,
        ["Hill soil around stems", "Scout for blight in humid weather"],
        "No disease indicators were found on this potato leaf.",
    ),
    # -------------------------------------------------------------- Raspberry
    "Raspberry___healthy": _entry(
        "Raspberry", "Healthy", True, "None",
        ["Bright green compound leaves", "No spots or rust", "Strong canes"],
        _GENERIC_CARE,
        ["Prune old canes after fruiting"],
        "This raspberry leaf is free of visible disease.",
    ),
    # --------------------------------------------------------------- Soybean
    "Soybean___healthy": _entry(
        "Soybean", "Healthy", True, "None",
        ["Uniform green trifoliate leaves", "No lesions", "Healthy canopy"],
        _GENERIC_CARE,
        ["Rotate with cereal crops"],
        "No disease indicators were found on this soybean leaf.",
    ),
    # ---------------------------------------------------------------- Squash
    "Squash___Powdery_mildew": _entry(
        "Squash", "Powdery Mildew", False, "Moderate",
        ["White powdery patches on leaf surface", "Leaves yellow and dry", "Reduced fruit size"],
        ["Apply potassium bicarbonate or sulfur spray", "Remove heavily infected leaves", "Improve airflow"],
        ["Plant in full sun with spacing", "Avoid excess nitrogen", "Water at the base in the morning"],
        "White powdery growth on squash leaves is caused by Podosphaera xanthii.",
    ),
    # ------------------------------------------------------------ Strawberry
    "Strawberry___Leaf_scorch": _entry(
        "Strawberry", "Leaf Scorch", False, "Moderate",
        ["Small purple spots enlarging into brown patches", "Leaf margins look scorched", "Reduced vigour"],
        ["Remove infected leaves", "Apply fungicide", "Improve drainage and airflow"],
        ["Use resistant cultivars", "Avoid overhead irrigation", "Renovate beds after harvest"],
        "Coalescing purple-brown spots that scorch the leaf are typical of Diplocarpon earlianum.",
    ),
    "Strawberry___healthy": _entry(
        "Strawberry", "Healthy", True, "None",
        ["Bright green trifoliate leaves", "No spots", "Healthy crown"],
        _GENERIC_CARE,
        ["Mulch with straw to keep fruit clean"],
        "This strawberry leaf shows no disease.",
    ),
    # ---------------------------------------------------------------- Tomato
    "Tomato___Bacterial_spot": _entry(
        "Tomato", "Bacterial Spot", False, "High",
        ["Small greasy water-soaked leaf spots", "Spots turn brown with yellow halos", "Scabby fruit spots"],
        ["Apply copper + mancozeb bactericide", "Remove infected tissue", "Avoid overhead watering"],
        ["Use certified disease-free seed", "Rotate crops for 2+ years", "Keep foliage dry"],
        "Greasy water-soaked spots on tomato suggest Xanthomonas bacterial spot.",
    ),
    "Tomato___Early_blight": _entry(
        "Tomato", "Early Blight", False, "Moderate",
        ["Brown concentric 'target' spots", "Yellow halo around lesions", "Lower, older leaves affected first"],
        ["Remove infected lower leaves", "Apply chlorothalonil, copper or biofungicide", "Mulch and feed the plant"],
        ["Rotate crops", "Mulch to stop soil splash", "Water at the base and stake plants"],
        "Concentric target-like lesions on lower tomato leaves are classic Alternaria solani (early blight).",
    ),
    "Tomato___Late_blight": _entry(
        "Tomato", "Late Blight", False, "High",
        ["Large greasy grey-brown blotches", "White fuzzy mould on leaf undersides", "Rapid collapse in cool, wet weather"],
        ["Remove and destroy infected plants", "Apply a fungicide immediately", "Harvest remaining healthy fruit"],
        ["Plant resistant varieties", "Improve airflow", "Avoid overhead watering in cool weather"],
        "Rapidly spreading water-soaked blotches with white sporulation indicate Phytophthora infestans (late blight).",
    ),
    "Tomato___Leaf_Mold": _entry(
        "Tomato", "Leaf Mold", False, "Moderate",
        ["Pale-green spots on the upper leaf", "Olive-green velvety mould underneath", "Leaves yellow and drop"],
        ["Improve ventilation and reduce humidity", "Remove infected leaves", "Apply appropriate fungicide"],
        ["Reduce greenhouse humidity", "Space plants", "Water at the base in the morning"],
        "Olive velvety mould on the leaf underside signals Passalora fulva (leaf mold).",
    ),
    "Tomato___Septoria_leaf_spot": _entry(
        "Tomato", "Septoria Leaf Spot", False, "Moderate",
        ["Small circular spots with grey centres", "Dark borders and tiny black dots inside spots", "Lower leaves defoliate"],
        ["Remove infected leaves", "Apply fungicide (chlorothalonil/copper)", "Mulch to prevent splash"],
        ["Rotate crops", "Stake and prune for airflow", "Water at the base"],
        "Numerous small spots with grey centres and black pycnidia indicate Septoria lycopersici.",
    ),
    "Tomato___Spider_mites Two-spotted_spider_mite": _entry(
        "Tomato", "Spider Mites (Two-spotted)", False, "Moderate",
        ["Fine stippling / speckling on leaves", "Fine webbing on leaf undersides", "Leaves bronze and dry out"],
        ["Spray leaves (especially undersides) with water to dislodge mites", "Apply insecticidal soap or neem oil", "Introduce predatory mites"],
        ["Keep plants well watered to reduce stress", "Avoid dusty conditions", "Monitor undersides regularly"],
        "Fine stippling with webbing points to an infestation of two-spotted spider mites.",
    ),
    "Tomato___Target_Spot": _entry(
        "Tomato", "Target Spot", False, "Moderate",
        ["Brown spots with concentric rings", "Lesions on leaves, stems and fruit", "Defoliation in severe cases"],
        ["Apply fungicide", "Remove infected leaves", "Improve airflow"],
        ["Rotate crops", "Avoid overhead irrigation", "Maintain plant spacing"],
        "Concentric-ringed brown lesions indicate Corynespora cassiicola (target spot).",
    ),
    "Tomato___Tomato_Yellow_Leaf_Curl_Virus": _entry(
        "Tomato", "Tomato Yellow Leaf Curl Virus", False, "High",
        ["Upward curling and cupping of leaves", "Yellowing leaf margins", "Stunted plants and poor fruit set"],
        ["No cure - remove infected plants", "Control whitefly (the vector)", "Use reflective mulches / row covers"],
        ["Plant resistant varieties", "Manage whitefly populations", "Use insect screens in greenhouses"],
        "Upward leaf curling with yellow margins is characteristic of whitefly-transmitted TYLCV.",
    ),
    "Tomato___Tomato_mosaic_virus": _entry(
        "Tomato", "Tomato Mosaic Virus", False, "Moderate",
        ["Mosaic light/dark green mottling", "Leaf distortion and fern-leaf", "Stunted growth"],
        ["Remove and destroy infected plants", "Disinfect tools and hands", "Control aphids"],
        ["Use virus-free seed", "Disinfect tools between plants", "Avoid tobacco contact (can carry the virus)"],
        "Light and dark green mosaic mottling is typical of the highly contagious tomato mosaic virus.",
    ),
    "Tomato___healthy": _entry(
        "Tomato", "Healthy", True, "None",
        ["Deep green, even leaves", "No spots or curling", "Strong stems and new growth"],
        _GENERIC_CARE,
        ["Stake plants and water consistently", "Feed every 2-3 weeks"],
        "This tomato leaf is free of visible disease indicators.",
    ),
}


def labels() -> list[str]:
    """Return the sorted class labels in a deterministic order."""
    return sorted(DISEASE_INFO.keys())


def get_info(label: str) -> dict:
    """Look up disease info by class label, with a safe fallback."""
    return DISEASE_INFO.get(label, {
        "crop": label.split("___")[0].replace("_", " "),
        "disease": label.split("___")[-1].replace("_", " "),
        "healthy": "healthy" in label.lower(),
        "severity": "Unknown",
        "symptoms": ["Symptoms could not be matched to a known class"],
        "treatment": ["Consult a local agronomist for a confirmed diagnosis"],
        "prevention": _GENERIC_CARE,
        "explanation": "The model returned a class outside the known knowledge base.",
    })
