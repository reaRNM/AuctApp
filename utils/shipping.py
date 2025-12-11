# utils/shipping.py
import math

# Official 2025 USPS Ground Advantage Retail - Zone 9 Rates
# Source: Book1.pdf (Pages 4-6)

ZONE_9_RATES = {
    # Weight (lbs) -> Price ($)
    1: 12.45, 2: 17.15, 3: 20.10, 4: 22.20, 5: 23.75,
    6: 25.80, 7: 27.75, 8: 30.00, 9: 32.20, 10: 35.50,
    11: 39.85, 12: 42.65, 13: 46.55, 14: 50.00, 15: 52.15,
    16: 54.35, 17: 56.95, 18: 59.55, 19: 61.45, 20: 62.65,
    21: 70.65, 22: 75.95, 23: 79.85, 24: 83.10, 25: 86.25,
    26: 93.20, 27: 96.35, 28: 99.15, 29: 101.80, 30: 104.40,
    31: 107.00, 32: 109.55, 33: 112.05, 34: 114.45, 35: 116.95,
    36: 119.25, 37: 121.70, 38: 124.00, 39: 126.25, 40: 128.50,
    41: 130.75, 42: 132.90, 43: 135.05, 44: 137.10, 45: 139.20,
    46: 141.20, 47: 143.20, 48: 145.10, 49: 147.05, 50: 148.90,
    51: 150.65, 52: 152.45, 53: 154.20, 54: 155.95, 55: 157.60,
    56: 159.20, 57: 160.80, 58: 162.35, 59: 163.80, 60: 165.35,
    61: 166.70, 62: 168.15, 63: 169.45, 64: 170.80, 65: 172.05,
    66: 173.35, 67: 174.50, 68: 175.60, 69: 176.70, 70: 177.80
}

OVERSIZED_PRICE = 263.00 #

def estimate_shipping(lbs: float, oz: float = 0, length: float = 0, width: float = 0, height: float = 0) -> float:
    """
    Returns the exact USPS Ground Advantage Retail (Zone 9) shipping cost.
    Includes logic for Dimensional Weight, Oversized packages, and Nonstandard Length/Volume fees.
    """
    # 1. Calculate Total Weight
    total_lbs = lbs + (oz / 16.0)
    
    # 2. Dimensions Logic (Surcharges & Dim Weight)
    surcharge = 0.0
    is_oversized = False
    
    if length and width and height:
        # Sort dimensions to find Length (longest side)
        dims = sorted([length, width, height], reverse=True)
        L, W, H = dims[0], dims[1], dims[2]
        
        # Calculate Girth (2*W + 2*H)
        girth = 2 * (W + H)
        combined_length_girth = L + girth
        
        # Oversized Check (L + Girth > 108" and <= 130")
        if combined_length_girth > 108:
            if combined_length_girth <= 130:
                is_oversized = True
            else:
                return 0.0 # Exceeds USPS max size
        
        # Dimensional Weight (If Volume > 1 cu ft)
        volume_cu_ft = (L * W * H) / 1728.0
        if volume_cu_ft > 1:
            # Retail Dim Divisor is 166 (Standard USPS Retail rule)
            dim_weight = (L * W * H) / 166.0
            if dim_weight > total_lbs:
                total_lbs = dim_weight

        # Nonstandard Fees
        # Length > 22" but <= 30" -> Add $4.00
        if 22 < L <= 30:
            surcharge += 4.00
        # Length > 30" -> Add $8.40
        elif L > 30:
            surcharge += 8.40
            
        # Volume > 2 cu ft -> Add $18.00
        if volume_cu_ft > 2:
            surcharge += 18.00

    # 3. Determine Base Price
    price = 0.0
    
    if is_oversized:
        price = OVERSIZED_PRICE
    else:
        # Check Ounce Tiers (Under 1 lb)
        if total_lbs < 1.0:
            if total_lbs <= 0.25:   price = 8.40  # 4 oz
            elif total_lbs <= 0.50: price = 9.25  # 8 oz
            elif total_lbs <= 0.75: price = 11.10 # 12 oz
            else:                   price = 12.45 # 15.999 oz
        else:
            # Round up to next full pound
            rated_weight = math.ceil(total_lbs)
            
            # Lookup in table
            if rated_weight in ZONE_9_RATES:
                price = ZONE_9_RATES[rated_weight]
            elif rated_weight > 70:
                price = 0.0 # Over 70lbs limit for Ground Advantage
            else:
                price = 12.45 # Fallback (Should not happen if table is complete)

    if price == 0:
        return 0.0 # Error state (too heavy/large)

    return price + surcharge