from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import re
import unicodedata

from .lexical_resources import is_inflectional_variant, number_word_forms
from .metrics import TextSpan


_TOKEN_RE = re.compile(
    r"\d{4}[-/]\d{1,2}[-/]\d{1,2}"
    r"|[-+]?\d+(?:[.,]\d+)?"
    r"|[^\W\d_]+(?:['’][^\W\d_]+)*",
    re.UNICODE,
)
# A single quote only opens a quoted value when it does not sit inside a word:
# English possessives ("the owner's name") would otherwise pair up across the
# sentence and invent a quoted value that nobody wrote.
_QUOTED_RE = re.compile(
    r"[\"“”](?P<double>[^\"“”]+)[\"“”]"
    r"|(?<![\w'‘’])['‘’](?P<single>[^'‘’]+)['‘’](?!\w)"
)


@dataclass(frozen=True)
class QuestionToken:
    text: str
    normalized: str
    start: int
    end: int


@dataclass(frozen=True)
class NormalizedQuestion:
    original: str
    normalized: str
    tokens: tuple[QuestionToken, ...]


def normalize_text(value: str) -> str:
    text = unicodedata.normalize("NFC", value)
    text = text.translate(
        str.maketrans(
            {
                "’": "'",
                "‘": "'",
                "“": '"',
                "”": '"',
                "\u00a0": " ",
            }
        )
    )
    return " ".join(text.casefold().split())


def _normalize_token(value: str) -> str:
    normalized = normalize_text(value)
    numeric = normalized.replace(",", ".")
    try:
        decimal = Decimal(numeric)
    except InvalidOperation:
        return normalized

    if decimal == decimal.to_integral_value():
        return str(decimal.to_integral_value())
    return format(decimal.normalize(), "f")


def normalize_question(text: str) -> NormalizedQuestion:
    tokens = tuple(
        QuestionToken(
            text=match.group(0),
            normalized=_normalize_token(match.group(0)),
            start=match.start(),
            end=match.end(),
        )
        for match in _TOKEN_RE.finditer(text)
    )
    return NormalizedQuestion(
        original=text,
        normalized=normalize_text(text),
        tokens=tokens,
    )


def value_tokens(value: str) -> tuple[str, ...]:
    return tuple(
        _normalize_token(match.group(0)) for match in _TOKEN_RE.finditer(value)
    )


def find_exact_spans(
    question: NormalizedQuestion,
    value: str,
) -> list[TextSpan]:
    wanted = value_tokens(value)
    if not wanted or len(wanted) > len(question.tokens):
        return []

    spans: list[TextSpan] = []
    width = len(wanted)
    for start_index in range(len(question.tokens) - width + 1):
        candidate = question.tokens[start_index : start_index + width]
        candidate_values = tuple(token.normalized for token in candidate)
        if not _token_sequence_matches(candidate_values, wanted):
            continue
        start = candidate[0].start
        end = candidate[-1].end
        spans.append(
            TextSpan(
                text=question.original[start:end],
                normalized=" ".join(wanted),
                start=start,
                end=end,
            )
        )
    return spans


def _token_sequence_matches(
    candidate: tuple[str, ...],
    wanted: tuple[str, ...],
) -> bool:
    if candidate == wanted:
        return True
    if len(candidate) != len(wanted) or candidate[:-1] != wanted[:-1]:
        return False

    # English possessive morphology does not change the referenced value.
    # Keep this explicit and narrow; general stemming/fuzzy matching is outside
    # the deterministic MVP. A trailing bare apostrophe ("Peeters'") never
    # survives tokenization, so only the "'s" form needs handling here.
    return candidate[-1] == f"{wanted[-1]}'s"


def find_inflected_spans(
    question: NormalizedQuestion,
    value: str,
) -> list[TextSpan]:
    """Locate the value written in a different grammatical number.

    A question asking about "cakes" does name the stored value 'Cake', and
    treating that as unlicensed accounted for more than half of the unresolved
    obligations measured on Spider test. Only number inflection counts here;
    the direction guards inside `is_inflectional_variant` keep a name typo
    ('Luca' against 'Lucas') from licensing itself and losing a contradiction.
    """
    wanted = value_tokens(value)
    if not wanted or len(wanted) > len(question.tokens):
        return []

    normalized = " ".join(wanted)
    width = len(wanted)
    spans: list[TextSpan] = []
    for start_index in range(len(question.tokens) - width + 1):
        window = question.tokens[start_index : start_index + width]
        candidate = " ".join(token.normalized for token in window)
        if not is_inflectional_variant(candidate, normalized):
            continue
        spans.append(
            TextSpan(
                text=question.original[window[0].start : window[-1].end],
                normalized=normalized,
                start=window[0].start,
                end=window[-1].end,
            )
        )
    return spans


def find_number_word_spans(
    question: NormalizedQuestion,
    value: str,
) -> list[TextSpan]:
    """Locate the SQL number written out in words, e.g. 25000 as "twenty-five
    thousand".

    Generating the forms of a value we already know and matching them as token
    sequences replaces parsing arbitrary number words out of the question. The
    old parser carried its own vocabulary and stopped at 999; generation covers
    whatever the library covers, and the exact matcher still yields the offsets
    that findings cite as provenance.
    """
    normalized = _normalize_token(value)
    spans: dict[tuple[int, int], TextSpan] = {}
    for form in number_word_forms(value):
        for span in find_exact_spans(question, form):
            spans.setdefault(
                (span.start, span.end),
                TextSpan(
                    text=span.text,
                    normalized=normalized,
                    start=span.start,
                    end=span.end,
                ),
            )
    return [spans[key] for key in sorted(spans)]


def quoted_spans(question: NormalizedQuestion) -> list[TextSpan]:
    spans: list[TextSpan] = []
    for match in _QUOTED_RE.finditer(question.original):
        text = match.group("double") or match.group("single") or ""
        start, end = (
            match.span("double")
            if match.group("double") is not None
            else match.span("single")
        )
        spans.append(
            TextSpan(
                text=text,
                normalized=normalize_text(text),
                start=start,
                end=end,
            )
        )
    return spans
