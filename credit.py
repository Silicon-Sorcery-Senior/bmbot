def can(active_credit):
	if (active_credit == 'Yes'):
		return False
	else:
		return True

def calculate_interest_days(amount):
	return int(amount) / 100

def calculate_total(initial, interest, interest_days):
	return int(initial) * (1 + float(interest) / 100) ** int(interest_days)
