"""Lexical predicates behind the deterministic question-SQL rules.

Every use of `nltk`, `rapidfuzz` and `inflect` lives here, so the rules stay
free of library detail and the vocabulary source can be replaced without
touching them. Replacing WordNet with a generated lemma index later is a change
to this file alone.

Nothing here is statistical: the same input yields the same answer for a given
corpus version, which is what lets a finding be re-audited from the assumptions
recorded with it.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from functools import lru_cache
import re

REQUIRED_CORPORA = ("wordnet", "stopwords")

_DOWNLOAD_HINT = (
    "Run `text2sql lexical-data` once to fetch it, or point NLTK_DATA at an "
    "existing copy."
)

_FOLD_RE = re.compile(r"[^0-9a-z ]+")
_PRODUCTIVE_SUFFIXES = (
    "ation",
    "ment",
    "ness",
    "ers",
    "ing",
    "ed",
    "er",
    "ly",
)
_PRODUCTIVE_PREFIXES = ("re", "un")
# Written-number matching is useful for human-scale thresholds, not machine
# identifiers or scientific-notation magnitudes. Keeping a finite boundary also
# avoids inflect's documented/undocumented out-of-range failure modes.
_MAX_GENERATED_INTEGER = 10**15


class LexicalResourcesUnavailable(RuntimeError):
    """The lexical corpora are missing.

    Raised while the pipeline is being assembled rather than per item: a rule
    that silently loses its vocabulary guard would keep emitting findings with
    a worse false-positive rate, and that is harder to notice than a failure.
    """


def ensure_available() -> None:
    """Load the corpora, or fail with something the caller can act on."""
    try:
        _wordnet()
        _function_words()
    except LookupError as exc:
        missing = _missing_corpus(str(exc)) or "/".join(REQUIRED_CORPORA)
        raise LexicalResourcesUnavailable(
            f"Lexical corpus {missing!r} is not available. {_DOWNLOAD_HINT}"
        ) from exc


def download() -> dict[str, bool]:
    """Fetch the corpora. Used by the CLI, never by the analyzer itself."""
    import nltk

    return {corpus: bool(nltk.download(corpus)) for corpus in REQUIRED_CORPORA}


def resource_versions() -> dict[str, str]:
    """Versions to record with findings, so a verdict stays reproducible."""
    from importlib.metadata import PackageNotFoundError, version

    versions: dict[str, str] = {}
    for package in ("nltk", "rapidfuzz", "inflect"):
        try:
            versions[package] = version(package)
        except PackageNotFoundError:
            versions[package] = "unknown"
    try:
        versions["wordnet"] = _wordnet().get_version() or "unknown"
    except (LookupError, AttributeError):
        versions["wordnet"] = "unavailable"
    return versions


def fold(text: str) -> str:
    """Case-fold and strip punctuation, keeping word boundaries."""
    lowered = text.casefold().replace("-", " ").replace("_", " ")
    return " ".join(_FOLD_RE.sub(" ", lowered).split())


def is_function_word(token: str) -> bool:
    """Whether a token belongs to a closed class carrying no value content."""
    return token.casefold() in _function_words()


def is_known_word(text: str) -> bool:
    """Whether every token is an exact dictionary entry.

    Deliberately exact: `morphy` would reduce `cookes` to `cook` and hide the
    very typo the near-miss rule looks for. Proper nouns count as known, since
    WordNet lists them.
    """
    tokens = _alpha_tokens(text)
    return bool(tokens) and all(_has_lemma(token) for token in tokens)


def is_known_word_or_form(text: str) -> bool:
    """Whether every token is a WordNet lemma or a regular inflection.

    Literal near-miss detection deliberately uses the stricter
    :func:`is_known_word`: reducing ``cookes`` to ``cook`` could hide the typo
    it is meant to find. Question lexical integrity has a different job and
    must not call ordinary plurals such as ``countries`` spelling errors.
    """
    tokens = _alpha_tokens(text)
    return bool(tokens) and all(_has_lemma_or_form(token) for token in tokens)


def is_common_word(text: str) -> bool:
    """Whether every token is a common word rather than a proper name.

    WordNet capitalises proper-noun lemmas, so the test is free: `lucas`
    resolves only to the lemma `Lucas` and is therefore not a common word,
    while `dean` resolves to `dean`.

    Unlike `is_known_word` this accepts a regular inflection of a common word,
    because plural forms are absent from the dictionary: `advertisements` has
    to count as common for `advertisement` to be recognised as its singular.
    """
    tokens = _alpha_tokens(text)
    return bool(tokens) and all(_is_common_lemma_or_form(token) for token in tokens)


def is_productive_derivative(token: str) -> bool:
    """Whether an OOV token is a transparent derivation of a known word.

    WordNet does not list every productive English derivative. This narrow
    guard keeps forms such as ``schooler``, ``reshared`` and ``uncredited``
    from becoming typo findings while retaining real slips such as
    ``headquarted`` (its putative stem ``headquart`` is unknown).
    """
    folded = fold(token)
    if not folded or " " in folded or not folded.isalpha():
        return False
    has_known_suffix_base = any(
        len(folded) - len(suffix) >= 3
        and folded.endswith(suffix)
        and _has_lemma_or_form(folded[: -len(suffix)])
        for suffix in _PRODUCTIVE_SUFFIXES
    )
    has_known_prefix_base = any(
        len(folded) - len(prefix) >= 3
        and folded.startswith(prefix)
        and _has_lemma_or_form(folded[len(prefix) :])
        for prefix in _PRODUCTIVE_PREFIXES
    )
    return has_known_suffix_base or has_known_prefix_base


def number_inflection_forms(value: str) -> tuple[str, ...]:
    """Return a common noun together with its singular and plural forms."""
    folded = fold(value)
    if not folded or " " in folded or not folded.isalpha():
        return ()

    forms = {folded}
    if not is_common_word(folded):
        return (folded,)

    engine = _inflect_engine()
    singular = engine.singular_noun(folded)
    base = singular.casefold() if isinstance(singular, str) else folded
    forms.add(base)
    plural = engine.plural(base)
    if isinstance(plural, str):
        forms.add(plural.casefold())
    return tuple(sorted(forms))


def multiplicative_number_forms(value: str) -> tuple[str, ...]:
    """Adverbial count forms that cardinal number generation does not cover."""
    try:
        number = Decimal(value)
    except (InvalidOperation, ValueError):
        return ()
    if number != number.to_integral_value():
        return ()
    return {
        1: ("once",),
        2: ("twice",),
        3: ("thrice",),
    }.get(int(number), ())


def count_quantifier_forms(value: str) -> tuple[str, ...]:
    """Count-specific quantifiers not produced by cardinal number generation."""
    try:
        number = Decimal(value)
    except (InvalidOperation, ValueError):
        return ()
    return ("single",) if number == 1 else ()


def ordinal_number_forms(value: str) -> tuple[str, ...]:
    """Written ordinal forms of an integral SQL value."""
    try:
        number = Decimal(value)
    except (InvalidOperation, ValueError):
        return ()
    if number != number.to_integral_value():
        return ()
    if abs(number) > _MAX_GENERATED_INTEGER:
        return ()

    engine = _inflect_engine()
    # inflect accepts small Python ints but routes sufficiently large ints
    # through a regex path that expects text (observed on BIRD identifiers).
    ordinal = engine.ordinal(str(int(number)))
    forms = {str(ordinal), engine.number_to_words(ordinal)}
    return tuple(sorted(form for form in forms if form))


def is_abbreviation_variant(candidate: str, value: str) -> bool:
    """Whether a question phrase is a conservative abbreviation of a value.

    Accepted shapes are an uppercase initialism (``US``/``United States``), a
    token-wise prefix abbreviation (``Info``/``Information``), or a distinctive
    proper-name/acronym component (``Stanford``/``Stanford University``).
    Common single words are not allowed to stand for an arbitrary longer value.
    """
    candidate_tokens = fold(candidate).split()
    value_tokens = fold(value).split()
    if not candidate_tokens or not value_tokens or candidate_tokens == value_tokens:
        return False

    compact_candidate = "".join(candidate_tokens)
    initials = "".join(token[0] for token in value_tokens if token)
    raw_compact = re.sub(r"[^A-Za-z]", "", candidate)
    if (
        len(candidate_tokens) == 1
        and len(initials) >= 2
        and compact_candidate == initials
        and raw_compact.isupper()
    ):
        return True

    # A shortened single token is indistinguishable from a spelling mistake
    # (`Luca`/`Lucas`, `Sky`/`Skyfall`). Prefix abbreviation is admitted only
    # inside a multi-token phrase where unchanged neighbours bind the role.
    if len(candidate_tokens) == len(value_tokens) and len(value_tokens) >= 2:
        changed = False
        for left, right in zip(candidate_tokens, value_tokens):
            if left == right or is_inflectional_variant(left, right):
                continue
            if (
                min(len(left), len(right)) < 3
                or abs(len(left) - len(right)) < 2
                or not (left.startswith(right) or right.startswith(left))
            ):
                break
            changed = True
        else:
            return changed

    width = len(candidate_tokens)
    for start in range(len(value_tokens) - width + 1):
        value_window = value_tokens[start : start + width]
        if (
            width >= 2
            and width >= len(value_tokens) - 1
            and all(
                left == right or is_inflectional_variant(left, right)
                for left, right in zip(candidate_tokens, value_window)
            )
        ):
            return True
        if value_window != candidate_tokens:
            continue
        distinctive = any(not is_common_word(token) for token in candidate_tokens)
        if distinctive or (raw_compact.isupper() and len(raw_compact) >= 2):
            return True
    return False


def is_pertainym_variant(candidate: str, value: str) -> bool:
    """Whether WordNet relates an adjective to the named entity it pertains to."""
    candidate_folded, value_folded = fold(candidate), fold(value)
    if not candidate_folded or not value_folded:
        return False
    return (
        value_folded in _pertainym_names(candidate_folded)
        or candidate_folded in _pertainym_names(value_folded)
    )


def is_derivational_variant(candidate: str, value: str) -> bool:
    """Whether two words share a base or a direct WordNet derivation."""
    candidate_folded, value_folded = fold(candidate), fold(value)
    if (
        not candidate_folded
        or not value_folded
        or " " in candidate_folded
        or " " in value_folded
        or candidate_folded == value_folded
    ):
        return False
    candidate_bases = _morphy_forms(candidate_folded)
    value_bases = _morphy_forms(value_folded)
    if candidate_bases & value_bases:
        return True
    if (
        is_known_word_or_form(candidate_folded)
        and is_known_word_or_form(value_folded)
        and _stem(candidate_folded) == _stem(value_folded)
    ):
        return True
    return bool(
        _derivational_names(candidate_folded) & ({value_folded} | value_bases)
        or _derivational_names(value_folded)
        & ({candidate_folded} | candidate_bases)
    )


def near_miss_distance(left: str, right: str, *, short_len: int = 5) -> int | None:
    """Edit distance when two strings are one small slip apart, else None.

    The budget scales with the shorter string: one edit for short values, two
    for longer ones. Identical strings are not a near miss.
    """
    from rapidfuzz.distance import Levenshtein

    left, right = fold(left), fold(right)
    if not left or not right:
        return None
    budget = 1 if min(len(left), len(right)) <= short_len else 2
    distance = Levenshtein.distance(left, right, score_cutoff=budget)
    if 0 < distance <= budget:
        return distance
    return None


def is_inflectional_variant(candidate: str, value: str) -> bool:
    """Whether the two differ only by English number inflection.

    Direction matters. A question that pluralises a stored singular value
    ("all volvos" for `model = 'volvo'`) is ordinary paraphrase. The mirror
    shape, question singular against a stored value that merely looks plural,
    is how name typos present themselves (`Luca` against `Lucas`), so it counts
    as inflection only when the stored value is itself a common English word.
    """
    candidate_tokens, value_tokens = fold(candidate).split(), fold(value).split()
    if not candidate_tokens or len(candidate_tokens) != len(value_tokens):
        return False
    # Only the head noun carries number inflection in English.
    if candidate_tokens[:-1] != value_tokens[:-1]:
        return False

    head_candidate, head_value = candidate_tokens[-1], value_tokens[-1]
    if head_candidate == head_value:
        return False

    engine = _inflect_engine()
    singular = engine.singular_noun(head_candidate)
    if isinstance(singular, str) and singular.casefold() == head_value:
        return True
    plural = engine.plural(head_candidate)
    if isinstance(plural, str) and plural.casefold() == head_value:
        return is_common_word(head_value)
    return False


def number_word_forms(value: str) -> tuple[str, ...]:
    """Written-out forms of a number, for matching against question text.

    Generating the forms of a known SQL literal replaces parsing arbitrary
    number words out of the question: the parser had a ceiling and a hand-built
    vocabulary, while generation covers whatever the library covers.
    """
    try:
        number = Decimal(value)
    except (InvalidOperation, ValueError):
        return ()
    if number != number.to_integral_value():
        return ()
    if abs(number) > _MAX_GENERATED_INTEGER:
        return ()

    engine = _inflect_engine()
    integral = int(number)
    forms = {
        engine.number_to_words(integral),
        engine.number_to_words(integral, andword=""),
    }
    return tuple(sorted(form for form in forms if form))


@lru_cache(maxsize=1)
def _wordnet():
    from nltk.corpus import wordnet

    # Reading one lemma forces the lazy corpus loader to resolve now, so a
    # missing corpus surfaces here instead of on the first analyzed item.
    wordnet.lemmas("test")
    return wordnet


@lru_cache(maxsize=1)
def _function_words() -> frozenset[str]:
    from nltk.corpus import stopwords

    return frozenset(stopwords.words("english"))


@lru_cache(maxsize=1)
def _inflect_engine():
    import inflect

    return inflect.engine()


@lru_cache(maxsize=8192)
def _stem(token: str) -> str:
    return _stemmer().stem(token)


@lru_cache(maxsize=1)
def _stemmer():
    from nltk.stem import SnowballStemmer

    return SnowballStemmer("english")


@lru_cache(maxsize=8192)
def _has_lemma(token: str) -> bool:
    return bool(_wordnet().lemmas(token))


@lru_cache(maxsize=8192)
def _has_lemma_or_form(token: str) -> bool:
    if _has_lemma(token):
        return True
    base = _wordnet().morphy(token)
    return bool(base) and _has_lemma(base)


@lru_cache(maxsize=8192)
def _morphy_forms(token: str) -> frozenset[str]:
    wordnet = _wordnet()
    forms = {token}
    for pos in (
        wordnet.NOUN,
        wordnet.VERB,
        wordnet.ADJ,
        wordnet.ADV,
    ):
        base = wordnet.morphy(token, pos)
        if base:
            forms.add(fold(base))
    return frozenset(forms)


@lru_cache(maxsize=8192)
def _pertainym_names(token: str) -> frozenset[str]:
    return frozenset(
        fold(related.name())
        for lemma in _wordnet().lemmas(token)
        for related in lemma.pertainyms()
    )


@lru_cache(maxsize=8192)
def _derivational_names(token: str) -> frozenset[str]:
    return frozenset(
        fold(related.name())
        for lemma in _wordnet().lemmas(token)
        for related in lemma.derivationally_related_forms()
    )


@lru_cache(maxsize=8192)
def _has_common_lemma(token: str) -> bool:
    return any(lemma.name()[:1].islower() for lemma in _wordnet().lemmas(token))


@lru_cache(maxsize=8192)
def _is_common_lemma_or_form(token: str) -> bool:
    if _has_common_lemma(token):
        return True
    base = _wordnet().morphy(token)
    return bool(base) and _has_common_lemma(base)


def _alpha_tokens(text: str) -> list[str]:
    return [token for token in fold(text).split() if token.isalpha()]


def _missing_corpus(message: str) -> str | None:
    match = re.search(r"corpora/(\w+)", message)
    return match.group(1) if match else None
