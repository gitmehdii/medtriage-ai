from datetime import date, datetime, timezone
from typing import Any, Literal

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, field_validator, model_validator

from medical_knowledge_mcp.config import get_settings


SUPPORTED_COUNTRIES = frozenset(
    "AD AE AF AG AI AL AM AO AQ AR AS AT AU AW AX AZ BA BB BD BE BF BG BH BI BJ BL BM BN BO BQ BR BS BT BV BW BY BZ CA CC CD CF CG CH CI CK CL CM CN CO CR CU CV CW CX CY CZ DE DJ DK DM DO DZ EC EE EG EH ER ES ET FI FJ FK FM FO FR GA GB GD GE GF GG GH GI GL GM GN GP GQ GR GS GT GU GW GY HK HM HN HR HT HU ID IE IL IM IN IO IQ IR IS IT JE JM JO JP KE KG KH KI KM KN KP KR KW KY KZ LA LB LC LI LK LR LS LT LU LV LY MA MC MD ME MF MG MH MK ML MM MN MO MP MQ MR MS MT MU MV MW MX MY MZ NA NC NE NF NG NI NL NO NP NR NU NZ OM PA PE PF PG PH PK PL PM PN PR PS PT PW PY QA RE RO RS RU RW SA SB SC SD SE SG SH SI SJ SK SL SM SN SO SR SS ST SV SX SY SZ TC TD TF TG TH TJ TK TL TM TN TO TR TT TV TW TZ UA UG UM US UY UZ VA VC VE VG VI VN VU WF WS YE YT ZA ZM ZW".split()
)
ALLOWED_SOURCE_DOMAINS = frozenset({"has-sante.fr", "sante.gouv.fr", "ameli.fr", "who.int", "nhs.uk"})


def _validate_country(value: str) -> str:
    value = value.upper()
    if value not in SUPPORTED_COUNTRIES:
        raise ValueError("country must be a valid ISO 3166-1 alpha-2 code")
    return value


def _allowed_source_domains() -> frozenset[str]:
    configured_domains = {
        domain.lower().rstrip(".")
        for domain in get_settings().allowed_domains
        if domain.strip()
    }
    return frozenset(configured_domains) or ALLOWED_SOURCE_DOMAINS


def _validate_official_url(value: AnyHttpUrl) -> AnyHttpUrl:
    if value.scheme != "https":
        raise ValueError("source URL must use HTTPS")
    hostname = (value.host or "").lower().rstrip(".")
    if not any(hostname == domain or hostname.endswith(f".{domain}") for domain in _allowed_source_domains()):
        raise ValueError("source URL domain is not allow-listed")
    return value


class SourceRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    organization: str = Field(min_length=1)
    country: str
    speciality: str = Field(min_length=1)
    url: AnyHttpUrl
    publication_date: date
    last_update_date: date
    last_verified_at: datetime
    content_hash: str = Field(min_length=1)
    active: bool = True

    @field_validator("country")
    @classmethod
    def validate_country(cls, value: str) -> str:
        return _validate_country(value)

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: AnyHttpUrl) -> AnyHttpUrl:
        return _validate_official_url(value)

    @model_validator(mode="after")
    def validate_dates(self):
        verified_date = self.last_verified_at.date()
        if self.last_update_date < self.publication_date:
            raise ValueError("last_update_date cannot precede publication_date")
        if verified_date < self.last_update_date:
            raise ValueError("last_verified_at cannot precede last_update_date")
        return self


class Citation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(min_length=1)
    url: AnyHttpUrl
    title: str = Field(min_length=1)
    publication_date: date
    last_update_date: date
    last_verified_at: datetime
    retrieved_at: datetime

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: AnyHttpUrl) -> AnyHttpUrl:
        return _validate_official_url(value)

    @model_validator(mode="after")
    def validate_timestamps(self):
        if self.last_verified_at > datetime.now(timezone.utc) or self.retrieved_at > datetime.now(timezone.utc):
            raise ValueError("citation timestamps cannot be in the future")
        if self.last_update_date < self.publication_date or self.last_verified_at.date() < self.last_update_date:
            raise ValueError("citation dates are not chronological")
        return self

    @model_validator(mode="after")
    def validate_dates(self):
        if self.last_update_date < self.publication_date:
            raise ValueError("last_update_date cannot precede publication_date")
        if self.last_verified_at.date() < self.last_update_date:
            raise ValueError("last_verified_at cannot precede last_update_date")
        if self.retrieved_at < self.last_verified_at:
            raise ValueError("retrieved_at cannot precede last_verified_at")
        return self


class GuidelineResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    organization: str = Field(min_length=1)
    country: str
    url: AnyHttpUrl
    publication_date: date
    last_update_date: date
    last_verified_at: datetime
    excerpt: str = Field(min_length=1)
    relevance_score: float = Field(ge=0, le=1)
    citation: Citation
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("country")
    @classmethod
    def validate_country(cls, value: str) -> str:
        return _validate_country(value)

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: AnyHttpUrl) -> AnyHttpUrl:
        return _validate_official_url(value)

    @model_validator(mode="after")
    def validate_timestamps(self):
        if self.last_verified_at > datetime.now(timezone.utc) or self.retrieved_at > datetime.now(timezone.utc):
            raise ValueError("guideline timestamps cannot be in the future")
        if self.last_update_date < self.publication_date or self.last_verified_at.date() < self.last_update_date:
            raise ValueError("guideline dates are not chronological")
        return self

    @model_validator(mode="after")
    def validate_dates(self):
        if self.last_update_date < self.publication_date:
            raise ValueError("last_update_date cannot precede publication_date")
        if self.last_verified_at.date() < self.last_update_date:
            raise ValueError("last_verified_at cannot precede last_update_date")
        if self.retrieved_at < self.last_verified_at:
            raise ValueError("retrieved_at cannot precede last_verified_at")
        return self


class RedFlag(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symptom: str = Field(min_length=1)
    country: str
    severity: str = Field(pattern="^(low|medium|high|critical)$")
    action: str = Field(min_length=1)
    evidence_excerpt: str = Field(min_length=1)
    citation: Citation

    @field_validator("country")
    @classmethod
    def validate_country(cls, value: str) -> str:
        return _validate_country(value)


class SearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1)
    speciality: str | None = None
    country: str = "FR"
    limit: int = Field(default=5, ge=1, le=50)

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("query must not be blank")
        return value

    @field_validator("country")
    @classmethod
    def validate_country(cls, value: str) -> str:
        return _validate_country(value)


class KnowledgeError(BaseModel):
    code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    ok: Literal[False] = False
    error: KnowledgeError


StructuredError = KnowledgeError
ErrorEnvelope = ErrorResponse
