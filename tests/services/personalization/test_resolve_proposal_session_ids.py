"""Tests for resolve_proposal_session_ids.

Ensures the resolver:
- canonicalises `uuid__partN` suffixes,
- drops hallucinated or unknown IDs,
- falls back to the full loaded set when no cited IDs match.
"""

from vibelens.services.personalization.shared import resolve_proposal_session_ids


def test_empty_proposal_ids_returns_full_loaded_set() -> None:
    loaded = ["abc-1", "def-2", "ghi-3"]
    assert resolve_proposal_session_ids(
        proposal_session_ids=[],
        loaded_session_ids=loaded,
    ) == loaded
    print("empty proposal_ids → full loaded set")


def test_cited_ids_filtered_to_loaded_set() -> None:
    loaded = ["abc-1", "def-2", "ghi-3"]
    proposal = ["abc-1", "ghi-3", "hallucinated-x"]
    resolved = resolve_proposal_session_ids(
        proposal_session_ids=proposal,
        loaded_session_ids=loaded,
    )
    assert resolved == ["abc-1", "ghi-3"]
    print(f"proposal {proposal} → {resolved} (hallucinated dropped)")


def test_partn_suffix_canonicalised_both_sides() -> None:
    # Loaded IDs may have been split into __part1/__part2; proposal may cite
    # either the base or a part suffix. Canonical match must succeed.
    loaded = ["abc-1__part1", "abc-1__part2", "def-2"]
    proposal = ["abc-1", "def-2__part1"]
    resolved = resolve_proposal_session_ids(
        proposal_session_ids=proposal,
        loaded_session_ids=loaded,
    )
    assert resolved == ["abc-1", "def-2"]
    print(f"loaded {loaded} + proposal {proposal} → {resolved}")


def test_duplicates_deduplicated() -> None:
    loaded = ["abc-1", "def-2"]
    proposal = ["abc-1", "abc-1__part1", "abc-1"]
    resolved = resolve_proposal_session_ids(
        proposal_session_ids=proposal,
        loaded_session_ids=loaded,
    )
    assert resolved == ["abc-1"]
    print(f"duplicates/parts in {proposal} → deduped {resolved}")


def test_all_cited_unknown_falls_back_to_loaded() -> None:
    loaded = ["abc-1", "def-2"]
    proposal = ["unknown-x", "unknown-y"]
    resolved = resolve_proposal_session_ids(
        proposal_session_ids=proposal,
        loaded_session_ids=loaded,
    )
    assert resolved == loaded
    print(f"all-unknown {proposal} → fallback {resolved}")
