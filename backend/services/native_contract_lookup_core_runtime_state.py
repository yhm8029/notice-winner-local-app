from __future__ import annotations

import os
import threading
from dataclasses import dataclass
from dataclasses import field
from dataclasses import replace


def _env_int(name: str, default: int) -> int:
    raw = str(os.getenv(name) or "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except Exception:
        return default


def _env_float(name: str, default: float) -> float:
    raw = str(os.getenv(name) or "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except Exception:
        return default


G2B_CONTRACT_ENDPOINTS: list[tuple[str, str, str]] = [
    ("Servc", "https://apis.data.go.kr/1230000/ao/CntrctInfoService/getCntrctInfoListServc", "cntrctNm"),
    ("ServcPPSSrch", "https://apis.data.go.kr/1230000/ao/CntrctInfoService/getCntrctInfoListServcPPSSrch", "cntrctNm"),
    ("Cnstwk", "https://apis.data.go.kr/1230000/ao/CntrctInfoService/getCntrctInfoListCnstwk", "cnstwkNm"),
    ("CnstwkPPSSrch", "https://apis.data.go.kr/1230000/ao/CntrctInfoService/getCntrctInfoListCnstwkPPSSrch", "cnstwkNm"),
]
LOFIN_CONTRACT_OPENAPI_URL = "https://www.lofin365.go.kr/lf/hub/WCEGCF"
HUB_LIST_URL = "https://www.hub.go.kr/portal/dps/dsr/idx-dsr-selectDesignPbpPbancList.do"
HUB_AWARD_LIST_URL = "https://www.hub.go.kr/portal/dps/dpr/idx-dpr-designPbpPrwinPdtList.do"
HUB_RESULT_TAB_NO = "4"
HUB_RESULT_SCHDL_SN = "2"
HUB_MAX_SEARCH_RESULTS = 5
LOFIN_OPENAPI_KEY_ENV_NAMES = (
    "LOFIN_OPENAPI_KEY",
    "LOFIN_API_KEY",
    "LOFIN_KEY",
)
EAIS_BASE_URL = "https://www.eais.go.kr"
EAIS_LIST_API_URL = f"{EAIS_BASE_URL}/awp/AWPAIA01R02"
EAIS_DETAIL_API_URL = f"{EAIS_BASE_URL}/awp/AWPAIA01R03"
EAIS_PARTICIPANT_API_URL = f"{EAIS_BASE_URL}/awp/AWPAIA01R05"
EAIS_LIST_REFERER = f"{EAIS_BASE_URL}/moct/awp/aia01/AWPAIA01L04"
EAIS_VIEW_REFERER = f"{EAIS_BASE_URL}/moct/awp/aia01/AWPAIA01V01"

LOFIN_DATE_SWEEP_MAX_WORKERS = max(1, _env_int("WINNER_PIPELINE_LOFIN_DATE_SWEEP_WORKERS", 3))
LOFIN_GLOBAL_MAX_CONCURRENCY = max(1, _env_int("WINNER_PIPELINE_LOFIN_GLOBAL_MAX_CONCURRENCY", 4))
EAIS_LIST_MAX_WORKERS = max(1, _env_int("WINNER_PIPELINE_EAIS_LIST_WORKERS", 3))
LOFIN_TOTAL_SWEEP_TIMEOUT_SEC = max(5.0, _env_float("WINNER_PIPELINE_LOFIN_TOTAL_SWEEP_TIMEOUT_SEC", 30.0))
_LOFIN_GLOBAL_SEMAPHORE = threading.BoundedSemaphore(LOFIN_GLOBAL_MAX_CONCURRENCY)
LOFIN_CONTRACT_KIND_NAME = "용역"


@dataclass(frozen=True)
class ContractLookupResult:
    contract_name: str = ""
    contract_date: str = ""
    contract_amount: str = ""
    target_name: str = ""
    inst_name: str = ""
    dept_name: str = ""
    officer_name: str = ""
    officer_tel: str = ""
    contract_period_text: str = ""
    contract_duration_days: int = 0
    site_name: str = ""
    match_score: float = 0.0
    source_type: str = "g2b_contract_api"


@dataclass(frozen=True)
class ContractLookupMeta:
    contract_lookup_path: str = "no_hit"
    query_sweep_used: bool = False
    query_sweep_hit: bool = False
    lofin_date_workers: int = 0
    lofin_global_semaphore_limit: int = 0
    lofin_powershell_used: bool = False
    lofin_ssl_fallback_used: bool = False
    lofin_dates_examined: int = 0
    lofin_requests_total: int = 0
    lofin_pages_fetched_total: int = 0
    lofin_timeout_count: int = 0
    lofin_first_nonempty_date: str = ""
    lofin_hit_date: str = ""
    lofin_best_score: float = 0.0
    lofin_max_active_requests: int = 0
    lofin_budget_seconds: float = 0.0
    lofin_budget_exhausted: bool = False


@dataclass
class _LofinRuntimeStats:
    date_workers: int = 0
    semaphore_limit: int = 0
    powershell_used: bool = False
    ssl_fallback_used: bool = False
    dates_examined: int = 0
    requests_total: int = 0
    pages_fetched_total: int = 0
    timeout_count: int = 0
    first_nonempty_date: str = ""
    hit_date: str = ""
    best_score: float = 0.0
    max_active_requests: int = 0
    budget_seconds: float = 0.0
    budget_exhausted: bool = False
    _active_requests: int = 0
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def begin_request(self) -> None:
        with self._lock:
            self._active_requests += 1
            if self._active_requests > self.max_active_requests:
                self.max_active_requests = self._active_requests

    def end_request(self) -> None:
        with self._lock:
            if self._active_requests > 0:
                self._active_requests -= 1

    def note_request(self) -> None:
        with self._lock:
            self.requests_total += 1

    def note_page_fetched(self) -> None:
        with self._lock:
            self.pages_fetched_total += 1

    def note_powershell_used(self) -> None:
        with self._lock:
            self.powershell_used = True

    def note_ssl_fallback_used(self) -> None:
        with self._lock:
            self.ssl_fallback_used = True

    def note_timeout(self) -> None:
        with self._lock:
            self.timeout_count += 1

    def note_dates_examined(self, count: int) -> None:
        with self._lock:
            self.dates_examined += max(0, int(count))

    def note_nonempty_date(self, date_hint: str) -> None:
        value = str(date_hint or "").strip()
        if not value:
            return
        with self._lock:
            if not self.first_nonempty_date:
                self.first_nonempty_date = value

    def note_hit(self, *, date_hint: str, best_score: float) -> None:
        with self._lock:
            self.hit_date = str(date_hint or "").strip()
            self.best_score = max(0.0, float(best_score or 0.0))

    def note_best_score(self, best_score: float) -> None:
        with self._lock:
            self.best_score = max(self.best_score, max(0.0, float(best_score or 0.0)))

    def note_budget_exhausted(self) -> None:
        with self._lock:
            self.budget_exhausted = True

    def to_meta(self) -> ContractLookupMeta:
        return ContractLookupMeta(
            lofin_date_workers=self.date_workers,
            lofin_global_semaphore_limit=self.semaphore_limit,
            lofin_powershell_used=self.powershell_used,
            lofin_ssl_fallback_used=self.ssl_fallback_used,
            lofin_dates_examined=self.dates_examined,
            lofin_requests_total=self.requests_total,
            lofin_pages_fetched_total=self.pages_fetched_total,
            lofin_timeout_count=self.timeout_count,
            lofin_first_nonempty_date=self.first_nonempty_date,
            lofin_hit_date=self.hit_date,
            lofin_best_score=self.best_score,
            lofin_max_active_requests=self.max_active_requests,
            lofin_budget_seconds=self.budget_seconds,
            lofin_budget_exhausted=self.budget_exhausted,
        )


_LOOKUP_META = threading.local()


def get_last_contract_lookup_meta() -> ContractLookupMeta:
    meta = getattr(_LOOKUP_META, "value", None)
    if isinstance(meta, ContractLookupMeta):
        return meta
    return ContractLookupMeta()


def _set_last_contract_lookup_meta(meta: ContractLookupMeta) -> None:
    _LOOKUP_META.value = meta


def _merge_contract_lookup_meta(
    base: ContractLookupMeta,
    *,
    extra: ContractLookupMeta | None = None,
    contract_lookup_path: str | None = None,
) -> ContractLookupMeta:
    merged = base
    if extra is not None:
        merged = replace(
            merged,
            lofin_date_workers=max(merged.lofin_date_workers, extra.lofin_date_workers),
            lofin_global_semaphore_limit=max(
                merged.lofin_global_semaphore_limit,
                extra.lofin_global_semaphore_limit,
            ),
            lofin_powershell_used=merged.lofin_powershell_used or extra.lofin_powershell_used,
            lofin_ssl_fallback_used=merged.lofin_ssl_fallback_used or extra.lofin_ssl_fallback_used,
            lofin_dates_examined=max(merged.lofin_dates_examined, extra.lofin_dates_examined),
            lofin_requests_total=max(merged.lofin_requests_total, extra.lofin_requests_total),
            lofin_pages_fetched_total=max(
                merged.lofin_pages_fetched_total,
                extra.lofin_pages_fetched_total,
            ),
            lofin_timeout_count=max(merged.lofin_timeout_count, extra.lofin_timeout_count),
            lofin_first_nonempty_date=(
                merged.lofin_first_nonempty_date or extra.lofin_first_nonempty_date
            ),
            lofin_hit_date=merged.lofin_hit_date or extra.lofin_hit_date,
            lofin_best_score=max(merged.lofin_best_score, extra.lofin_best_score),
            lofin_max_active_requests=max(
                merged.lofin_max_active_requests,
                extra.lofin_max_active_requests,
            ),
            lofin_budget_seconds=max(merged.lofin_budget_seconds, extra.lofin_budget_seconds),
            lofin_budget_exhausted=merged.lofin_budget_exhausted or extra.lofin_budget_exhausted,
        )
    if contract_lookup_path is not None:
        merged = replace(merged, contract_lookup_path=contract_lookup_path)
    return merged
