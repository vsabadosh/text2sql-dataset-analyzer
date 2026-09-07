from __future__ import annotations

import pytest

from text2sql_pipeline.analyzers.question_sql_consistency import (
    lexical_resources as lex,
)


def test_corpora_are_available_in_the_test_environment():
    lex.ensure_available()
    versions = lex.resource_versions()
    assert versions["wordnet"] != "unavailable"
    assert set(versions) == {"nltk", "rapidfuzz", "inflect", "wordnet"}


@pytest.mark.parametrize(
    "text, expected",
    [
        ("cook", True),
        # An exact lemma, not a stem: reducing 'cookes' to 'cook' would hide
        # the very slip the near-miss rule looks for.
        ("cookes", False),
        ("Lucas", True),
        ("qwertyuiop", False),
    ],
)
def test_is_known_word_matches_exact_lemmas_only(text, expected):
    assert lex.is_known_word(text) is expected


def test_known_word_or_form_accepts_regular_inflections():
    assert lex.is_known_word("countries") is False
    assert lex.is_known_word_or_form("countries") is True
    assert lex.is_known_word_or_form("coutries") is False


def test_productive_derivative_guard_is_conservative():
    assert lex.is_productive_derivative("schooler") is True
    assert lex.is_productive_derivative("reshared") is True
    assert lex.is_productive_derivative("uncredited") is True
    assert lex.is_productive_derivative("headquarted") is False
    assert lex.is_productive_derivative("recieved") is False


def test_number_inflection_forms_cover_identifier_references():
    assert lex.number_inflection_forms("country") == ("countries", "country")
    assert lex.number_inflection_forms("countries") == ("countries", "country")
    assert lex.number_inflection_forms("qwerty") == ("qwerty",)


def test_non_cardinal_number_forms_are_generated_separately():
    assert lex.multiplicative_number_forms("2") == ("twice",)
    assert lex.multiplicative_number_forms("4") == ()
    assert lex.count_quantifier_forms("1") == ("single",)
    assert lex.count_quantifier_forms("2") == ()
    assert lex.ordinal_number_forms("5") == ("5th", "fifth")
    assert "100000000000th" in lex.ordinal_number_forms("100000000000")
    assert lex.ordinal_number_forms("1e100") == ()
    assert lex.ordinal_number_forms("3.5") == ()


@pytest.mark.parametrize(
    "candidate,value",
    [
        ("Stanford", "Stanford University"),
        ("MPEG", "MPEG audio file"),
        ("Gatwick", "London Gatwick"),
        ("Computer Information Systems", "Computer Info Systems"),
        ("collectible cards", "Collectible card game"),
        ("US", "United States"),
    ],
)
def test_conservative_abbreviation_shapes(candidate, value):
    assert lex.is_abbreviation_variant(candidate, value) is True


@pytest.mark.parametrize(
    "candidate,value",
    [
        ("United", "United States"),
        ("audio", "MPEG audio file"),
        ("us", "United States"),
        ("Luca", "Lucas"),
        ("Sky", "Skyfall"),
        ("Ball to the Wall", "Balls to the Wall"),
    ],
)
def test_common_fragments_and_lowercase_initials_are_not_abbreviations(
    candidate, value
):
    assert lex.is_abbreviation_variant(candidate, value) is False


@pytest.mark.parametrize(
    "candidate,value",
    [
        ("European", "Europe"),
        ("Canadian", "Canada"),
        ("French", "France"),
    ],
)
def test_wordnet_pertainyms_license_demonyms(candidate, value):
    assert lex.is_pertainym_variant(candidate, value) is True


def test_pertainyms_do_not_invent_external_aliases():
    assert lex.is_pertainym_variant("British", "UK") is False


@pytest.mark.parametrize(
    "candidate,value",
    [
        ("successful", "Success"),
        ("lithographic", "lithograph"),
        ("failed", "fail"),
        ("research", "researcher"),
    ],
)
def test_guarded_derivational_variants(candidate, value):
    assert lex.is_derivational_variant(candidate, value) is True


@pytest.mark.parametrize(
    "candidate,value",
    [
        ("Luca", "Lucas"),
        ("Dean", "Daan"),
        ("cookes", "Cookie"),
    ],
)
def test_derivational_matching_preserves_known_typo_findings(candidate, value):
    assert lex.is_derivational_variant(candidate, value) is False


@pytest.mark.parametrize(
    "text, expected",
    [
        ("dean", True),
        # WordNet stores proper nouns capitalised, which is what separates a
        # name from a common word.
        ("lucas", False),
        ("advertisements", True),
    ],
)
def test_is_common_word_separates_names_from_words(text, expected):
    assert lex.is_common_word(text) is expected


@pytest.mark.parametrize(
    "left, right, expected",
    [
        ("dean", "daan", 1),
        ("caribbean", "carribean", 2),
        ("peeters", "peeters", None),
        # One edit within four characters is as likely to be another value.
        ("read", "red", 1),
        ("cat", "dog", None),
    ],
)
def test_near_miss_distance_is_calibrated_to_length(left, right, expected):
    assert lex.near_miss_distance(left, right) == expected


def test_only_longer_strings_get_a_two_edit_budget():
    assert lex.near_miss_distance("anna", "anne") == 1
    assert lex.near_miss_distance("anna", "ande") is None
    assert lex.near_miss_distance("mortage", "mortgages") == 2


@pytest.mark.parametrize(
    "candidate, value, expected",
    [
        # A question pluralising a stored singular is ordinary paraphrase.
        ("volvos", "volvo", True),
        ("b 52 bombers", "b 52 bomber", True),
        ("advertisement", "advertisements", True),
        # The mirror shape is how name typos present themselves, so it only
        # counts as inflection when the stored value is a real word.
        ("luca", "lucas", False),
        ("dean", "daan", False),
    ],
)
def test_inflectional_variant_is_direction_sensitive(candidate, value, expected):
    assert lex.is_inflectional_variant(candidate, value) is expected


def test_number_word_forms_cover_both_and_variants():
    assert lex.number_word_forms("25000") == ("twenty-five thousand",)
    assert lex.number_word_forms("1234") == (
        "one thousand, two hundred and thirty-four",
        "one thousand, two hundred thirty-four",
    )
    assert lex.number_word_forms("3.5") == ()
    assert lex.number_word_forms("1e100") == ()
    assert lex.number_word_forms("PAID") == ()


def test_missing_corpus_fails_loudly_with_the_fetch_command(monkeypatch):
    """A guard that decides verdicts must not degrade quietly."""

    def raise_lookup():
        raise LookupError("Resource corpora/wordnet not found.")

    monkeypatch.setattr(lex, "_wordnet", raise_lookup)
    with pytest.raises(lex.LexicalResourcesUnavailable) as error:
        lex.ensure_available()

    assert "wordnet" in str(error.value)
    assert "text2sql lexical-data" in str(error.value)


def test_function_words_are_recognised():
    assert lex.is_function_word("the") is True
    assert lex.is_function_word("dean") is False
