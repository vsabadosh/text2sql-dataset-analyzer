"""
Tests for the question-SQL consistency report.
"""
import json
import os
import tempfile
from pathlib import Path

import pytest

from text2sql_pipeline.analyzers.question_sql_consistency.question_sql_consistency_analyzer import (
    QuestionSqlConsistencyAnalyzer,
)
from text2sql_pipeline.core.models import DataItem
from text2sql_pipeline.output.report import MarkdownReportGenerator
from text2sql_pipeline.output.sinks.duckdb import DuckDBMetricsSink


class StubDbManager:
    def get_sqlglot_dialect(self) -> str:
        return "sqlite"


# Spider train 640/641 and 2579/2580: paraphrase pairs whose gold SQL is
# identical, so the clean twin settles the disputed literal from inside the
# dataset. Item 13 contributes an unlicensed obligation, item 42 a clean one.
ITEMS = [
    (
        "640",
        "store_1",
        "List all tracks bought by customer Daan Peeters.",
        'SELECT name FROM customers WHERE first_name = "Daan" AND last_name = "Peeters"',
    ),
    (
        "641",
        "store_1",
        "What are the tracks that Dean Peeters bought?",
        'SELECT name FROM customers WHERE first_name = "Daan" AND last_name = "Peeters"',
    ),
    (
        "2579",
        "inn_1",
        "How many kids stay in the rooms reserved by ROY SWEAZY?",
        'SELECT kids FROM Reservations WHERE FirstName = "ROY" AND LastName = "SWEAZY"',
    ),
    (
        "2580",
        "inn_1",
        "Find the number of kids staying in the rooms reserved by a person called ROY SWEAZ.",
        'SELECT kids FROM Reservations WHERE FirstName = "ROY" AND LastName = "SWEAZY"',
    ),
    # Spider test 1570/1571: the twin writes the literal in the plural. Asking
    # for the exact spelling filed the typo as an anomalous SQL value, when the
    # twin in fact proves the question is at fault.
    (
        "1570",
        "bakery_1",
        "What are the ids of Cookies whose price is lower than any Croissant?",
        'SELECT id FROM goods WHERE food = "Cookie" AND price < '
        "(SELECT min(price) FROM goods WHERE food = 'Croissant')",
    ),
    (
        "1571",
        "bakery_1",
        "Give the ids of cookes that are cheaper than any croissant.",
        'SELECT id FROM goods WHERE food = "Cookie" AND price < '
        "(SELECT min(price) FROM goods WHERE food = 'Croissant')",
    ),
    (
        "13",
        "department_management",
        "What are the distinct ages of the heads who are acting?",
        "SELECT age FROM head WHERE temporary_acting = 'Yes'",
    ),
    (
        "42",
        "store_1",
        "Which staff are in Sales?",
        "SELECT * FROM staff WHERE dept = 'Sales'",
    ),
    (
        "766",
        "address_1",
        "How many countries do we have?",
        "SELECT count(DISTINCT country) FROM City",
    ),
    (
        "767",
        "address_1",
        "Count the number of coutries.",
        "SELECT count(DISTINCT country) FROM City",
    ),
    (
        "1855",
        "planet_1",
        "Who received the heaviest package?",
        "SELECT recipient FROM package ORDER BY weight DESC LIMIT 1",
    ),
    (
        "1856",
        "planet_1",
        "Who receieved the heaviest package?",
        "SELECT recipient FROM package ORDER BY weight DESC LIMIT 1",
    ),
]


