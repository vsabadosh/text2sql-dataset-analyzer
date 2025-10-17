# pipeline/container.py
from typing import Any, Dict, List
from dependency_injector import containers, providers

from .pipeline.registry import get_class
from .db.adapters.factory import make_adapter
from .db.adapters.base.schema_identity import SchemaIdentity
from .db.manager import DbManager


class PipelineContainer(containers.DeclarativeContainer):
    """
    Wires components from config using automatic dependency injection.
    
    Components declare their dependencies via INJECT class attribute:
        INJECT = ["db_manager"]  # Inject DbManager
        INJECT = ["dialect"]     # Inject SQL dialect string
    
    No hardcoding required - container checks INJECT attribute automatically.
    """

    # Providers placeholders
    loader            = providers.Provider()
    normalizers_chain = providers.List()
    analyzers_chain   = providers.List()
    driver            = providers.Provider()

    def wire_from_config(self, cfg: Dict[str, Any]) -> None:
        # Helper function to build provider with INJECT support
        def build_provider(ComponentCls: type, params: Dict[str, Any], db_manager_prov):
            """Build a provider with automatic dependency injection based on INJECT attribute."""
            inject_list = getattr(ComponentCls, 'INJECT', [])
            kwargs = dict(params)
            
            for inject_item in inject_list:
                if inject_item == "db_manager":
                    kwargs["db_manager"] = db_manager_prov
            
            return providers.Singleton(ComponentCls, **kwargs)
        
        # ---------- Source DB (new shape) ----------
        sdbcfg   = cfg.get("sourceDb") or {}
        dialect  = (sdbcfg.get("dialect") or "sqlite").strip().lower()
        kind     = (sdbcfg.get("kind") or ("file" if dialect == "sqlite" else "server")).strip().lower()
        endpoint = sdbcfg.get("endpoint")
        if not endpoint:
            raise ValueError("sourceDb.endpoint is required")

        # Adapter + DbManager
        schema_identity = providers.Factory(SchemaIdentity)
        adapter = providers.Singleton(
            make_adapter,
            dialect=dialect,
            kind=kind,
            endpoint=endpoint,
            identity=schema_identity,
        )
        db_manager = providers.Singleton(DbManager, adapter=adapter)

        # ---------- Loader ----------
        lcfg    = cfg.get("load") or {}
        lname   = lcfg.get("name")
        lparams = lcfg.get("params") or {}
        if not lname:
            raise ValueError("config.load.name is required")
        LoaderCls = get_class("loader", lname)
        self.loader = build_provider(LoaderCls, lparams, db_manager)

        # ---------- Normalizers chain ----------
        n_specs = cfg.get("normalize") or []
        n_provs: List[providers.Provider] = []
        for spec in n_specs:
            name = spec.get("name")
            if not name:
                raise ValueError("normalize item must have name")
            params = dict(spec.get("params") or {})
            NormalizerCls = get_class("normalizer", name)
            n_provs.append(build_provider(NormalizerCls, params, db_manager))

        self.normalizers_chain = providers.List(*n_provs)

        # ---------- Analyzers chain ----------
        a_specs = cfg.get("analyze") or []
        a_provs: List[providers.Provider] = []
        for spec in a_specs:
            name = spec.get("name")
            if not name:
                raise ValueError("analyze item must have name")
            params = dict(spec.get("params") or {})
            AnalyzerCls = get_class("analyzer", name)
            a_provs.append(build_provider(AnalyzerCls, params, db_manager))

        self.analyzers_chain = providers.List(*a_provs)
