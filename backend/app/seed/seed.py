"""Seed script for the Mizizi archive.

Populates reference data (Ugandan languages, communities, places, contributors)
and a set of sample Cultural Objects with transcripts, translations, permissions
and provenance — demonstrating the full object lifecycle.

Run:  python -m app.seed.seed
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models import (
    Community,
    Consent,
    Contributor,
    CulturalContext,
    CulturalObject,
    Language,
    Permission,
    Place,
    ProvenanceEvent,
    Transcription,
    Translation,
)
from app.models.enums import (
    ConsentType,
    ObjectStatus,
    ProvenanceEventType,
    VerificationStatus,
    Visibility,
)
from app.services import object_code
from app.services.provenance_service import create_provenance_event

# --- Reference data --------------------------------------------------------

LANGUAGES = [
    {"name": "Luganda", "iso_639_3": "lug", "glottocode": "gand1255",
     "description": "Language of the Baganda, central Uganda."},
    {"name": "Runyankole-Rukiga", "iso_639_3": "nyn", "glottocode": "nyan1308",
     "description": "Language of the Banyankore and Bakiga, western Uganda."},
    {"name": "Acholi", "iso_639_3": "ach", "glottocode": "acol1236",
     "description": "Language of the Acholi people, northern Uganda."},
    {"name": "Lusoga", "iso_639_3": "xog", "glottocode": "soga1244",
     "description": "Language of the Basoga, eastern Uganda."},
    {"name": "Luo", "iso_639_3": "luo", "glottocode": "luok1242",
     "description": "Nilotic language of northern Uganda and Kenya."},
    {"name": "Runyoro", "iso_639_3": "nyo", "glottocode": "nyor1247",
     "description": "Language of the Banyoro, western Uganda."},
    {"name": "Rutooro", "iso_639_3": "ttj", "glottocode": "toor1238",
     "description": "Language of the Batooro, western Uganda."},
    {"name": "Ateso", "iso_639_3": "teo", "glottocode": "teso1249",
     "description": "Language of the Iteso, eastern Uganda."},
    {"name": "Lugbara", "iso_639_3": "lgg", "glottocode": "lugb1240",
     "description": "Language of the Lugbara people, north-west Uganda."},
    {"name": "English", "iso_639_3": "eng", "glottocode": "stan1293",
     "description": "Working language for translations."},
    {"name": "Swahili", "iso_639_3": "swa", "glottocode": "swah1253",
     "description": "Lingua franca across East Africa."},
]

COMMUNITIES = [
    {"name": "Baganda", "country": "Uganda", "region": "Central Region",
     "description": "People of Buganda, central Uganda."},
    {"name": "Banyankore", "country": "Uganda", "region": "Western Region",
     "description": "People of Ankole, south-western Uganda."},
    {"name": "Bakiga", "country": "Uganda", "region": "Western Region",
     "description": "People of Kigezi, south-western Uganda."},
    {"name": "Acholi", "country": "Uganda", "region": "Northern Region",
     "description": "People of Acholiland, northern Uganda."},
    {"name": "Basoga", "country": "Uganda", "region": "Eastern Region",
     "description": "People of Busoga, eastern Uganda."},
    {"name": "Luo", "country": "Uganda", "region": "Northern Region",
     "description": "Nilotic people of the north."},
    {"name": "Banyoro", "country": "Uganda", "region": "Western Region",
     "description": "People of Bunyoro, western Uganda."},
    {"name": "Batooro", "country": "Uganda", "region": "Western Region",
     "description": "People of Tooro, western Uganda."},
    {"name": "Iteso", "country": "Uganda", "region": "Eastern Region",
     "description": "People of Teso, eastern Uganda."},
]

PLACES = [
    {"name": "Masaka", "country": "Uganda", "region": "Central Region", "district": "Masaka",
     "latitude": -0.3387, "longitude": 31.7388},
    {"name": "Mbarara", "country": "Uganda", "region": "Western Region", "district": "Mbarara",
     "latitude": -0.6072, "longitude": 30.6545},
    {"name": "Gulu", "country": "Uganda", "region": "Northern Region", "district": "Gulu",
     "latitude": 2.7743, "longitude": 32.2980},
    {"name": "Jinja", "country": "Uganda", "region": "Eastern Region", "district": "Jinja",
     "latitude": 0.4244, "longitude": 33.2042},
    {"name": "Kampala", "country": "Uganda", "region": "Central Region", "district": "Kampala",
     "latitude": 0.3476, "longitude": 32.5825},
    {"name": "Kabale", "country": "Uganda", "region": "Western Region", "district": "Kabale",
     "latitude": -1.2494, "longitude": 29.9865},
    {"name": "Soroti", "country": "Uganda", "region": "Eastern Region", "district": "Soroti",
     "latitude": 1.7153, "longitude": 33.6102},
]

CONTRIBUTORS = [
    {"display_name": "Community Recording — Masaka", "anonymous": True, "role": "collector",
     "notes": "Field recordings collected with consent during the 'Tell Us Your Story' campaign."},
    {"display_name": "Elders' Circle — Gulu", "anonymous": True, "role": "collector",
     "notes": "Recordings of elders from the Acholi community."},
    {"display_name": "Ankole Cultural Documentation Group", "anonymous": False,
     "role": "community partner", "notes": "Community-led documentation in the Ankole kingdom."},
    {"display_name": "Mizizi Pilot Team", "anonymous": False, "role": "institutional",
     "notes": "Mizizi Uganda Pilot field team."},
]

# --- Sample cultural objects ----------------------------------------------

SAMPLE_OBJECTS = [
    {
        "title": "The Hare and the Lion",
        "object_type": "story",
        "description": "A classic Luganda trickster tale in which the clever hare outwits the lion.",
        "language": "Luganda", "community": "Baganda", "place": "Masaka",
        "contributor": "Community Recording — Masaka",
        "transcript": ("Omukyala omu yali ayagala okulaba enkomerero y’olugero lw’omwamukulu. "
                       "Ennume eyali eba mu ngalo y’empologoma. Omwamukulu yalina amagezi nnyo; "
                       "yaliba ng’agamba nti, “Nze sirya walanga, naye muli emyaka egyole.”"),
        "translation": ("A certain woman wanted to see the end of an old tale. The hare was caught "
                        "in the lion's paws. But the hare was very clever; he said, "
                        "'I do not fear death, but there are years to come.'"),
        "themes": "wisdom, deception, trickster",
        "audience": "children",
        "genre": "folktale",
        "permissions": {"public_access": True, "educational_use": True, "ai_analysis": True,
                        "ai_training": False, "derivative_work": True, "commercial_use": False},
        "consents": [("Community Elders — Masaka", ConsentType.PUBLIC_ACCESS),
                     ("Community Elders — Masaka", ConsentType.EDUCATIONAL_USE)],
        "verification": VerificationStatus.COMMUNITY_VERIFIED,
        "status": ObjectStatus.PUBLISHED,
        "visibility": Visibility.PUBLIC,
    },
    {
        "title": "Olugendo lw'Omusota (The Serpent's Journey)",
        "object_type": "story",
        "description": "A Runyankole story about a serpent and a young herder.",
        "language": "Runyankole-Rukiga", "community": "Banyankore", "place": "Mbarara",
        "contributor": "Ankole Cultural Documentation Group",
        "transcript": ("Kare-kare, omusota omunene gukagira omwana w'ente. Omwana yebariza "
                       "enyama yawe, kandi omusota ogu gwamusinga kutwarira ekinyamwanga."),
        "translation": ("Long ago, a great serpent captured the herder's son. The boy asked for "
                        "his freedom, but the serpent carried him far away."),
        "themes": "courage, family, serpent",
        "audience": "children",
        "genre": "folktale",
        "permissions": {"public_access": True, "educational_use": True, "ai_analysis": True,
                        "ai_training": False, "derivative_work": True, "commercial_use": False},
        "consents": [("Ankole Cultural Documentation Group", ConsentType.PUBLIC_ACCESS)],
        "verification": VerificationStatus.HUMAN_REVIEWED,
        "status": ObjectStatus.PUBLISHED,
        "visibility": Visibility.PUBLIC,
    },
    {
        "title": "Gin Ma Nyoo (The Bird Song)",
        "object_type": "song",
        "description": "A children's song from the Acholi community, sung during harvest.",
        "language": "Acholi", "community": "Acholi", "place": "Gulu",
        "contributor": "Elders' Circle — Gulu",
        "transcript": ("Gin ma nyoo, gin ma nyoo, winyo owinyo i otok. "
                       "Lagonya tungi, lagonya tungi, obed bedo i wi kot."),
        "translation": ("The singing thing, the singing thing, the bird is singing in the garden. "
                        "Play the horn, play the horn, let it rest upon the rooftop."),
        "themes": "children, harvest, music",
        "audience": "children",
        "genre": "children's song",
        "permissions": {"public_access": True, "educational_use": True, "ai_analysis": True,
                        "ai_training": False, "derivative_work": False, "commercial_use": False},
        "consents": [("Elders' Circle — Gulu", ConsentType.PUBLIC_ACCESS)],
        "verification": VerificationStatus.HUMAN_REVIEWED,
        "status": ObjectStatus.PUBLISHED,
        "visibility": Visibility.PUBLIC,
    },
    {
        "title": "Omusota gw'Olunaku (Riddle of the Day)",
        "object_type": "riddle",
        "description": "A riddle elders pose to children at twilight.",
        "language": "Luganda", "community": "Baganda", "place": "Kampala",
        "contributor": "Community Recording — Masaka",
        "transcript": "Akantu akalimba, akalimba ne kubba: nkyukira mu ngalo z’omwana.",
        "translation": "It plays and plays and then it cries: it slips from the child's hands.",
        "themes": "riddle, children, games",
        "audience": "children",
        "genre": "riddle",
        "permissions": {"public_access": True, "educational_use": True, "ai_analysis": True,
                        "ai_training": False, "derivative_work": True, "commercial_use": False},
        "consents": [("Community Elders — Masaka", ConsentType.PUBLIC_ACCESS)],
        "verification": VerificationStatus.COMMUNITY_VERIFIED,
        "status": ObjectStatus.PUBLISHED,
        "visibility": Visibility.PUBLIC,
    },
    {
        "title": "Amagezi g’abakadde (The Wisdom of the Elders)",
        "object_type": "proverb",
        "description": "A proverb about the value of elder wisdom.",
        "language": "Runyankole-Rukiga", "community": "Bakiga", "place": "Kabale",
        "contributor": "Ankole Cultural Documentation Group",
        "transcript": "Amagezi g’abakadde ntangara ne zinyonyi ziija kugarya.",
        "translation": "The wisdom of the elders, if not preserved, even the birds will scatter it.",
        "themes": "wisdom, elders, preservation",
        "audience": "all",
        "genre": "proverb",
        "permissions": {"public_access": True, "educational_use": True, "ai_analysis": True,
                        "ai_training": True, "derivative_work": True, "commercial_use": False},
        "consents": [("Ankole Cultural Documentation Group", ConsentType.PUBLIC_ACCESS)],
        "verification": VerificationStatus.COMMUNITY_VERIFIED,
        "status": ObjectStatus.PUBLISHED,
        "visibility": Visibility.PUBLIC,
    },
    {
        "title": "Lakwena's Warning (Personal Memory)",
        "object_type": "personal_memory",
        "description": "A personal recollection about the meaning of the name Lakwena.",
        "language": "Acholi", "community": "Acholi", "place": "Gulu",
        "contributor": "Elders' Circle — Gulu",
        "transcript": "Nyinga Lakwena, ni obedo lok 'Acholi. Koro lanyut me cwiny ma weko dano bedo konyo.",
        "translation": "My name is Lakwena, which is the Acholi word for messenger. It shows the "
                       "spirit that leads one to help others.",
        "themes": "names, identity, memory",
        "audience": "all",
        "genre": "personal history",
        "permissions": {"public_access": False, "educational_use": True, "ai_analysis": False,
                        "ai_training": False, "derivative_work": False, "commercial_use": False},
        "consents": [("Elders' Circle — Gulu", ConsentType.PRESERVATION)],
        "verification": VerificationStatus.UNVERIFIED,
        "status": ObjectStatus.DRAFT,
        "visibility": Visibility.RESTRICTED,
    },
]

# --- Reusable bits ---------------------------------------------------------


def get_or_create(db: Session, model, **attrs):
    item = db.execute(select(model).where(*[getattr(model, k) == v for k, v in attrs.items()])).scalars().first()
    if item is None:
        item = model(**attrs)
        db.add(item)
        db.flush()
    return item


def seed_reference(db: Session) -> dict:
    langs = {l["name"]: get_or_create(db, Language, name=l["name"], iso_639_3=l["iso_639_3"],
                                       glottocode=l["glottocode"], description=l["description"])
             for l in LANGUAGES}
    comms = {c["name"]: get_or_create(db, Community, name=c["name"], country=c["country"],
                                      region=c["region"], description=c["description"])
             for c in COMMUNITIES}
    places = {p["name"]: get_or_create(db, Place, name=p["name"], country=p["country"],
                                       region=p["region"], district=p["district"],
                                       latitude=p["latitude"], longitude=p["longitude"])
              for p in PLACES}
    contribs = {c["display_name"]: get_or_create(db, Contributor, display_name=c["display_name"],
                                                 anonymous=c["anonymous"], role=c["role"], notes=c["notes"])
                for c in CONTRIBUTORS}
    return {"languages": langs, "communities": comms, "places": places, "contributors": contribs}


def seed_objects(db: Session, refs: dict) -> None:
    english = refs["languages"]["English"]
    for spec in SAMPLE_OBJECTS:
        existing = db.execute(
            select(CulturalObject).where(CulturalObject.title == spec["title"])
        ).scalars().first()
        if existing is not None:
            continue

        lang = refs["languages"][spec["language"]]
        comm = refs["communities"][spec["community"]]
        place = refs["places"][spec["place"]]
        contrib = refs["contributors"][spec["contributor"]]

        code = object_code.generate_object_code(db, spec["object_type"], lang.id)

        obj = CulturalObject(
            object_code=code,
            object_type=spec["object_type"],
            title=spec["title"],
            description=spec["description"],
            original_language_id=lang.id,
            community_id=comm.id,
            place_id=place.id,
            contributor_id=contrib.id,
            status=spec["status"].value,
            visibility=spec["visibility"].value,
            verification_status=spec["verification"].value,
        )
        db.add(obj)
        db.flush()

        create_provenance_event(db, obj.id, ProvenanceEventType.OBJECT_CREATED, actor="seed",
                                description=f"Seed: object created ({code}).")

        # Transcription + translation
        db.add(Transcription(cultural_object_id=obj.id, language_id=lang.id,
                             text=spec["transcript"], model_name="seed", model_version="1.0",
                             confidence=0.99,
                             verification_status="human_reviewed", created_by="seed"))
        db.add(Translation(cultural_object_id=obj.id, source_language_id=lang.id,
                           target_language_id=english.id, text=spec["translation"],
                           model_name="seed", model_version="1.0",
                           verification_status="human_reviewed"))

        # Cultural context
        db.add(CulturalContext(cultural_object_id=obj.id, genre=spec["genre"],
                               audience=spec["audience"], themes=spec["themes"]))

        # Permissions
        perm_values = {"preservation": True, **spec["permissions"]}
        db.add(Permission(cultural_object_id=obj.id, **perm_values))

        # Consents
        for party, ctype in spec["consents"]:
            db.add(Consent(cultural_object_id=obj.id, consenting_party=party,
                           consent_type=ctype.value, granted_at=None))

        # Provenance trail
        create_provenance_event(db, obj.id, ProvenanceEventType.TRANSCRIPTION_GENERATED, actor="seed",
                                description="Seed transcript created.")
        create_provenance_event(db, obj.id, ProvenanceEventType.TRANSLATION_GENERATED, actor="seed",
                                description="Seed translation created.")
        create_provenance_event(db, obj.id, ProvenanceEventType.CONSENT_RECORDED, actor="seed",
                                description="Seed consent recorded.")
        create_provenance_event(db, obj.id, ProvenanceEventType.OBJECT_PUBLISHED, actor="seed",
                                description="Seed object published.")


SEED_USERS = [
    {
        "email": "admin@mizizi.app",
        "password": "MiziziAdmin!2026",
        "display_name": "Mizizi Administrator",
        "role": "admin",
        "languages": ["Luganda", "English"],
        "places": ["Kampala"],
        "communities": ["Baganda"],
    },
    {
        "email": "nalongo@mizizi.app",
        "password": "Nalongo!2026",
        "display_name": "Nalongo Nakato",
        "role": "member",
        "languages": ["Luganda", "English"],
        "places": ["Masaka"],
        "communities": ["Baganda"],
    },
    {
        "email": "owor@mizizi.app",
        "password": "Owor!2026",
        "display_name": "Owor Apio",
        "role": "member",
        "languages": ["Acholi", "English"],
        "places": ["Gulu"],
        "communities": ["Acholi"],
    },
    {
        "email": "mukasa@mizizi.app",
        "password": "Mukasa!2026",
        "display_name": "Mukasa Ssentamu",
        "role": "reviewer",
        "languages": ["Luganda", "English"],
        "places": ["Masaka"],
        "communities": ["Baganda"],
    },
]


def seed_users(db: Session, refs: dict) -> dict:
    """Idempotently create accounts (admin, reviewers, demo members)."""
    from app.core import security as security_mod
    from app.models import User, UserCommunity, UserLanguage, UserPlace

    created = {}
    for spec in SEED_USERS:
        existing = db.execute(select(User).where(User.email == spec["email"])).scalars().first()
        if existing is not None:
            created[spec["email"]] = existing
            continue
        user = User(
            email=spec["email"],
            password_hash=security_mod.hash_password(spec["password"]),
            display_name=spec["display_name"],
            role=spec["role"],
        )
        db.add(user)
        db.flush()
        for name in spec["languages"]:
            db.add(UserLanguage(user_id=user.id, language_id=refs["languages"][name].id))
        for name in spec["places"]:
            db.add(UserPlace(user_id=user.id, place_id=refs["places"][name].id))
        for name in spec["communities"]:
            db.add(UserCommunity(user_id=user.id, community_id=refs["communities"][name].id))
        created[spec["email"]] = user
    return created


def main() -> None:
    db = SessionLocal()
    try:
        refs = seed_reference(db)
        db.commit()
        seed_objects(db, refs)
        db.commit()
        seed_users(db, refs)
        db.commit()
        total = db.execute(select(CulturalObject)).scalars().all()
        print(f"Seed complete. {len(total)} cultural objects in archive.")
    finally:
        db.close()


if __name__ == "__main__":
    main()