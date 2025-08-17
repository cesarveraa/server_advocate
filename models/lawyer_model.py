# models.py
from pydantic import BaseModel
from typing import List, Dict, Literal, Optional

# ── Settings ────────────────────────────────────────────────────────────────
class Settings(BaseModel):
    theme: Literal["light", "dark", "auto"]
    enableDarkModeToggle: bool
    defaultLanguage: Literal["es", "en"]
    languages: List[Literal["es", "en"]]
    entityType: Literal["firm", "person"]

# ── Styling ────────────────────────────────────────────────────────────────
class StylingTheme(BaseModel):
    primaryColor: str
    secondaryColor: str
    backgroundColor: str
    textPrimary: str
    textSecondary: str
    borderColor: str
    cardBackground: str
    footerBackground: str
    footerText: str

class Styling(BaseModel):
    light: StylingTheme
    dark: StylingTheme
    fontFamily: str
    fontSize: Dict[str, str]

# ── Analytics ──────────────────────────────────────────────────────────────
class PageClicks(BaseModel):
    hero: int
    services: int
    team: int
    cases: int
    contact: int
    experience: int

class ContactClicks(BaseModel):
    whatsapp: int
    email: int
    phone: int

class Analytics(BaseModel):
    visitorCount: int
    visitorLocations: List[str]
    pageClicks: PageClicks
    contactClicks: ContactClicks

# ── Content (por idioma) ───────────────────────────────────────────────────
class MenuItem(BaseModel):
    label: str
    anchor: str

class Header(BaseModel):
    logoText: str
    menuItems: List[MenuItem]

class HeroFeature(BaseModel):
    icon: str
    title: str
    description: str
    buttonText: str
    buttonLink: str

class Hero(BaseModel):
    backgroundImage: str
    title: str
    subtitle: str
    features: List[HeroFeature]

class About(BaseModel):
    title: str
    mission: str
    values: str
    buttonText: str
    buttonLink: str

class ExperienceItem(BaseModel):
    dateRange: str
    role: str
    details: str

class Person(BaseModel):
    photo: str
    name: str
    title: str
    bio: str
    experience: List[ExperienceItem]
    careerHighlights: List[str]
    experienceTitle: str
    highlightsTitle: str
    experienceButton: str
    learnMoreButton: str

class ConsultationContactInfo(BaseModel):
    address: str
    phone: str
    hours: str
    email: str

class Consultation(BaseModel):
    title: str
    subtitle: str
    icon: str
    contactInfo: ConsultationContactInfo

class ServiceItem(BaseModel):
    icon: str
    title: str
    description: str
    buttonText: str
    buttonLink: str

class Services(BaseModel):
    title: str
    items: List[ServiceItem]

class TeamMember(BaseModel):
    photo: str
    name: str
    role: str
    bioLink: str
    bioButton: str

class Team(BaseModel):
    title: str
    members: List[TeamMember]

class CaseItem(BaseModel):
    caseTitle: str
    description: str
    detailsLink: str
    detailsButton: str

class Cases(BaseModel):
    title: str
    items: List[CaseItem]

class FormField(BaseModel):
    label: str
    type: str
    name: str
    placeholder: str

class ContactLocation(BaseModel):
    embedMapUrl: str

class ContactDetails(BaseModel):
    address: str
    phone: str
    email: str
    hours: str

class Contact(BaseModel):
    title: str
    formFields: List[FormField]
    submitButtonText: str
    location: ContactLocation
    details: ContactDetails

class FooterLink(BaseModel):
    label: str
    anchor: Optional[str] = None
    url: Optional[str] = None

class FooterResource(BaseModel):
    label: str
    url: str

class Footer(BaseModel):
    quickLinks: List[FooterLink]
    resources: List[FooterResource]
    languageSelector: str
    copyright: str

class SocialNetwork(BaseModel):
    name: str
    url: str
    icon: str

class SocialMedia(BaseModel):
    title: str
    networks: List[SocialNetwork]
    contactButton: str
    contactText: str

class UIEntityToggle(BaseModel):
    firmLabel: str
    personLabel: str
    switchToFirm: str
    switchToPerson: str

class UI(BaseModel):
    entityToggle: UIEntityToggle

# ── Data Principal ─────────────────────────────────────────────────────────
class ContentLanguage(BaseModel):
    header: Header
    hero: Hero
    about: About
    person: Person
    consultation: Consultation
    services: Services
    team: Team
    cases: Cases
    contact: Contact
    footer: Footer
    socialMedia: SocialMedia
    ui: UI

class ContentData(BaseModel):
    settings: Settings
    styling: Styling
    analytics: Analytics
    content: Dict[Literal["es", "en"], ContentLanguage]

class LawyerProfile(BaseModel):
    code: str
    data: ContentData
    ownerUid: Optional[str] = None  # ← NUEVO

class LawyerProfileIn(BaseModel):
    data: ContentData
