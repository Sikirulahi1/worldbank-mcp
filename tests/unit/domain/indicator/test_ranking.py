"""Unit tests for domain/indicator/ranking.py."""
from src.domain.indicator.entities import IndicatorCandidate
from src.domain.indicator.ranking import rank_candidates


def test_rank_candidates():
    candidates = [
        IndicatorCandidate("ID_3", "C", "DB", 15.0),
        IndicatorCandidate("ID_1", "A", "DB", 20.5),
        IndicatorCandidate("ID_2", "B", "DB", 20.5), # Tie in score
        IndicatorCandidate("ID_4", "D", "DB", 5.0),
    ]
    
    ranked = rank_candidates(candidates)
    
    assert len(ranked) == 4
    
    # Highest score first
    assert ranked[0].idno == "ID_1"
    
    # Tie broken by idno alphabetically
    assert ranked[1].idno == "ID_2"
    
    # Next highest score
    assert ranked[2].idno == "ID_3"
    
    # Lowest score last
    assert ranked[3].idno == "ID_4"


def test_rank_empty():
    assert rank_candidates([]) == []
