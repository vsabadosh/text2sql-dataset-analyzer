
def import_builtin_plugins() -> None:
    # LOADERS
    import text2sql_pipeline.loaders.jsonl_loader
    import text2sql_pipeline.loaders.json_loader
    import text2sql_pipeline.loaders.csv_loader
    import text2sql_pipeline.loaders.hf_loader

    # NORMALIZERS
    import text2sql_pipeline.normalizers.alias_mapper
    import text2sql_pipeline.normalizers.id_assign
    import text2sql_pipeline.normalizers.db_identity_assign

    # ANALYZERS
    import text2sql_pipeline.analyzers.schema_validation.schema_analysis_annot
    import text2sql_pipeline.analyzers.query_syntax.query_syntax_annot
    import text2sql_pipeline.analyzers.query_execution.query_execution_annot
    import text2sql_pipeline.analyzers.query_antipattern.query_antipattern_annot
    import text2sql_pipeline.analyzers.llm_as_a_judge.semantic_llm_annot

    # ADAPTERS
    import text2sql_pipeline.db.adapters.sqlite_sa
    import text2sql_pipeline.db.adapters.postgres_sa