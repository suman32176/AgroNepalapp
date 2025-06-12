from django import template

register = template.Library()

@register.filter
def div(value, arg):
    """Divide value by arg."""
    try:
        return value / arg
    except (ZeroDivisionError, TypeError):
        return 0  # Return 0 if division by zero or invalid value

@register.filter
def mul(value, arg):
    """Multiply value by arg."""
    try:
        return value * arg
    except (TypeError, ValueError):
        return 0  # Return 0 in case of invalid input (e.g., None or non-numeric values)
    
    

@register.filter
def average_rating(reviews):
    if not reviews:
        return 0
    total = sum(review.rating for review in reviews)
    return total / len(reviews)



@register.filter(name='add_class')
def add_class(field, css):
    return field.as_widget(attrs={"class": css})


@register.filter(name='multiply')
def multiply(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0