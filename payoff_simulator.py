def simulate_payoff(loan_amount, rate, years, current_payment):
    """
    Simulate payoff for a given rate and term.
    """
    r = rate / 100 / 12
    n = years * 12
    try:
        monthly_payment = loan_amount * r * (1 + r)**n / ((1 + r)**n - 1)
    except ZeroDivisionError:
        monthly_payment = loan_amount / n
    total_payment = monthly_payment * n
    interest_paid = total_payment - loan_amount

    return {
        'Estimated Monthly Payment': f"${monthly_payment:.2f}",
        'Total Payment Over Loan': f"${total_payment:.2f}",
        'Total Interest Paid': f"${interest_paid:.2f}",
        'Current Monthly Payment': f"${current_payment:.2f}",
        'Potential Savings': f"${(current_payment * n) - total_payment:.2f}"
    }
