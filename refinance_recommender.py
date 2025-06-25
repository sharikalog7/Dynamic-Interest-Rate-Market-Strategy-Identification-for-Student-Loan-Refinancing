def recommend_refinance_options(loan_amount, income, credit_score, predicted_rate):
    """
    Returns a list of refinancing options with links to real lenders.
    """
    options = []
    lenders = [
        {
            "lender": "SoFi",
            "url": "https://www.sofi.com/refinance-student-loan/",
            "rate_adj": 0.0,
            "term_years": 10
        },
        {
            "lender": "Earnest",
            "url": "https://www.earnest.com/student-loan-refinancing",
            "rate_adj": 0.2,
            "term_years": 15
        },
        {
            "lender": "LendKey",
            "url": "https://www.lendkey.com/student-loan-refinancing/",
            "rate_adj": -0.2,
            "term_years": 7
        }
    ]
    # Simple eligibility check
    if credit_score >= 600 and income > 20000:
        for lender in lenders:
            rate = round(predicted_rate + lender["rate_adj"], 2)
            options.append({
                "Lender": lender["lender"],
                "Link": lender["url"],
                "Rate (%)": rate,
                "Term (years)": lender["term_years"]
            })
    return options
