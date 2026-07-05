from src.retrieval.project_detector import detect_project, normalize_text

def test_normalize_text():
    assert normalize_text("Explain TalentForge") == "explain talentforge"
    assert normalize_text("n8n-aks-platform") == "n8n aks platform"
    assert normalize_text("  talent  forge!!!  ") == "talent forge"
    assert normalize_text("") == ""
    assert normalize_text(None) == ""

def test_detect_project_exact_names():
    assert detect_project("Tell me about talentforge") == "talentforge"
    assert detect_project("Explain reservation-system") == "reservation-system"
    assert detect_project("Show classsync details") == "classsync"

def test_detect_project_aliases():
    assert detect_project("How does talent forge rank candidates?") == "talentforge"
    assert detect_project("What is the reservation system?") == "reservation-system"
    assert detect_project("How to deploy aks?") == "n8n-aks-platform"
    assert detect_project("Explain kubernetes configuration") == "n8n-aks-platform"
    assert detect_project("Is class sync automated?") == "classsync"

def test_detect_project_case_and_punctuation():
    assert detect_project("Explain TALENT Forge!!!") == "talentforge"
    assert detect_project("what about N8N/AKS?") == "n8n-aks-platform"
    assert detect_project("explain reservation_system.") == "reservation-system"

def test_detect_project_no_match():
    assert detect_project("What is Ajay's work experience?") is None
    assert detect_project("Do you know Python and FastAPI?") is None

def test_detect_project_ambiguous():
    # If multiple different projects match, it should return None
    assert detect_project("Compare TalentForge with ClassSync") is None
    assert detect_project("How does aks deploy classsync?") is None

def test_detect_project_word_boundaries():
    # 'aks' is an alias, but 'tasks' or 'aksers' should not match
    assert detect_project("Show all cron tasks") is None
    assert detect_project("aksers deployment rules") is None
    # 'n8n' is an alias, but 'n8nner' should not match
    assert detect_project("n8nner workflows") is None

def test_detect_project_nested_aliases_consumption():
    # 'reservation system' contains 'reservation'. 
    # Sorting by length and replacing matched spans prevents duplicate projects/confusion.
    assert detect_project("Explain the reservation system") == "reservation-system"
    # Even if they are in different order or separate, it should handle them.
    assert detect_project("We use aks and kubernetes") == "n8n-aks-platform"

def test_explicit_project_wins():
    # Scenario A: Explicit project is passed (should win, no auto-detection runs)
    query = "Explain TalentForge"
    explicit_project = "reservation-system"
    resolved_project = explicit_project if explicit_project is not None else detect_project(query)
    assert resolved_project == "reservation-system"
    
    # Scenario B: No project is passed, auto-detection executes
    query = "Explain TalentForge"
    explicit_project = None
    resolved_project = explicit_project if explicit_project is not None else detect_project(query)
    assert resolved_project == "talentforge"
