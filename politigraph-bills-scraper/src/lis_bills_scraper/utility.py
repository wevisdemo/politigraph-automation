from datetime import datetime

def convert_thai_date_to_universal(thai_date_str:str) -> str:
    
    # Parse the date string in the format dd/mm/yyyy
    dt_object = datetime.strptime(thai_date_str, '%d/%m/%Y')
    
    # Check whether the year is valid
    if dt_object.year < 2500: # year if already in Gregorian year
        # TODO update this before the year 2100 or successfully achieve Open Parliament
        year_2_digit = int(str(dt_object.year)[2:])
        gregorian_year = 2000 + year_2_digit
    else:
        # Convert the Thai year to Gregorian year by subtracting 543
        gregorian_year = dt_object.year - 543

    # Create a new datetime object with the corrected year
    universal_dt_object = dt_object.replace(year=gregorian_year)

    # Format the new datetime object into the desired yyyy-mm-dd string format
    return universal_dt_object.strftime('%Y-%m-%d')