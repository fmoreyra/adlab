"""Breed catalog and helpers for protocol forms."""

BREED_OTHER = "Otra"
BREED_MIXED = "Mestizo/CRIollo"
BREED_UNSPECIFIED = "Sin especificar"

BREED_COMMON_SUFFIX = [BREED_MIXED, BREED_UNSPECIFIED, BREED_OTHER]

_CANINO_BREEDS = [
    "Akita",
    "American Pit Bull Terrier",
    "American Staffordshire Terrier",
    "Beagle",
    "Border Collie",
    "Boxer",
    "Bulldog Francés",
    "Bulldog Inglés",
    "Bull Terrier",
    "Caniche (Poodle)",
    "Cavalier King Charles Spaniel",
    "Chihuahua",
    "Cocker Spaniel",
    "Collie",
    "Dachshund (Salchicha)",
    "Dálmata",
    "Doberman",
    "Dogo Argentino",
    "Fila Brasileiro",
    "Galgo Español",
    "Golden Retriever",
    "Gran Danés",
    "Husky Siberiano",
    "Jack Russell Terrier",
    "Labrador Retriever",
    "Mastín",
    "Ovejero Alemán",
    "Ovejero Australiano",
    "Pekinés",
    "Pointer",
    "Pomerania",
    "Presa Canario",
    "Pug",
    "Rottweiler",
    "Samoyedo",
    "Schnauzer",
    "Setter Inglés",
    "Shar Pei",
    "Shih Tzu",
    "Staffordshire Bull Terrier",
    "Terranova",
    "Weimaraner",
    "West Highland White Terrier",
    "Yorkshire Terrier",
]

_FELINO_BREEDS = [
    "Abisinio",
    "American Curl",
    "Angora Turco",
    "Bengala",
    "British Shorthair",
    "Burmés",
    "Chartreux",
    "Exótico",
    "Himalayo",
    "Maine Coon",
    "Mau Egipcio",
    "Noruego de Bosque",
    "Persa",
    "Ragdoll",
    "Romano",
    "Ruso Azul",
    "Savannah",
    "Scottish Fold",
    "Siamés",
    "Somalí",
    "Sphynx",
]

_BOVINO_BREEDS = [
    "Aberdeen Angus",
    "Belted Galloway",
    "Brahman",
    "Brangus",
    "Charolais",
    "Criollo bovino",
    "Hereford",
    "Holando (Holstein)",
    "Jersey",
    "Limousin",
    "Normando",
    "Piedmontese",
    "Pinzgauer",
    "Retinta",
    "Romagnola",
    "San Martinero",
    "Shorthorn",
    "Simmental",
    "Wagyu",
]

_EQUINO_BREEDS = [
    "Appaloosa",
    "Árabe",
    "Criollo",
    "Cuarto de Milla (Quarter Horse)",
    "Falabella",
    "Frisón",
    "Holsteiner (Warmblood)",
    "Lusitano",
    "Mustang",
    "Paint Horse",
    "Palomino",
    "Pinto",
    "Pura Raza Española (PRE)",
    "Silla Francés",
    "Standardbred",
    "Thoroughbred (Pura Sangue Inglés)",
    "Trakehner",
]

_OVINO_BREEDS = [
    "Corriedale",
    "Dorper",
    "Hampshire",
    "Ideal",
    "Ile de France",
    "Lincoln",
    "Manchega",
    "Merino",
    "Pelibuey",
    "Romney Marsh",
    "Suffolk",
    "Texel",
]

_CAPRINO_BREEDS = [
    "Alpine",
    "Anglo-Nubiana",
    "Angora",
    "Boer",
    "Criolla",
    "La Mancha",
    "Nubia",
    "Saanen",
    "Toggenburg",
]

_PORCINO_BREEDS = [
    "Berkshire",
    "Criollo porcino",
    "Duroc",
    "Hampshire",
    "Landrace",
    "Large White",
    "Pietrain",
    "Tamworth",
    "Yorkshire",
]

_AVIAR_BREEDS = [
    "Aves de corral (no especificada)",
    "Broiler (pollo de engorde)",
    "Canario",
    "Codorniz",
    "Gallina ponedora",
    "Ganso",
    "Leghorn",
    "Loros/psitácidos (mascota)",
    "Paloma",
    "Pato (doméstico)",
    "Pavo",
    "Rhode Island Red",
]


def _build_breed_list(breeds: list[str]) -> list[str]:
    """Return breeds sorted alphabetically with common suffix appended."""
    return sorted(breeds, key=str.casefold) + BREED_COMMON_SUFFIX


BREEDS_BY_SPECIES: dict[str, list[str]] = {
    "Canino": _build_breed_list(_CANINO_BREEDS),
    "Felino": _build_breed_list(_FELINO_BREEDS),
    "Bovino": _build_breed_list(_BOVINO_BREEDS),
    "Equino": _build_breed_list(_EQUINO_BREEDS),
    "Ovino": _build_breed_list(_OVINO_BREEDS),
    "Caprino": _build_breed_list(_CAPRINO_BREEDS),
    "Porcino": _build_breed_list(_PORCINO_BREEDS),
    "Aviar": _build_breed_list(_AVIAR_BREEDS),
    "Otro": list(BREED_COMMON_SUFFIX),
}


def get_breeds_for_species(species: str) -> list[str]:
    """
    Return breed options for a species value.

    Args:
        species: Protocol species choice value.

    Returns:
        List of breed labels for the species, or Otro fallback.
    """
    if not species:
        return list(BREED_COMMON_SUFFIX)
    return BREEDS_BY_SPECIES.get(species, BREEDS_BY_SPECIES["Otro"])


def get_breed_choices_for_species(
    species: str,
) -> list[tuple[str, str]]:
    """
    Return Django choice tuples for breed select field.

    Args:
        species: Protocol species choice value.

    Returns:
        List of (value, label) tuples without empty placeholder.
    """
    return [(breed, breed) for breed in get_breeds_for_species(species)]


def resolve_stored_breed(
    species: str,
    stored_breed: str,
) -> tuple[str, str]:
    """
    Map a stored breed string to select + optional other field values.

    Args:
        species: Protocol species choice value.
        stored_breed: Value currently stored in Protocol.breed.

    Returns:
        Tuple of (breed_select_value, breed_other_value).
    """
    if not stored_breed:
        return "", ""

    available = get_breeds_for_species(species)
    if stored_breed in available:
        return stored_breed, ""

    return BREED_OTHER, stored_breed
