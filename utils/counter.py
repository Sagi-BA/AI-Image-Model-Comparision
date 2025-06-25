import os
import streamlit as st
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve the COUNTER value from the .env file
def get_user_count(formatted=False):
    count = os.getenv('COUNTER', '0')
    try:
        count = int(count)
    except ValueError:
        count = 0
    
    if formatted:
        return format_count(count)
    
    return count

def increment_user_count():
    count = get_user_count() + 1
    os.environ['COUNTER'] = str(count)  # This will only update the current session.
    return count

def decrement_user_count():
    count = max(0, get_user_count() - 1)
    os.environ['COUNTER'] = str(count)  # This will only update the current session.
    return count

def format_count(count):
    """Format the count with commas and round to nearest thousand if over 1000"""    
    if count >= 1000:
        return f"{count:,}"
    return f"{count:,}"

# Example usage
if __name__ == "__main__":
    current_count = get_user_count()
    st.write(f"Current user count: {format_count(current_count)}")
    
    incremented_count = increment_user_count()
    st.write(f"User count after increment: {format_count(incremented_count)}")
    
    decremented_count = decrement_user_count()
    st.write(f"User count after decrement: {format_count(decremented_count)}")
