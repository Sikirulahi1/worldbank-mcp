"""reference_data.py — Static country reference list."""
from src.domain.country.entities import Country


COUNTRIES: list[Country] = [
    Country(iso2="US", iso3="USA", name="United States", aliases=["USA", "United States of America", "America"]),
    Country(iso2="GB", iso3="GBR", name="United Kingdom", aliases=["UK", "Great Britain", "Britain"]),
    Country(iso2="NG", iso3="NGA", name="Nigeria", aliases=[]),
    Country(iso2="CI", iso3="CIV", name="Cote d'Ivoire", aliases=["Ivory Coast", "Côte d'Ivoire"]),
    
    Country(iso2="CG", iso3="COG", name="Congo, Rep.", aliases=["Republic of the Congo", "Congo-Brazzaville"]),
    Country(iso2="CD", iso3="COD", name="Congo, Dem. Rep.", aliases=["DRC", "Democratic Republic of the Congo", "Congo-Kinshasa", "Zaire"]),
    
    Country(iso2="KR", iso3="KOR", name="Korea, Rep.", aliases=["South Korea"]),
    Country(iso2="KP", iso3="PRK", name="Korea, Dem. People's Rep.", aliases=["North Korea"]),
]

