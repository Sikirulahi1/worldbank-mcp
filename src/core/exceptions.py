"""Shared exception hierarchy for worldbank-mcp."""


class WorldBankMCPError(Exception):
    pass


class WorldBankAPIError(WorldBankMCPError):
    pass


class WorldBankTimeoutError(WorldBankAPIError):
    pass


class WorldBankConnectionError(WorldBankAPIError):
    pass


class WorldBankHTTPStatusError(WorldBankAPIError):
    pass


class WorldBankRateLimitError(WorldBankAPIError):
    pass


class WorldBankResponseError(WorldBankAPIError):
    pass


class MetadataParseError(WorldBankAPIError):
    pass


class CountryResolutionError(WorldBankMCPError):
    pass


class IndicatorValidationError(WorldBankMCPError):
    pass


class ExportError(WorldBankMCPError):
    """Raised when writing a file fails."""


class UnsupportedFormatError(WorldBankMCPError):
    """Raised when an unsupported export format is requested."""
