"""50-Industry to ETF mapping for US economy framework.

Maps 50 distinct US economy industries to their most representative
liquid ETFs for performance tracking.
"""

from typing import Optional


class IndustryMapper:
    """Static mapping of 50 industries to representative ETFs."""

    # Comprehensive 50-industry framework mapped to liquid ETFs
    INDUSTRY_ETF_MAP = {
        # Technology (8)
        "Software": "IGV",
        "Semiconductors": "SOXX",
        "Cloud Computing": "CLOU",
        "Cybersecurity": "HACK",
        "Artificial Intelligence": "BOTZ",
        "Internet": "FDN",
        "Hardware": "XLK",
        "Telecommunications": "VOX",

        # Healthcare (6)
        "Biotechnology": "IBB",
        "Pharmaceuticals": "XPH",
        "Healthcare Providers": "IHF",
        "Medical Devices": "IHI",
        "Managed Care": "XLV",
        "Healthcare REIT": "VHT",

        # Financials (7)
        "Banks": "KBE",
        "Insurance": "KIE",
        "Asset Management": "PFM",
        "Fintech": "FINX",
        "REITs": "VNQ",
        "Payments": "IPAY",
        "Regional Banks": "KRE",

        # Consumer (8)
        "Retail": "XRT",
        "E-Commerce": "IBUY",
        "Consumer Staples": "XLP",
        "Consumer Discretionary": "XLY",
        "Restaurants": "PBJ",
        "Apparel": "IYK",
        "Automotive": "CARZ",
        "Luxury Goods": "LUXE",

        # Energy & Materials (5)
        "Oil & Gas": "XLE",
        "Renewable Energy": "ICLN",
        "Mining": "XME",
        "Steel": "SLX",
        "Chemicals": "XLB",

        # Industrials (5)
        "Aerospace & Defense": "ITA",
        "Transportation": "XTN",
        "Construction": "ITB",
        "Logistics": "FTXR",
        "Industrials": "XLI",

        # Real Estate & Infrastructure (4)
        "Real Estate": "IYR",
        "Infrastructure": "PAVE",
        "Homebuilders": "XHB",
        "Commercial Real Estate": "INDS",

        # Communications & Media (3)
        "Media": "PBS",
        "Entertainment": "PEJ",
        "Social Media": "SOCL",

        # Other (4)
        "Utilities": "XLU",
        "Agriculture": "DBA",
        "Cannabis": "MSOS",
        "ESG": "ESGU",
    }

    @classmethod
    def get_all_industries(cls) -> list[str]:
        """Get list of all 50 industries.

        Returns:
            List of industry names sorted alphabetically.
        """
        return sorted(cls.INDUSTRY_ETF_MAP.keys())

    @classmethod
    def get_etf(cls, industry: str) -> Optional[str]:
        """Get ETF ticker for an industry.

        Args:
            industry: Industry name (case-insensitive).

        Returns:
            ETF ticker symbol or None if industry not found.
        """
        # Case-insensitive lookup
        for ind, etf in cls.INDUSTRY_ETF_MAP.items():
            if ind.lower() == industry.lower():
                return etf
        return None

    @classmethod
    def get_industry(cls, etf: str) -> Optional[str]:
        """Get industry name for an ETF ticker.

        Args:
            etf: ETF ticker symbol (case-insensitive).

        Returns:
            Industry name or None if ETF not found.
        """
        etf_upper = etf.upper()
        for industry, ticker in cls.INDUSTRY_ETF_MAP.items():
            if ticker == etf_upper:
                return industry
        return None

    @classmethod
    def get_all_etfs(cls) -> list[str]:
        """Get list of all ETF tickers.

        Returns:
            List of ETF tickers.
        """
        return list(cls.INDUSTRY_ETF_MAP.values())

    @classmethod
    def get_industry_etf_pairs(cls) -> list[dict[str, str]]:
        """Get list of all industry → ETF mappings.

        Returns:
            List of dicts with 'industry' and 'etf' keys.
        """
        return [
            {"industry": industry, "etf": etf}
            for industry, etf in sorted(cls.INDUSTRY_ETF_MAP.items())
        ]

    @classmethod
    def validate_industry(cls, industry: str) -> bool:
        """Check if an industry exists in the mapping.

        Args:
            industry: Industry name to validate.

        Returns:
            True if industry exists, False otherwise.
        """
        return cls.get_etf(industry) is not None

    @classmethod
    def get_count(cls) -> int:
        """Get total number of industries tracked.

        Returns:
            Number of industries (should always be 50).
        """
        return len(cls.INDUSTRY_ETF_MAP)
