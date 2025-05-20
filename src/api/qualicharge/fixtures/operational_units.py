r"""QualiCharge operational units fixture.

Initial release: 2024/05/17

Fixture generated from AFIREV's official CSV file available at:
https://afirev.fr/fr/liste-des-identifiants-attribues/

Columns have been selected via:

```
csvcut -d ';' -K 1 -c 2,3 data/afirev-charging.csv
```

Values have been cleaned manually (trimmed and fixed encoding issues).

To update this list:

```
diff old.csv new.csv | \
    grep "> FR" | \
    sed "s/> \(FR.*\),\(.*\)/Item(\"\\1\", \"\\2\",),/g"
```

And then remove/update Operational units with a new name.
"""

from collections import namedtuple
from typing import List

# Nota bene: we import the GroupOperationalUnit schema so that the MetaData registry
# is aware of the GroupOperationalUnit table and allows to use this secondary
# (intermediate) relationship.
#
# For reference, see:
# https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html#orm-declarative-relationship-secondary-eval
from qualicharge.auth.schemas import GroupOperationalUnit  # noqa: F401
from qualicharge.schemas.core import OperationalUnit, OperationalUnitTypeEnum

# Operational units
Item = namedtuple("Item", ["code", "name"])
data: List[Item] = [
    Item(
        "FR073",
        "ACELEC CHARGE",
    ),
    Item(
        "FR0NX",
        "NEXTENEO",
    ),
    Item(
        "FR147",
        "E.Z.O",
    ),
    Item(
        "FR281",
        "WALLCORP",
    ),
    Item(
        "FR2AC",
        "SUPERNOVA",
    ),
    Item(
        "FR3R3",
        "R3",
    ),
    Item(
        "FR55C",
        "Electric 55 Charging",
    ),
    Item(
        "FR594",
        "Communauté d'Agglomération de Cambrai",
    ),
    Item(
        "FR5GS",
        "GREENSPOT - MOBILYGREEN",
    ),
    Item(
        "FR730",
        "MAIRIE DE MARCK",
    ),
    Item(
        "FR777",
        "BE GREEN MOBILITY",
    ),
    Item(
        "FR911",
        "Porsche Sales & Marketplace GmbH",
    ),
    Item(
        "FRA02",
        "Communauté d'Agglomération de Marne et Gondoire",
    ),
    Item(
        "FRA03",
        "Communauté d'Agglomération Paris - Vallée de la Ma",
    ),
    Item(
        "FRA04",
        "Val d'Europe agglomération",
    ),
    Item(
        "FRA05",
        "Rambouillet Territoires",
    ),
    Item(
        "FRA07",
        "CCHVC",
    ),
    Item(
        "FRA15",
        "CC- Plaine de l'Ain",
    ),
    Item(
        "FRA16",
        "Réseau WiiiZ",
    ),
    Item(
        "FRA21",
        "Communauté de communes de la Côtière",
    ),
    Item(
        "FRA22",
        "Communauté d'Agglomération de la Riviera Française",
    ),
    Item(
        "FRA30",
        "Le Pont du Gard",
    ),
    Item(
        "FRA31",
        "Toulouse Métropole - Parking",
    ),
    Item(
        "FRA51",
        "CC – Vitry Champagne et Der",
    ),
    Item(
        "FRA87",
        "SMA PNR Gatinais",
    ),
    Item(
        "FRA88",
        "Communauté de Communes de la Châtaigneraie Cantalienne",
    ),
    Item(
        "FRABA",
        "CCVBA",
    ),
    Item(
        "FRACA",
        "AEROPORTS DE LA COTE D'AZUR",
    ),
    Item(
        "FRADP",
        "Paris Aéroport",
    ),
    Item(
        "FRAIR",
        "Airbus",
    ),
    Item(
        "FRALS",
        "ALTENSYS",
    ),
    Item(
        "FRANG",
        "ChargeAngels",
    ),
    Item(
        "FRAPR",
        "APRR",
    ),
    Item(
        "FRAPS",
        "AMPERUS",
    ),
    Item(
        "FRARE",
        "AREA TECH",
    ),
    Item(
        "FRATL",
        "Atlante",
    ),
    Item(
        "FRAUT",
        "Autel Europe",
    ),
    Item(
        "FRAVE",
        "AVENEL",
    ),
    Item(
        "FRBAT",
        "KALBORN",
    ),
    Item(
        "FRBBJ",
        "BBJ Mazères",
    ),
    Item(
        "FRBCC",
        "BEC CONSTRUCTION CHAMPAGNE",
    ),
    Item(
        "FRBE1",
        "Bouygues Energies & Services",
    ),
    Item(
        "FRBE2",
        "Bouygues Energies & Services",
    ),
    Item(
        "FRBEC",
        "Be Cablé",
    ),
    Item(
        "FRBHM",
        "BORNECO",
    ),
    Item(
        "FRBMP",
        "Bump",
    ),
    Item(
        "FRBPF",
        "bp France",
    ),
    Item(
        "FRBR1",
        "Bohr Emobility",
    ),
    Item(
        "FRBRS",
        "BRS",
    ),
    Item(
        "FRBS1",
        "Bornes Solutions",
    ),
    Item(
        "FRBSC",
        "Bornes Solutions - Itinérance Publique Copropriété",
    ),
    Item(
        "FRBSP",
        "Bornes Solutions - Itinérance Publique",
    ),
    Item(
        "FRC01",
        "Métropole Rouen Normandie",
    ),
    Item(
        "FRC2A",
        "CAR2PLUG",
    ),
    Item(
        "FRC2N",
        "CAR2PLUG",
    ),
    Item(
        "FRC2P",
        "CAR2PLUG",
    ),
    Item(
        "FRC4F",
        "Compleo Charging Technologies",
    ),
    Item(
        "FRCAR",
        "Carrefour Proximité",
    ),
    Item(
        "FRCG0",
        "ChargeGuru",
    ),
    Item(
        "FRCHA",
        "CHARGEPOLY",
    ),
    Item(
        "FRCHK",
        "Chargekeeper",
    ),
    Item(
        "FRCIT",
        "CITEOS",
    ),
    Item(
        "FRCM1",
        "CLEM",
    ),
    Item(
        "FRCNT",
        "CONECTIC",
    ),
    Item(
        "FRCOF",
        "COFIROUTE",
    ),
    Item(
        "FRCPI",
        "ChargePoint",
    ),
    Item(
        "FRCTS",
        "Citeos Vinci Energies",
    ),
    Item(
        "FRDMB",
        "DKV Mobility",
    ),
    Item(
        "FRDNP",
        "DROPNPLUG",
    ),
    Item(
        "FRDOU",
        "KBDR DOUAINS",
    ),
    Item(
        "FRDRE",
        "Dream Energy",
    ),
    Item(
        "FRDRV",
        "DRIVECO charging network",
    ),
    Item(
        "FRDS6",
        "Commuanuté de Communes Desvres Samer",
    ),
    Item(
        "FRDWD",
        "Docuworld",
    ),
    Item(
        "FRE04",
        "IZIVIA-Corridoor",
    ),
    Item(
        "FRE05",
        "Renault-Employés",
    ),
    Item(
        "FRE08",
        "DRIVECO",
    ),
    Item(
        "FRE10",
        "Virta",
    ),
    Item(
        "FRE11",
        "Leroy-Merlin",
    ),
    Item(
        "FRE12",
        "Marché International de Rungis",
    ),
    Item(
        "FRE27",
        "ODIM Infrastructure",
    ),
    Item(
        "FRE32",
        "Centre Leclerc Trie Chateau",
    ),
    Item(
        "FRE44",
        "AIRBUS ESR",
    ),
    Item(
        "FRE45",
        "IMT Douai",
    ),
    Item(
        "FRE47",
        "Hotel Akena",
    ),
    Item(
        "FRE59",
        "SCAPNOR",
    ),
    Item(
        "FREAB",
        "EAB",
    ),
    Item(
        "FREBN",
        "CPO Réseau EBORN",
    ),
    Item(
        "FRECH",
        "Easy Charge",
    ),
    Item(
        "FRECN",
        "MEA ENERGIES",
    ),
    Item(
        "FREDI",
        "EDRI",
    ),
    Item(
        "FREES",
        "Engie Energie Services",
    ),
    Item(
        "FREFC",
        "EDRI",
    ),
    Item(
        "FREFL",
        "Road",
    ),
    Item(
        "FREGR",
        "EG Retail (France) -Stations BP en France",
    ),
    Item(
        "FRELC",
        "Electra",
    ),
    Item(
        "FRELM",
        "Reseau Le Mans, parking Cénovia",
    ),
    Item(
        "FRELY",
        "BORNE SIE-ELY",
    ),
    Item(
        "FREMI",
        "E.Leclerc Millau Centre Cial Du Viaduc",
    ),
    Item(
        "FRENR",
        "Enerstock Charging Station",
    ),
    Item(
        "FREOL",
        "EOLIBERTY Network",
    ),
    Item(
        "FREPA",
        "EPAPS",
    ),
    Item(
        "FREPI",
        "ECO-PI",
    ),
    Item(
        "FRESE",
        "Réseau saint Étienne métropole",
    ),
    Item(
        "FRESL",
        "Free2Move eSolutions",
    ),
    Item(
        "FREST",
        "E-STATION",
    ),
    Item(
        "FRETI",
        "E-TOTEM TI",
    ),
    Item(
        "FREVA",
        "EVADEA",
    ),
    Item(
        "FREVC",
        "EV Cars",
    ),
    Item(
        "FREVZ",
        "evZen",
    ),
    Item(
        "FREXA",
        "EXADYS",
    ),
    Item(
        "FREZD",
        "E.Zdrive",
    ),
    Item(
        "FRFAS",
        "Fastned",
    ),
    Item(
        "FRFLB",
        "Flowbird Park & Charge",
    ),
    Item(
        "FRFR0",
        "Freshmile CPO",
    ),
    Item(
        "FRFR1",
        "Freshmile",
    ),
    Item(
        "FRFR2",
        "Freshmile-Advenir",
    ),
    Item(
        "FRFR3",
        "Freshmile Infrastructure",
    ),
    Item(
        "FRFRS",
        "Freshmile Semi-public",
    ),
    Item(
        "FRFUL",
        "Fulgura",
    ),
    Item(
        "FRG02",
        "Carrefour Property",
    ),
    Item(
        "FRG05",
        "Centre Commercial Grand Var",
    ),
    Item(
        "FRG06",
        "COLRUYT",
    ),
    Item(
        "FRG10",
        "Points de charge hors voirie publique France entière multi-aménageurs",
    ),
    Item(
        "FRG11",
        "LE CAMPING DU LAC",
    ),
    Item(
        "FRG29",
        "Immo Mousquetaires",
    ),
    Item(
        "FRG38",
        "BE TROM SOLUTIONS ENVIRONNEMENTALES MARQUE Be Cablé",
    ),
    Item(
        "FRG51",
        "Driveco pour Décathlon",
    ),
    Item(
        "FRG53",
        "GOLF CLUB DE LYON",
    ),
    Item(
        "FRG58",
        "CI2C",
    ),
    Item(
        "FRGCE",
        "Elli",
    ),
    Item(
        "FRGFX",
        "GreenFlux",
    ),
    Item(
        "FRGMB",
        "GAIA Mobility",
    ),
    Item(
        "FRGMO",
        "GEMO",
    ),
    Item(
        "FRGOB",
        "GMOB",
    ),
    Item(
        "FRGRN",
        "Gaia Green Charging",
    ),
    Item(
        "FRGSP",
        "GREENSPOT",
    ),
    Item(
        "FRGYM",
        "GreenYellow, Shift Mobility",
    ),
    Item(
        "FRH01",
        "Pass Pass Electrique - Communauté d'Agglomération du Pays de Saint Omer",
    ),
    Item(
        "FRH02",
        "Pass Pass Electrique - Communauté d'Agglomération Maubeuge Val de Sambre",
    ),
    Item(
        "FRH03",
        "Pass Pass Electrique - Communauté d'Agglomération Valenciennes Métropole",
    ),
    Item(
        "FRH04",
        "Pass Pass Electrique - Communauté d'Agglomération Douaisis Agglo",
    ),
    Item(
        "FRH05",
        "Pass Pass Electrique - Communauté d'Agglomération du Boulonnais",
    ),
    Item(
        "FRH06",
        "Pass Pass Electrique - Communauté Urbaine d'Arras",
    ),
    Item(
        "FRH07",
        "Pass Pass Electrique - Communauté de Communes du Coeur d'Ostrevent",
    ),
    Item(
        "FRH08",
        "Pass Pass Electrique - Ville d'Hazebrouck",
    ),
    Item(
        "FRH09",
        "Pass Pass Electrique - Communauté de Communes Flandre-Lys",
    ),
    Item(
        "FRH10",
        "Pass Pass Electrique - Communauté de Communes du Pays de Lumbres",
    ),
    Item(
        "FRH11",
        "Pass Pass Electrique - Communauté de Communes du Pays d'Opale",
    ),
    Item(
        "FRH13",
        (
            "Pass Pass Electrique - Communauté d'Agglomération Béthune Bruay Artois "
            "Lys Romane"
        ),
    ),
    Item(
        "FRH15",
        "Communauté Urbaine de Dunkerque",
    ),
    Item(
        "FRH16",
        "Communauté de Communes du Pays de Mormal",
    ),
    Item(
        "FRH17",
        "Ville de Fourmies",
    ),
    Item(
        "FRH18",
        "Communauté de Communes Campagnes de l'Artois",
    ),
    Item(
        "FRH19",
        "Ville d'Annoeullin",
    ),
    Item(
        "FRH20",
        "Communauté de Communes Pévèle Carembault",
    ),
    Item(
        "FRH21",
        "Pass Pass Electrique - Commune d'Hénin-Beaumont",
    ),
    Item(
        "FRHF1",
        "Bornes IRVE Communauté de Communes des Hauts de Flandre",
    ),
    Item(
        "FRHPB",
        "Communauté de communes de la Houve et du Pays Boulageois",
    ),
    Item(
        "FRHPC",
        "Réseau Total HPC",
    ),
    Item(
        "FRIEN",
        "IECharge France",
    ),
    Item(
        "FRIIM",
        "IZIVIA IMPACT",
    ),
    Item(
        "FRIKA",
        "IRVE IKEA FRANCE",
    ),
    Item(
        "FRIND",
        "INDELEC MOBILITY",
    ),
    Item(
        "FRION",
        "IONITY",
    ),
    Item(
        "FRIOY",
        "IONITY GmbH",
    ),
    Item(
        "FRIPK",
        "Interparking France",
    ),
    Item(
        "FRISC",
        "ISC - ELECTRISE",
    ),
    Item(
        "FRISE",
        "INOUID Smart ECharging",
    ),
    Item(
        "FRIXL",
        "IZIVIA EXPRESS",
    ),
    Item(
        "FRIZF",
        "IZIVIA FAST",
    ),
    Item(
        "FRIZM",
        "IZIVIA Métropoles",
    ),
    Item(
        "FRJRC",
        "jerecharge.com",
    ),
    Item(
        "FRKV2",
        "Kolektivolt_2",
    ),
    Item(
        "FRLAF",
        "LAFON Technologies siège Bassens",
    ),
    Item(
        "FRLDL",
        "Lidl France",
    ),
    Item(
        "FRLE1",
        "E.Leclerc",
    ),
    Item(
        "FRLE2",
        "E.Leclerc",
    ),
    Item(
        "FRLEK",
        "LEKTRI.CO",
    ),
    Item(
        "FRLGC",
        "Commune de La Garenne-Colombes",
    ),
    Item(
        "FRLGE",
        "Réseaux Groupe LGE",
    ),
    Item(
        "FRLIB",
        "EOLIBERTY",
    ),
    Item(
        "FRLMC",
        "LOAD MY CAR",
    ),
    Item(
        "FRLMS",
        "Last Mile Solutions",
    ),
    Item(
        "FRLOD",
        "LODMI",
    ),
    Item(
        "FRLPA",
        "LPA - Lyon Parc Auto",
    ),
    Item(
        "FRLPI",
        "Allego Group",
    ),
    Item(
        "FRLST",
        "LOAD STATIONS",
    ),
    Item(
        "FRLUM",
        "LUMI'iN FRANCE",
    ),
    Item(
        "FRM13",
        "Aix-Marseille Provence Métropole",
    ),
    Item(
        "FRM29",
        "Brest Métropole",
    ),
    Item(
        "FRM31",
        "Toulouse Métropole",
    ),
    Item(
        "FRM34",
        "Montpellier Méditerranée Métropole (34)",
    ),
    Item(
        "FRM38",
        "Grenoble-Alpes Métropole",
    ),
    Item(
        "FRM54",
        "Département de Meurthe et Moselle",
    ),
    Item(
        "FRM59",
        "Pass Pass Electrique - Métropole Européenne de Lille",
    ),
    Item(
        "FRMAP",
        "Electromaps",
    ),
    Item(
        "FRMAU",
        "ProperPhi",
    ),
    Item(
        "FRMBA",
        "MA BORNE AUTO",
    ),
    Item(
        "FRMBI",
        "MOBIVE",
    ),
    Item(
        "FRMBP",
        "MobilityPlus",
    ),
    Item(
        "FRMEL",
        "Concession IRVE de la MEL",
    ),
    Item(
        "FRMFC",
        "Mobilize Fast Charge",
    ),
    Item(
        "FRMGP",
        "Métropolis",
    ),
    Item(
        "FRMOB",
        "MOBELEC",
    ),
    Item(
        "FRMON",
        "Monaco ON France",
    ),
    Item(
        "FRMW1",
        "MOBILYWEB",
    ),
    Item(
        "FRN54",
        "SDE54",
    ),
    Item(
        "FRNXS",
        "Nexans Charging Solutions",
    ),
    Item(
        "FROBS",
        "ORIOS by SPIE",
    ),
    Item(
        "FRONE",
        "reev",
    ),
    Item(
        "FROTH",
        "Stations TIERS",
    ),
    Item(
        "FROZE",
        "OZECAR",
    ),
    Item(
        "FRP01",
        "Parking EFFIA",
    ),
    Item(
        "FRP07",
        "INDIGO Group",
    ),
    Item(
        "FRPA1",
        "AVIA Picoty Autoroutes",
    ),
    Item(
        "FRPAM",
        "Paragon Mobility",
    ),
    Item(
        "FRPAN",
        "Securecharge",
    ),
    Item(
        "FRPD1",
        "Power Dot",
    ),
    Item(
        "FRPHI",
        "ProperPhi",
    ),
    Item(
        "FRPL1",
        "LePlein",
    ),
    Item(
        "FRPL2",
        "LePlein",
    ),
    Item(
        "FRPL3",
        "LePlein",
    ),
    Item(
        "FRPR1",
        "AVIA Picoty Réseau",
    ),
    Item(
        "FRPRP",
        "Ville de Perpignan",
    ),
    Item(
        "FRPVD",
        "PROVIRIDIS",
    ),
    Item(
        "FRPY1",
        "PICOTY",
    ),
    Item(
        "FRQOV",
        "QOVOLTIS",
    ),
    Item(
        "FRQPK",
        "Q-Park France",
    ),
    Item(
        "FRQWC",
        "Qwello France SAS",
    ),
    Item(
        "FRQWT",
        "QoWatt",
    ),
    Item(
        "FRRBO",
        "Robert Bosch, Division Connected Mobility Solutions",
    ),
    Item(
        "FRREB",
        "REBORNE",
    ),
    Item(
        "FRRIR",
        "RIRODO",
    ),
    Item(
        "FRRM1",
        "RIVIERA MOBILITES",
    ),
    Item(
        "FRRMA",
        "Recharger mon auto",
    ),
    Item(
        "FRROC",
        "ROCPIERRE",
    ),
    Item(
        "FRROS",
        "Rossini Energy",
    ),
    Item(
        "FRRSE",
        "Régie Services Energie",
    ),
    Item(
        "FRS02",
        "USEDA 02",
    ),
    Item(
        "FRS08",
        "Fédération Départementale d'Energie des Ardennes",
    ),
    Item(
        "FRS09",
        "SDE09",
    ),
    Item(
        "FRS11",
        "SYADEN 11",
    ),
    Item(
        "FRS12",
        "SIEDA 12",
    ),
    Item(
        "FRS13",
        "SMED13",
    ),
    Item(
        "FRS14",
        "MobiSDEC",
    ),
    Item(
        "FRS16",
        "SDEG 16",
    ),
    Item(
        "FRS17",
        "SDEER 17",
    ),
    Item(
        "FRS19",
        "FDEE 19",
    ),
    Item(
        "FRS21",
        "SICECO 21",
    ),
    Item(
        "FRS22",
        "BREV�CAR",
    ),
    Item(
        "FRS23",
        "SDEC23",
    ),
    Item(
        "FRS24",
        "SDE 24",
    ),
    Item(
        "FRS27",
        "SIEGE 27",
    ),
    Item(
        "FRS28",
        "SDE 28",
    ),
    Item(
        "FRS30",
        "SMEG 30",
    ),
    Item(
        "FRS31",
        "SDEHG",
    ),
    Item(
        "FRS32",
        "Réseau SDE32",
    ),
    Item(
        "FRS33",
        "SDEEG 33",
    ),
    Item(
        "FRS34",
        "Hérault Energies 34",
    ),
    Item(
        "FRS35",
        "SDE 35",
    ),
    Item(
        "FRS36",
        "SDEI 36",
    ),
    Item(
        "FRS37",
        "SIEIL 37",
    ),
    Item(
        "FRS40",
        "SYDEC 40",
    ),
    Item(
        "FRS41",
        "SIDELC",
    ),
    Item(
        "FRS42",
        "SIEL 42",
    ),
    Item(
        "FRS44",
        "SYDELA",
    ),
    Item(
        "FRS46",
        "FDEL 46",
    ),
    Item(
        "FRS47",
        "Territoire d'Energie Lot-et-Garonne",
    ),
    Item(
        "FRS48",
        "SDEE 48",
    ),
    Item(
        "FRS49",
        "SIEML 49",
    ),
    Item(
        "FRS50",
        "e-charge50",
    ),
    Item(
        "FRS51",
        "SIEM 51",
    ),
    Item(
        "FRS52",
        "SDED52",
    ),
    Item(
        "FRS53",
        "Territoire d'Énergie de la Mayenne",
    ),
    Item(
        "FRS54",
        "Meurthe-et-Moselle",
    ),
    Item(
        "FRS55",
        "FUCLEM",
    ),
    Item(
        "FRS56",
        "Morbihan énergies",
    ),
    Item(
        "FRS59",
        "Pass Pass Electrique - SIDEC (Syndicat mIxte De l’Energie du Cambrésis)",
    ),
    Item(
        "FRS60",
        "Réseau Mouv'Oise",
    ),
    Item(
        "FRS61",
        "SE61",
    ),
    Item(
        "FRS62",
        "Fédération départementale d’énergie du Pas-de-Calais",
    ),
    Item(
        "FRS63",
        "IRVE - TE63",
    ),
    Item(
        "FRS64",
        "SDEPA 64",
    ),
    Item(
        "FRS66",
        "SYDEEL 66",
    ),
    Item(
        "FRS68",
        "TEA68",
    ),
    Item(
        "FRS69",
        "SYDER",
    ),
    Item(
        "FRS71",
        "SYDESL",
    ),
    Item(
        "FRS72",
        "Sarthe IRVE",
    ),
    Item(
        "FRS76",
        "SDE76",
    ),
    Item(
        "FRS77",
        "EcoCharge 77",
    ),
    Item(
        "FRS80",
        "IRVE 80",
    ),
    Item(
        "FRS81",
        "SDET 81",
    ),
    Item(
        "FRS82",
        "Infrastructure de recharge TARN-ET-GARONNE",
    ),
    Item(
        "FRS84",
        "SEV",
    ),
    Item(
        "FRS85",
        "Syndicat Départemental d'Energie et d'Equipement d",
    ),
    Item(
        "FRS86",
        "SOREGIES",
    ),
    Item(
        "FRS87",
        "SYNDICAT ENERGIES HAUTE  VIENNE",
    ),
    Item(
        "FRS88",
        "SDEV88",
    ),
    Item(
        "FRS90",
        "IRVE Territoire-de-Belfort",
    ),
    Item(
        "FRS91",
        "SMOYS91",
    ),
    Item(
        "FRS95",
        "SDEVO",
    ),
    Item(
        "FRSAE",
        "SAEMES",
    ),
    Item(
        "FRSDG",
        "Syndicat de la Diège",
    ),
    Item(
        "FRSE1",
        "STATIONS-E - France",
    ),
    Item(
        "FRSE2",
        "STATIONS-E",
    ),
    Item(
        "FRSE3",
        "STATIONS-E",
    ),
    Item(
        "FRSEC",
        "SSEC",
    ),
    Item(
        "FRSEO",
        "SEOLIS",
    ),
    Item(
        "FRSEV",
        "NovaBorne",
    ),
    Item(
        "FRSFS",
        "Shell Recharge",
    ),
    Item(
        "FRSGA",
        "SGA INDUSTRIES",
    ),
    Item(
        "FRSHE",
        "Shell Recharge France",
    ),
    Item(
        "FRSHL",
        "Shell Recharge",
    ),
    Item(
        "FRSIG",
        "Syndicat intercommunal pour le gaz et l'électricité en Île-de-France (SIGEIF)",
    ),
    Item(
        "FRSIP",
        "SIPPEREC",
    ),
    Item(
        "FRSJS",
        "SJS SERVICES",
    ),
    Item(
        "FRSLF",
        "SAP Labs France",
    ),
    Item(
        "FRSMI",
        "WATTZHUB",
    ),
    Item(
        "FRSOD",
        "Sodetrel",
    ),
    Item(
        "FRSPS",
        "Réseau de bornes électriques Shell France",
    ),
    Item(
        "FRSSD",
        "DRIVECO",
    ),
    Item(
        "FRSTB",
        "ST2B",
    ),
    Item(
        "FRSUA",
        "COOPERATIVE U ENSEIGNE",
    ),
    Item(
        "FRSUN",
        "e-nergyze",
    ),
    Item(
        "FRSWC",
        "SOWATT SOLUTIONS CPO",
    ),
    Item(
        "FRSWI",
        "Swish",
    ),
    Item(
        "FRSWS",
        "SOWATT SOLUTIONS",
    ),
    Item(
        "FRSYS",
        "See You Sun",
    ),
    Item(
        "FRT2P",
        "Time2Plug",
    ),
    Item(
        "FRTCB",
        "Réseau Total Business",
    ),
    Item(
        "FRTDA",
        "Bornes 50 kW Thevenin & Ducrot Autoroutes",
    ),
    Item(
        "FRTEC",
        "TECHEM",
    ),
    Item(
        "FRTLS",
        "TOULIBEO",
    ),
    Item(
        "FRTNM",
        "Shell Recharge",
    ),
    Item(
        "FRTSC",
        "TESLA SUPERCHARGER",
    ),
    Item(
        "FRTSL",
        "Tesla",
    ),
    Item(
        "FRUBI",
        "ubitricity",
    ),
    Item(
        "FRURW",
        "Réseau UNIBAIL",
    ),
    Item(
        "FRV05",
        "Ville de Rosheim",
    ),
    Item(
        "FRV07",
        "IRVE Sablé sur Sarthe",
    ),
    Item(
        "FRV09",
        "Ville de Vic-sur-Cère",
    ),
    Item(
        "FRV12",
        "Ville d'Avray",
    ),
    Item(
        "FRV14",
        "Ville de Revel",
    ),
    Item(
        "FRV15",
        "Ville de Pleaux",
    ),
    Item(
        "FRV16",
        "Ville de Viriat",
    ),
    Item(
        "FRV17",
        "Ville de Murat",
    ),
    Item(
        "FRV18",
        "Ville de la Ciotat",
    ),
    Item(
        "FRV19",
        "Ville de Garches",
    ),
    Item(
        "FRV20",
        "Ville de Bresse Vallons",
    ),
    Item(
        "FRV21",
        "Ville de Blagnac",
    ),
    Item(
        "FRV51",
        "Communauté urbaine du Grand Reims",
    ),
    Item(
        "FRV75",
        "Belib'",
    ),
    Item(
        "FRVEV",
        "VEV Services Limited",
    ),
    Item(
        "FRVGF",
        "VGF Volkswagen Group France",
    ),
    Item(
        "FRVIA",
        "ENGIE Vianeo",
    ),
    Item(
        "FRVIS",
        "Enrvision",
    ),
    Item(
        "FRVLT",
        "Volta Charging",
    ),
    Item(
        "FRW10",
        "WAAT",
    ),
    Item(
        "FRW11",
        "WAAT",
    ),
    Item(
        "FRWA1",
        "WAAT",
    ),
    Item(
        "FRWA2",
        "WAAT",
    ),
    Item(
        "FRWA3",
        "WAAT",
    ),
    Item(
        "FRWA4",
        "WAAT",
    ),
    Item(
        "FRWA5",
        "WAAT",
    ),
    Item(
        "FRWA6",
        "WAAT",
    ),
    Item(
        "FRWA7",
        "WAAT",
    ),
    Item(
        "FRWA8",
        "WAAT",
    ),
    Item(
        "FRWA9",
        "WAAT",
    ),
    Item(
        "FRWAT",
        "WAAT",
    ),
    Item(
        "FRWBC",
        "WELLBORNE",
    ),
    Item(
        "FRWGO",
        "WE-GO",
    ),
    Item(
        "FRWRN",
        "Werenode",
    ),
    Item(
        "FRX75",
        "borne de recharge sur candélabre Paris",
    ),
    Item(
        "FRY01",
        "SEYMABORNE - Communauté urbaine Grand Paris Seine et Oise",
    ),
    Item(
        "FRY02",
        "SEYMABORNE - Communauté de communes des Portes de l’Île-de-France",
    ),
    Item(
        "FRY03",
        "SEYMABORNE - Syndicat d'Energie des Yvelines",
    ),
    Item(
        "FRY04",
        "SEYMABORNE - Ville de BEYNES",
    ),
    Item(
        "FRY05",
        "SEYMABORNE - Ville de BOUGIVAL",
    ),
    Item(
        "FRY06",
        "SEYMABORNE - Ville de COIGNIERES",
    ),
    Item(
        "FRY07",
        "SEYMABORNE - Ville de COURGENT",
    ),
    Item(
        "FRY08",
        "SEYMABORNE - Ville de DAMMARTIN EN SERVE",
    ),
    Item(
        "FRY09",
        "SEYMABORNE - Ville de FEUCHEROLLES",
    ),
    Item(
        "FRY10",
        "SEYMABORNE - Ville de HOUILLES",
    ),
    Item(
        "FRY11",
        "SEYMABORNE - Ville de JOUARS PONTCHARTRAIN",
    ),
    Item(
        "FRY12",
        "SEYMABORNE - Ville de JOUY LE MOUTIER",
    ),
    Item(
        "FRY13",
        "SEYMABORNE - Ville de LA VILLENEUVE EN CHEVRIE",
    ),
    Item(
        "FRY14",
        "SEYMABORNE - Ville de LE MESNIL LE ROI",
    ),
    Item(
        "FRY15",
        "SEYMABORNE - Ville de LE PORT MARLY",
    ),
    Item(
        "FRY16",
        "SEYMABORNE - Ville de L'ETANG LA VILLE",
    ),
    Item(
        "FRY17",
        "SEYMABORNE - Ville de LE TREMBLAY SUR MAULDRE",
    ),
    Item(
        "FRY18",
        "SEYMABORNE - Ville de LOUVECIENNES",
    ),
    Item(
        "FRY19",
        "SEYMABORNE - Ville de MAREIL MARLY",
    ),
    Item(
        "FRY20",
        "SEYMABORNE - Ville de MARLY LE ROI",
    ),
    Item(
        "FRY21",
        "SEYMABORNE - Ville de MAUREPAS",
    ),
    Item(
        "FRY22",
        "SEYMABORNE - Ville de MERE",
    ),
    Item(
        "FRY23",
        "SEYMABORNE - Ville de NEAUPHLE-LE-CHÂTEAU",
    ),
    Item(
        "FRY24",
        "SEYMABORNE - Ville de NOISY LE ROI",
    ),
    Item(
        "FRY25",
        "SEYMABORNE - Ville de PLAISIR",
    ),
    Item(
        "FRY26",
        "SEYMABORNE - Ville de SAINT NOM LA BRETECHE",
    ),
    Item(
        "FRY27",
        "SEYMABORNE - Ville de SEPTEUIL",
    ),
    Item(
        "FRY28",
        "SEYMABORNE - Ville de THIVERVAL-GRIGNON",
    ),
    Item(
        "FRY29",
        "SEYMABORNE - Ville de THOIRY",
    ),
    Item(
        "FRY30",
        "SEYMABORNE - Ville de TOUSSUS LE NOBLE",
    ),
    Item(
        "FRY31",
        "SEYMABORNE - Ville de VILLEPREUX",
    ),
    Item(
        "FRY32",
        "SEYMABORNE - Ville de BONNIERES SUR SEINE",
    ),
    Item(
        "FRY33",
        "SEYMABORNE - Ville de MAULE",
    ),
    Item(
        "FRY34",
        "SEYMABORNE - Ville de FRENEUSE",
    ),
    Item(
        "FRY35",
        "SEYMABORNE - Ville de CRESPIERES",
    ),
    Item(
        "FRY36",
        "SEYMABORNE - Ville de CHAMBOURCY",
    ),
    Item(
        "FRY55",
        "YES55",
    ),
    Item(
        "FRZAR",
        "Aramis - ZEborneMS",
    ),
    Item(
        "FRZBK",
        "Burger King - ZEborne",
    ),
    Item(
        "FRZHO",
        "Hôtellerie - ZEborne",
    ),
    Item(
        "FRZHR",
        "ZEborne - Hôtellerie Restauration",
    ),
    Item(
        "FRZIM",
        "Intermarché - ZEborneMS",
    ),
    Item(
        "FRZKA",
        "Kia - ZEborneMS",
    ),
    Item(
        "FRZMA",
        "Mazda - ZEborne",
    ),
    Item(
        "FRZP1",
        "ZEPHYRE",
    ),
    Item(
        "FRZPE",
        "Professionnel Entreprise - ZEborneMS",
    ),
    Item(
        "FRZSU",
        "SuperU - ZeborneMS",
    ),
    Item(
        "FRZTL",
        "Toyota/Lexus - ZEborne",
    ),
    Item(
        "FRZUN",
        "ZUNDER",
    ),
    # Update: 2025/02/05
    Item(
        "FR0CU",
        "Charge Unix",
    ),
    Item(
        "FR190",
        "Watt'up",
    ),
    Item(
        "FRALL",
        "Allego France",
    ),
    Item(
        "FRALN",
        "ALDI SARL",
    ),
    Item(
        "FRBCF",
        "BE CHARGE",
    ),
    Item(
        "FRBEZ",
        "Ville de Béziers",
    ),
    Item(
        "FRBFC",
        "Citeos pour le compte du réseau de recharge en Bourgogne-Franche-Comté",
    ),
    Item(
        "FRBPE",
        "bp pulse",
    ),
    Item(
        "FRCG1",
        "ChargeGuru",
    ),
    Item(
        "FRCVT",
        "Covolt",
    ),
    Item(
        "FRECP",
        "ProperPhi",
    ),
    Item(
        "FREKL",
        "EKLEO Montlouis-sur-Loire",
    ),
    Item(
        "FRELE",
        "Electrip",
    ),
    Item(
        "FRELT",
        "ELTO",
    ),
    Item(
        "FREMO",
        "E-MOTUM",
    ),
    Item(
        "FRENT",
        "Enerstock Charging Station",
    ),
    Item(
        "FRERA",
        "Eranovum e-Mobility",
    ),
    Item(
        "FREVE",
        "FAROAD",
    ),
    Item(
        "FRFZD",
        "Fuzed",
    ),
    Item(
        "FRHDA",
        "Réseau PL de AS24",
    ),
    Item(
        "FRHDT",
        "Réseau PL de TotalEnergies",
    ),
    Item(
        "FRHOP",
        "HOPLA POWER CHARGE",
    ),
    Item(
        "FRJBA",
        "E-MOTUM",
    ),
    Item(
        "FRMBX",
        "Mercedes-Benz High Power Charging GmbH",
    ),
    Item(
        "FRMEI",
        "Mob-Energy",
    ),
    Item(
        "FRORV",
        "O'TERRE",
    ),
    Item(
        "FRPLM",
        "Prologis Mobility",
    ),
    Item(
        "FRPY2",
        "AVIA PICOTY",
    ),
    Item(
        "FRRVE",
        "REVEO",
    ),
    Item(
        "FRSLM",
        "SPLM Société Publique Lyonnaise de Mobilités",
    ),
    Item(
        "FRUB2",
        "ubitricity France",
    ),
    Item(
        "FRUSC",
        "Voltalia Mobility",
    ),
    Item(
        "FRVAY",
        "vaylens GmbH",
    ),
    Item(
        "FRVIR",
        "VIRTA Global France",
    ),
    Item(
        "FRWII",
        "Bornes W:I",
    ),
    Item(
        "FRYAW",
        "Yaway",
    ),
    Item(
        "FRZMR",
        "ZEborne Mobility Service - France",
    ),
    # Update: 2025/04/08
    Item(
        "FR151",
        "PORT DE CAEN OUISTREHAM",
    ),
    Item(
        "FRBE3",
        "Bouygues Energies & Services",
    ),
    Item(
        "FRBLR",
        "MBLR",
    ),
    Item(
        "FRCHF",
        "CHARGEFACILE",
    ),
    Item(
        "FRCHO",
        "ChargeHop",
    ),
    Item(
        "FRDLM",
        "Delmonicos",
    ),
    Item(
        "FRGLY",
        "IZIVIA Grand Lyon",
    ),
    Item(
        "FRHM1",
        "HEMERA MOBILITY",
    ),
    Item(
        "FRIMX",
        "IZIVIA MAX",
    ),
    Item(
        "FRITP",
        "Interparking France ",
    ),
    Item(
        "FRQVI",
        "QOVOLTIS Infra",
    ),
    Item(
        "FRSPI",
        "Spirii FR",
    ),
    Item(
        "FRYES",
        "YES55",
    ),
    # Update: 2025/05/20
    Item(
        "FRCPB",
        "Camping Les Pins Bleus",
    ),
    Item(
        "FRIGF",
        "Izivia Grand Frais",
    ),
    Item(
        "FRILF",
        "IZIVIA Impact LF",
    ),
    Item(
        "FRMBZ",
        "Mobilize Power Solutions",
    ),
    Item(
        "FRZET",
        "INTHY Distribution",
    ),
]

prefixes = [item.code for item in data]

# Create operational units
operational_units = [
    OperationalUnit(
        name=item.name, code=item.code, type=OperationalUnitTypeEnum.CHARGING
    )
    for item in data
]
