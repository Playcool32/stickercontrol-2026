from pydantic import BaseModel


class GoogleLoginRequest(BaseModel):
    """Credential (ID token JWT) entregado por Google Identity Services."""

    credential: str


class UserOut(BaseModel):
    id: int
    email: str
    name: str
    avatar: str | None


class StickerOut(BaseModel):
    """Figurita del catalogo + estado de coleccion del usuario actual."""

    id: int
    code: str
    group: str | None
    country_code: str
    country_name: str
    number: int
    player_name_or_detail: str
    type: str

    quantity: int
    is_pasted: bool
    notes: str | None
    status: str
    repetidas: int


class StickerSearchResponse(BaseModel):
    total: int
    items: list[StickerOut]


class NotesUpdate(BaseModel):
    notes: str | None = None


class CountrySummary(BaseModel):
    total: int
    pegadas: int
    faltantes: int
    repetidas: int
    porcentaje: float


class AlbumCountry(BaseModel):
    country_code: str
    country_name: str
    group: str | None
    flag: str | None
    stickers: list[StickerOut]
    summary: CountrySummary


class AlbumGroup(BaseModel):
    group: str
    countries: list[AlbumCountry]


class AlbumResponse(BaseModel):
    groups: list[AlbumGroup]
    special: list[AlbumCountry]


class MissingCountry(BaseModel):
    country_code: str
    country_name: str
    numbers: list[int]


class MissingResponse(BaseModel):
    by_country: list[MissingCountry]
    text: str


class DuplicateItem(BaseModel):
    number: int
    quantity: int


class DuplicateCountry(BaseModel):
    country_code: str
    country_name: str
    items: list[DuplicateItem]


class DuplicatesResponse(BaseModel):
    by_country: list[DuplicateCountry]
    text: str


class ProfileOut(BaseModel):
    id: int
    email: str
    name: str
    display_name: str | None
    city: str | None
    latitude: float | None
    longitude: float | None
    contact_email: str | None
    contact_whatsapp: str | None
    is_public: bool


class ProfileUpdate(BaseModel):
    display_name: str | None = None
    city: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    contact_email: str | None = None
    contact_whatsapp: str | None = None
    is_public: bool | None = None


class NearbyUser(BaseModel):
    user_id: int
    display_name: str
    city: str | None
    distance_km: float | None
    stickers_i_need_that_user_has: list[str]
    stickers_user_needs_that_i_have: list[str]
    match_count: int
    has_email: bool
    has_whatsapp: bool


class NearbyResponse(BaseModel):
    users: list[NearbyUser]


class ContactMessageResponse(BaseModel):
    text: str
    whatsapp_url: str | None
    mailto_url: str | None
