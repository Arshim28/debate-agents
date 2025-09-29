"""
Dynamic date and financial year utilities for the dialectical agent system
"""

from datetime import datetime
from typing import Tuple, Dict, Any

def get_current_financial_context() -> Dict[str, Any]:
    """
    Get current financial year and quarter context dynamically.

    Indian Financial Year: April 1 - March 31
    Q1: April - June
    Q2: July - September
    Q3: October - December
    Q4: January - March

    Returns:
        Dict containing current date, FY, quarter, and formatted strings
    """
    now = datetime.now()

    # Determine financial year
    if now.month >= 4:  # April onwards = current calendar year FY
        fy_year = now.year + 1
        fy_start_year = now.year
    else:  # January-March = previous calendar year FY
        fy_year = now.year
        fy_start_year = now.year - 1

    # Determine quarter
    if 4 <= now.month <= 6:  # April-June
        quarter = 1
        quarter_name = "Q1"
        quarter_months = "April-June"
    elif 7 <= now.month <= 9:  # July-September
        quarter = 2
        quarter_name = "Q2"
        quarter_months = "July-September"
    elif 10 <= now.month <= 12:  # October-December
        quarter = 3
        quarter_name = "Q3"
        quarter_months = "October-December"
    else:  # January-March
        quarter = 4
        quarter_name = "Q4"
        quarter_months = "January-March"

    # Build context
    context = {
        "current_date": now,
        "current_date_str": now.strftime("%B %d, %Y"),
        "current_date_short": now.strftime("%Y-%m-%d"),
        "financial_year": fy_year,
        "financial_year_str": f"FY{str(fy_year)[2:]}",
        "financial_year_full": f"FY{fy_year} (April {fy_start_year} - March {fy_year})",
        "quarter": quarter,
        "quarter_name": quarter_name,
        "quarter_full": f"{quarter_name} FY{str(fy_year)[2:]}",
        "quarter_period": f"{quarter_name} FY{str(fy_year)[2:]} ({quarter_months} {fy_start_year if quarter <= 3 else fy_year})",
        "half_year": "H1" if quarter <= 2 else "H2",
        "half_year_full": f"H1 FY{str(fy_year)[2:]}" if quarter <= 2 else f"H2 FY{str(fy_year)[2:]}"
    }

    return context

def get_previous_quarters(current_context: Dict[str, Any], num_quarters: int = 2) -> list:
    """
    Get previous quarters for reference in queries.

    Args:
        current_context: Output from get_current_financial_context()
        num_quarters: Number of previous quarters to return

    Returns:
        List of quarter strings for recent periods
    """
    quarters = []
    fy_year = current_context["financial_year"]
    current_quarter = current_context["quarter"]

    for i in range(1, num_quarters + 1):
        q = current_quarter - i
        year = fy_year

        if q <= 0:
            q = 4 + q  # Wrap around to previous FY
            year = fy_year - 1

        quarters.append(f"Q{q} FY{str(year)[2:]}")

    return quarters

if __name__ == "__main__":
    # Test the function
    context = get_current_financial_context()
    print("Financial Context:")
    for key, value in context.items():
        print(f"  {key}: {value}")

    print(f"\nPrevious quarters: {get_previous_quarters(context, 3)}")