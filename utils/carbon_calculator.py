class CarbonCalculator:
    def __init__(self):
        # CO2 reduction values per waste category (kg CO2 equivalent)
        self.category_values = {
            'biodegradable': {
                'co2_saved': 0.5,
                'description': 'Composting avoids methane emissions from landfills'
            },
            'recyclable': {
                'co2_saved': 1.2,
                'description': 'Recycling saves energy and raw materials'
            },
            'hazardous': {
                'co2_saved': 2.5,
                'description': 'Proper disposal prevents toxic emissions'
            }
        }
        
        # Equivalents for better understanding
        self.equivalents = {
            'trees_saved_per_kg': 0.02,  # One tree absorbs ~50kg CO2 per year
            'car_miles_per_kg': 4,  # Average car emits ~0.25kg CO2 per mile
            'phone_charges_per_kg': 120  # Smartphone charge ~0.0083kg CO2
        }
    
    def calculate_savings(self, category, quantity=1):
        """Calculate carbon savings for a waste item"""
        if category not in self.category_values:
            return {
                'co2_saved': 0,
                'category': category,
                'quantity': quantity
            }
        
        value = self.category_values[category]
        total_co2 = value['co2_saved'] * quantity
        
        return {
            'co2_saved': round(total_co2, 2),
            'category': category,
            'quantity': quantity,
            'description': value['description']
        }
    
    def get_equivalents(self, co2_kg):
        """Convert CO2 savings to relatable equivalents"""
        trees_saved = co2_kg * self.equivalents['trees_saved_per_kg']
        car_miles_avoided = co2_kg * self.equivalents['car_miles_per_kg']
        phone_charges = co2_kg * self.equivalents['phone_charges_per_kg']
        
        return {
            'trees_saved': round(trees_saved, 1),
            'car_miles_avoided': round(car_miles_avoided, 1),
            'phone_charges': round(phone_charges, 0),
            'co2_kg': round(co2_kg, 2)
        }
    
    def calculate_batch_savings(self, waste_items):
        """Calculate total savings from multiple waste items"""
        total_co2 = 0
        category_breakdown = {}
        
        for item in waste_items:
            category = item.get('category')
            quantity = item.get('quantity', 1)
            
            if category in self.category_values:
                savings = self.category_values[category]['co2_saved'] * quantity
                total_co2 += savings
                
                if category in category_breakdown:
                    category_breakdown[category] += savings
                else:
                    category_breakdown[category] = savings
        
        return {
            'total_co2': round(total_co2, 2),
            'category_breakdown': category_breakdown,
            'equivalents': self.get_equivalents(total_co2)
        }
    
    def get_sustainability_score(self, total_co2, total_items):
        """Calculate sustainability score based on impact"""
        if total_items == 0:
            return 0
        
        # Base score on average CO2 saved per item
        avg_co2_per_item = total_co2 / total_items
        max_possible = max(v['co2_saved'] for v in self.category_values.values())
        
        # Score from 0-100
        score = (avg_co2_per_item / max_possible) * 100
        
        # Bonus for quantity (more items = more impact)
        quantity_bonus = min(total_items * 0.5, 20)  # Max 20 points bonus
        
        final_score = min(score + quantity_bonus, 100)
        
        return round(final_score, 1)