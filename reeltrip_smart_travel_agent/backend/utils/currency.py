"""
Currency formatting helpers.
"""
import locale

# Currency symbol map
CURRENCY_SYMBOLS = {
    "INR": "\u20b9",   # ₹
    "USD": "$",
    "EUR": "\u20ac",   # €
    "GBP": "\u00a3",   # £
    "AED": "AED ",
    "JPY": "\u00a5",   # ¥
    "CNY": "\u00a5",   # ¥
    "AUD": "A$",
    "CAD": "C$",
    "SGD": "S$",
    "THB": "\u0e3f",   # ฿
    "MYR": "RM ",
    "KRW": "\u20a9",   # ₩
    "IDR": "Rp ",
    "PHP": "\u20b1",   # ₱
    "VND": "\u20ab",   # ₫
    "BRL": "R$",
    "MXN": "MX$",
    "ZAR": "R ",
    "TRY": "\u20ba",   # ₺
    "RUB": "\u20bd",   # ₽
    "CHF": "CHF ",
    "SEK": "kr ",
    "NOK": "kr ",
    "DKK": "kr ",
    "NZD": "NZ$",
    "HKD": "HK$",
    "TWD": "NT$",
    "SAR": "SAR ",
    "QAR": "QAR ",
    "KWD": "KWD ",
    "BHD": "BHD ",
    "OMR": "OMR ",
    "EGP": "E\u00a3",
    "LKR": "Rs ",
    "PKR": "Rs ",
    "BDT": "\u09f3",   # ৳
    "NPR": "Rs ",
}


def format_currency(amount: float, currency_code: str = "INR") -> str:
    """
    Format a number as currency with the appropriate symbol.

    Examples:
        format_currency(22642, "INR") -> "₹22,642"
        format_currency(500.50, "USD") -> "$501"
        format_currency(1234567, "INR") -> "₹12,34,567"
    """
    currency_code = currency_code.upper()
    symbol = CURRENCY_SYMBOLS.get(currency_code, f"{currency_code} ")

    # Round to nearest integer for cleaner display
    rounded = round(amount)

    # Format with commas (Indian numbering for INR, standard for others)
    if currency_code == "INR":
        formatted = _indian_number_format(rounded)
    else:
        formatted = f"{rounded:,}"

    return f"{symbol}{formatted}"


def _indian_number_format(number: int) -> str:
    """
    Format number in Indian numbering system.
    12,34,567 instead of 1,234,567
    """
    s = str(abs(number))
    if len(s) <= 3:
        return s

    # Last 3 digits
    result = s[-3:]
    s = s[:-3]

    # Group remaining digits in pairs
    while s:
        result = s[-2:] + "," + result
        s = s[:-2]

    if number < 0:
        return "-" + result
    return result