@pytest.fixture
def populated_db():
    """A metrics file plus the dataset the report reads provenance from."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "metrics.duckdb")

        dataset = Path(tmpdir) / MarkdownReportGenerator.ANNOTATED_DATASET
        with dataset.open("w", encoding="utf-8") as handle:
            for item_id, _, question, sql in ITEMS:
                handle.write(
                    json.dumps({"id": item_id, "question": question, "sql": sql}) + "\n"
                )

        items = [
            DataItem(id=item_id, dbId=db_id, question=question, sql=sql)
            for item_id, db_id, question, sql in ITEMS
        ]
        sink = DuckDBMetricsSink(db_path)
        list(
            QuestionSqlConsistencyAnalyzer(StubDbManager()).analyze(
                items, sink, "fixture"
            )
        )
        sink.close()
        yield tmpdir, db_path


@pytest.fixture
def corpus_discriminator_db():
    rows = [
        (
            "1",
            "art_1",
            "In what year was the artist who created a painting in 1884 born?",
            "SELECT birthYear FROM artist WHERE mediumOn = 'canvas'",
        ),
        (
            "2",
            "art_1",
            "List paintings on canvas.",
            "SELECT id FROM artist WHERE mediumOn = 'canvas'",
        ),
        (
            "3",
            "art_1",
            "Which canvas paintings are recorded?",
            "SELECT id FROM artist WHERE mediumOn = 'canvas'",
        ),
        (
            "4",
            "art_1",
            "Count paintings whose medium is canvas.",
            "SELECT count(*) FROM artist WHERE mediumOn = 'canvas'",
        ),
        (
            "5",
            "geo",
            "List all major cities.",
            "SELECT name FROM city WHERE population > 150000",
        ),
        (
            "6",
            "geo",
            "Which major cities are recorded?",
            "SELECT name FROM city WHERE population > 150000",
        ),
        (
            "7",
            "collection",
            "Which collection has the most documents?",
            (
                "SELECT collection_id, count(*) FROM collection "
                "WHERE name = 'Best' GROUP BY collection_id "
                "ORDER BY count(*) DESC LIMIT 1"
            ),
        ),
        (
            "8",
            "collection",
            "For the collection named Best, count its documents.",
            (
                "SELECT collection_id, count(*) FROM collection "
                "WHERE name = 'Best' GROUP BY collection_id "
                "ORDER BY count(*) DESC LIMIT 1"
            ),
        ),
        (
            "9",
            "collection",
            "Show the id of the Best collection.",
            "SELECT collection_id FROM collection WHERE name = 'Best'",
        ),
        (
            "10",
            "collection",
            "How many documents belong to Best?",
            (
                "SELECT count(*) FROM collection WHERE name = 'Best' "
                "GROUP BY collection_id"
            ),
        ),
        (
            "11",
            "shared_columns",
            "Show all users.",
            "SELECT id FROM users WHERE status = 'paid'",
        ),
        (
            "12",
            "shared_columns",
            "Show paid orders.",
            "SELECT id FROM orders WHERE status = 'paid'",
        ),
        (
            "13",
            "shared_columns",
            "Count paid orders.",
            "SELECT count(*) FROM orders WHERE status = 'paid'",
        ),
        (
            "14",
            "shared_columns",
            "List every paid order.",
            "SELECT id FROM orders WHERE status = 'paid'",
        ),
    ]
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "metrics.duckdb")
        dataset = Path(tmpdir) / MarkdownReportGenerator.ANNOTATED_DATASET
        with dataset.open("w", encoding="utf-8") as handle:
            for item_id, _, question, sql in rows:
                handle.write(
                    json.dumps({"id": item_id, "question": question, "sql": sql})
                    + "\n"
                )
        sink = DuckDBMetricsSink(db_path)
        items = [
            DataItem(id=item_id, dbId=db_id, question=question, sql=sql)
            for item_id, db_id, question, sql in rows
        ]
        list(
            QuestionSqlConsistencyAnalyzer(StubDbManager()).analyze(
                items, sink, "fixture"
            )
        )
        sink.close()
        yield tmpdir, db_path


def _report(tmpdir, db_path) -> str:
    path = os.path.join(tmpdir, "consistency.md")
    generator = MarkdownReportGenerator(db_path)
    generator.generate_question_sql_consistency_report(path)
    generator.close()
    return Path(path).read_text()


def test_report_summarises_verdicts(populated_db):
    report = _report(*populated_db)
    assert "# Question-SQL Consistency Report" in report
    assert "## Run Provenance" in report
    assert "**Analyzer:** `0.7.0`" in report
    assert "`comparison_boundary_alignment`" in report
    assert "`boundary_lexicon=1.1.0`" in report
    assert "`wordnet=" in report
    assert "**Total Items:** 12" in report
    assert "**Items With Contradictions:** 4" in report
    assert "| literal_alignment |" in report
    assert "| LITERAL_EXPLICITLY_LICENSED | SUPPORTED |" in report


def test_report_rejects_mixed_analyzer_provenance(populated_db):
    tmpdir, db_path = populated_db
    import duckdb

    conn = duckdb.connect(db_path)
    try:
        conn.execute(
            """
            UPDATE metrics_question_sql_consistency
            SET analyzer_version = '0.0.0'
            WHERE item_id = '640'
            """
        )
    finally:
        conn.close()

    report = _report(tmpdir, db_path)
    assert "Mixed question-SQL consistency provenance" in report
    assert "## Summary" not in report


def test_report_lists_contradictions_with_provenance(populated_db):
    report = _report(*populated_db)
    assert "## Contradictions (4)" in report
    assert "NEAR_MISS_LITERAL_MISMATCH" in report
    # The question value, the SQL predicate and the question text all travel
    # with the finding, so a reader can audit it without opening the dataset.
    assert "Dean" in report
    assert 'first_name = "Daan"' in report
    assert "What are the tracks that Dean Peeters bought?" in report


def test_report_treats_same_sql_peers_as_corroboration_not_ground_truth(
    populated_db,
):
    report = _report(*populated_db)
    assert "### Peer-Corroborated Question-Side Candidates (3)" in report
    assert "identical SQL alone does not prove" in report
    assert "List all tracks bought by customer Daan Peeters." in report
    assert "How many kids stay in the rooms reserved by ROY SWEAZY?" in report


def test_a_twin_confirms_through_the_plural_of_the_literal(populated_db):
    """A twin writing "Cookies" settles a predicate on 'Cookie'."""
    report = _report(*populated_db)
    assert "### Anomalous SQL Literals" not in report
    assert "What are the ids of Cookies whose price is lower than any Croissant?" in (
        report
    )


def test_twin_licensing_reuses_detector_abbreviation_guards():
    assert MarkdownReportGenerator._licenses_literal(
        "Show papers affiliated with Stanford.",
        "Stanford University",
    )
    assert not MarkdownReportGenerator._licenses_literal(
        "Show papers reviewed by Britanny Harris.",
        "Brittany Harris",
    )


def test_report_separates_identifier_proof_from_identical_sql_peer_signal(
    populated_db,
):
    report = _report(*populated_db)

    assert "## Question Lexical Integrity (2)" in report
    assert "**SQL identifier evidence:** 1" in report
    assert "**Identical-SQL peer candidates:** 2" in report
    assert "**Identifier findings with peer support:** 1" in report
    assert (
        "| 767 | address_1 | coutries | countries | SQL identifier + peer | "
        "country | 766 |"
    ) in report
    assert (
        "| 1856 | planet_1 | receieved | received | Identical-SQL peer | — | 1855 |"
        in report
    )


def test_report_records_declared_assumptions(populated_db):
    report = _report(*populated_db)
    assert "## Declared Assumptions" in report
    assert "NEAR_MISS_SIBLING_ADJACENCY" in report
    assert "SQLITE_DQS_STRING_FALLBACK" in report


def test_report_applies_corpus_discriminators_with_hidden_support(
    corpus_discriminator_db,
):
    report = _report(*corpus_discriminator_db)

    assert "### Corpus-Confirmed Unrequested Filters (2)" in report
    assert "| 1 | art_1 | artist | mediumon | EQ | canvas | 3 |" in report
    assert "| 7 | collection | collection | name | EQ | Best | 3 |" in report
    assert "| geo | city | population | GT | 150000 | 2 | 1 |" in report
    assert "| shared_columns | users | status | EQ | paid | 1 | 0 | unresolved |" in report
    assert "stable benchmark convention" in report


def test_report_counts_dataset_evidence_only_licenses():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "metrics.duckdb")
        item = DataItem(
            id="1",
            dbId="fixture",
            question="Show active customers.",
            sql="SELECT id FROM customer WHERE status = 'PAID'",
            metadata={"evidence": "active means status PAID"},
        )
        dataset = Path(tmpdir) / MarkdownReportGenerator.ANNOTATED_DATASET
        dataset.write_text(
            json.dumps(
                {"id": "1", "question": item.question, "sql": item.sql}
            )
            + "\n",
            encoding="utf-8",
        )
        sink = DuckDBMetricsSink(db_path)
        analyzer = QuestionSqlConsistencyAnalyzer(
            StubDbManager(),
            context={"evidence_keys": ["evidence"]},
        )
        list(analyzer.analyze([item], sink, "fixture"))
        sink.close()

        report = _report(tmpdir, db_path)

    assert "## Evidence Licensing Axis" in report
    assert "| All literals | 1 | 0 | 1 | 1 (100.0%) | 0 |" in report


def test_report_separates_unresolved_from_contradicted(populated_db):
    report = _report(*populated_db)
    assert "## Unresolved Obligations (1)" in report
    assert "SQL_LITERAL_UNLICENSED" in report
    assert "temporary_acting = 'Yes'" in report


def test_report_without_metrics_says_so():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "metrics.duckdb")
        DuckDBMetricsSink(db_path).close()
        report = _report(tmpdir, db_path)
    assert "No question-SQL consistency metrics available." in report
