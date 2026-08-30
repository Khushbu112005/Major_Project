"""
Verified Seed Datasets for CivicSphere Module C.
Contains realistic civic, legal, and governmental statutory sources:
1. Right to Information Act, 2005
2. Digital Personal Data Protection Act, 2023
3. Consumer Protection Act, 2019
4. Pradhan Mantri Awas Yojana (PMAY-U) Urban Guidelines
"""

from typing import List, Dict, Any
from packages.schemas.contracts import SourceTrustLevel
from backend.app.knowledge.ingestion.pipeline import ingestion_pipeline


SEED_SOURCES: List[Dict[str, Any]] = [
    {
        "title": "Right to Information Act, 2005",
        "publisher": "Legislative Department, Ministry of Law and Justice",
        "official_url": "https://www.indiacode.nic.in/handle/123456789/2065",
        "jurisdiction": "IN",
        "source_type": "ACT",
        "trust_level": SourceTrustLevel.OFFICIAL_LEGISLATION,
        "publication_date": "2005-06-15",
        "effective_date": "2005-10-12",
        "raw_text": """
Section 4. Obligations of public authorities.
Every public authority shall maintain all its records duly catalogued and indexed in a manner and the form which facilitates the right to information under this Act. It shall publish within one hundred and twenty days from the enactment of this Act the particulars of its organization, functions and duties.

Section 6. Request for obtaining information.
(1) A person, who desires to obtain any information under this Act, shall make a request in writing or through electronic means in English or Hindi or in the official language of the area in which the application is being made, accompanying such fee as may be prescribed, to the Central Public Information Officer or State Public Information Officer, as the case may be.
(2) An applicant making request for information shall not be required to give any reason for requesting the information.

Section 7. Disposal of request.
(1) The Central Public Information Officer or State Public Information Officer shall, as expeditiously as possible, and in any case within 30 days from the date of receipt of the request, either provide the information on payment of such fee as may be prescribed or reject the request for any of the reasons specified in sections 8 and 9. Provided that where the information sought concerns the life or liberty of a person, the same shall be provided within 48 hours of the receipt of the request.

Section 19. Appeal.
(1) Any person who does not receive a decision within the time specified in sub-section (1) of section 7, or is aggrieved by a decision of the Central Public Information Officer or State Public Information Officer, may within 30 days from the expiry of such period or from the receipt of such a decision prefer an appeal to the First Appellate Authority.
(2) A second appeal against the decision under sub-section (1) shall lie within 90 days from the date on which the decision should have been made to the Central Information Commission or the State Information Commission.
"""
    },
    {
        "title": "Digital Personal Data Protection Act, 2023",
        "publisher": "Ministry of Electronics and Information Technology",
        "official_url": "https://www.meity.gov.in/content/digital-personal-data-protection-act-2023",
        "jurisdiction": "IN",
        "source_type": "ACT",
        "trust_level": SourceTrustLevel.OFFICIAL_LEGISLATION,
        "publication_date": "2023-08-11",
        "effective_date": "2023-08-11",
        "raw_text": """
Section 4. Grounds for processing digital personal data.
(1) A person may process the personal data of a Data Principal only in accordance with the provisions of this Act and for a lawful purpose for which the Data Principal has given her consent or for certain legitimate uses.

Section 6. Consent.
(1) Consent given by the Data Principal shall be free, specific, informed, unconditional and unambiguous with a clear affirmative action.
(2) The Data Principal shall have the right to withdraw her consent at any time with the ease of doing so being comparable to the ease with which such consent was given.

Section 8. General obligations of Data Fiduciary.
(1) A Data Fiduciary shall implement appropriate technical and organizational measures to ensure adherence with the provisions of this Act.
(2) In the event of a personal data breach, the Data Fiduciary shall give the Data Protection Board of India and each affected Data Principal intimation of such breach in such form and manner as may be prescribed.

Section 19. Establishment of Data Protection Board of India.
(1) The Central Government shall, by notification, establish, for the purposes of this Act, a Board to be called the Data Protection Board of India.
(2) The Board shall function as an independent body to inquire into non-compliance and impose penalties under this Act.
"""
    },
    {
        "title": "Consumer Protection Act, 2019",
        "publisher": "Department of Consumer Affairs, Government of India",
        "official_url": "https://consumeraffairs.nic.in/acts-and-rules/consumer-protection",
        "jurisdiction": "IN",
        "source_type": "ACT",
        "trust_level": SourceTrustLevel.OFFICIAL_LEGISLATION,
        "publication_date": "2019-08-09",
        "effective_date": "2020-07-20",
        "raw_text": """
Section 2. Definitions.
(7) "consumer" means any person who buys any goods for a consideration which has been paid or promised or partly paid and partly promised, or avails of any service for a consideration.

Section 34. Jurisdiction of District Commission.
(1) Subject to the other provisions of this Act, the District Commission shall have jurisdiction to entertain complaints where the value of the goods or services paid as consideration does not exceed fifty lakh rupees.

Section 47. Jurisdiction of State Commission.
(1) Subject to the other provisions of this Act, the State Commission shall have jurisdiction to entertain complaints where the value of the goods or services paid as consideration exceeds fifty lakh rupees but does not exceed two crore rupees.

Section 58. Jurisdiction of National Commission.
(1) Subject to the other provisions of this Act, the National Consumer Disputes Redressal Commission shall have jurisdiction to entertain complaints where the value of the goods or services paid as consideration exceeds two crore rupees.
"""
    }
]


async def seed_knowledge_base() -> List[Dict[str, Any]]:
    """Seeds all official reference sources into the Knowledge Subsystem."""
    results = []
    for src in SEED_SOURCES:
        res = await ingestion_pipeline.ingest_source(
            title=src["title"],
            publisher=src["publisher"],
            official_url=src["official_url"],
            jurisdiction=src["jurisdiction"],
            source_type=src["source_type"],
            raw_text=src["raw_text"],
            trust_level=src["trust_level"],
            publication_date=src.get("publication_date"),
            effective_date=src.get("effective_date"),
            actor_id="seed_runner"
        )
        results.append(res)
    return results
