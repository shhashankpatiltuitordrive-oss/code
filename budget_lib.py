# budget_lib.py
# This module handles budget calculations and analysis logic

def calculate_budget(grocery_logs, budget):
    """
    Calculate total grocery cost and return budget status.

    Parameters:
    grocery_logs (list): List of grocery items with price and quantity
    budget (float): User budget

    Returns:
    dict: Contains total cost, status, and suggestion
    """

    total_cost = sum(item.price * item.quantity for item in grocery_logs)

    status = "within_budget"
    suggestion = "Good job managing budget"

    if total_cost > budget:
        status = "over_budget"
        suggestion = "Reduce quantity or choose cheaper items"

    return {
        "total_cost": total_cost,
        "status": status,
        "suggestion": suggestion
    }