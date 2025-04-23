"""
External API integration service.
Provides connections to external travel data APIs.
"""

import os
import logging
import requests
import json
from datetime import datetime, timedelta
from app.utils.caching import cache_expensive_operation

# API keys
FLIGHT_API_KEY = os.getenv("FLIGHT_API_KEY", "")
HOTEL_API_KEY = os.getenv("HOTEL_API_KEY", "")

@cache_expensive_operation(key="flight_prices", ttl_seconds=3600)  # Cache for 1 hour
def get_flight_prices(origin, destination, departure_date, return_date=None):
    """
    Get flight prices from external API.
    
    Args:
        origin: Origin airport code (e.g., 'JFK')
        destination: Destination airport code (e.g., 'LAX')
        departure_date: Departure date (YYYY-MM-DD)
        return_date: Return date (YYYY-MM-DD)
        
    Returns:
        dict: Flight price information
    """
    if not FLIGHT_API_KEY:
        logging.warning("Flight API key not configured")
        return {
            "success": False,
            "message": "Flight API not configured",
            "prices": []
        }
    
    try:
        # Convert city names to airport codes if needed
        origin_code = get_airport_code(origin)
        destination_code = get_airport_code(destination)
        
        # Format dates
        departure_date_str = departure_date.strftime('%Y-%m-%d') if isinstance(departure_date, datetime) else departure_date
        
        if return_date:
            return_date_str = return_date.strftime('%Y-%m-%d') if isinstance(return_date, datetime) else return_date
            trip_type = "round"
        else:
            return_date_str = None
            trip_type = "oneway"
        
        # API endpoint
        url = f"https://skyscanner-api.p.rapidapi.com/v3/flights/live/search/create"
        
        # Request payload
        payload = {
            "query": {
                "market": "US",
                "locale": "en-US",
                "currency": "USD",
                "queryLegs": [
                    {
                        "originPlaceId": {"iata": origin_code},
                        "destinationPlaceId": {"iata": destination_code},
                        "date": departure_date_str
                    }
                ],
                "adults": 1,
                "cabinClass": "CABIN_CLASS_ECONOMY"
            }
        }
        
        # Add return leg if round trip
        if return_date_str:
            payload["query"]["queryLegs"].append({
                "originPlaceId": {"iata": destination_code},
                "destinationPlaceId": {"iata": origin_code},
                "date": return_date_str
            })
        
        headers = {
            "content-type": "application/json",
            "X-RapidAPI-Key": FLIGHT_API_KEY,
            "X-RapidAPI-Host": "skyscanner-api.p.rapidapi.com"
        }
        
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code != 200:
            logging.error(f"Flight API error: {response.status_code} - {response.text}")
            return {
                "success": False,
                "message": f"API error: {response.status_code}",
                "prices": []
            }
            
        data = response.json()
        
        # Process and extract relevant information
        prices = []
        if 'content' in data and 'results' in data['content'] and 'itineraries' in data['content']['results']:
            itineraries = data['content']['results']['itineraries']
            for key, itinerary in itineraries.items():
                if 'pricingOptions' in itinerary:
                    for option in itinerary['pricingOptions']:
                        price = option.get('price', {}).get('amount')
                        if price:
                            agent = option.get('items', [{}])[0].get('agentName', 'Unknown')
                            prices.append({
                                "price": price,
                                "agent": agent,
                                "trip_type": trip_type,
                                "origin": origin_code,
                                "destination": destination_code,
                                "departure_date": departure_date_str,
                                "return_date": return_date_str
                            })
        
        # Sort by price
        prices.sort(key=lambda x: x['price'])
        
        return {
            "success": True,
            "message": "Successfully retrieved flight prices",
            "prices": prices[:5]  # Return top 5 cheapest options
        }
        
    except Exception as e:
        logging.error(f"Error getting flight prices: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "prices": []
        }

@cache_expensive_operation(key="hotel_prices", ttl_seconds=3600)  # Cache for 1 hour
def get_hotel_prices(city, country, check_in_date, check_out_date, guest_count=1):
    """
    Get hotel prices from external API.
    
    Args:
        city: City name
        country: Country name
        check_in_date: Check-in date (YYYY-MM-DD)
        check_out_date: Check-out date (YYYY-MM-DD)
        guest_count: Number of guests
        
    Returns:
        dict: Hotel price information
    """
    if not HOTEL_API_KEY:
        logging.warning("Hotel API key not configured")
        return {
            "success": False,
            "message": "Hotel API not configured",
            "hotels": []
        }
    
    try:
        # Format dates
        check_in_str = check_in_date.strftime('%Y-%m-%d') if isinstance(check_in_date, datetime) else check_in_date
        check_out_str = check_out_date.strftime('%Y-%m-%d') if isinstance(check_out_date, datetime) else check_out_date
        
        # Get destination ID
        destination_id = get_destination_id(city, country)
        if not destination_id:
            return {
                "success": False,
                "message": f"Could not find destination ID for {city}, {country}",
                "hotels": []
            }
        
        # API endpoint
        url = "https://booking-com.p.rapidapi.com/v1/hotels/search"
        
        # Query parameters
        params = {
            "dest_id": destination_id,
            "dest_type": "city",
            "units": "metric",
            "room_number": "1",
            "adults_number": str(guest_count),
            "checkin_date": check_in_str,
            "checkout_date": check_out_str,
            "filter_by_currency": "USD",
            "locale": "en-us",
            "order_by": "price",
            "page_number": "0",
            "include_adjacency": "true"
        }
        
        headers = {
            "X-RapidAPI-Key": HOTEL_API_KEY,
            "X-RapidAPI-Host": "booking-com.p.rapidapi.com"
        }
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code != 200:
            logging.error(f"Hotel API error: {response.status_code} - {response.text}")
            return {
                "success": False,
                "message": f"API error: {response.status_code}",
                "hotels": []
            }
            
        data = response.json()
        
        # Process and extract relevant information
        hotels = []
        if 'result' in data:
            for hotel in data['result']:
                price = hotel.get('price_breakdown', {}).get('gross_price', 0)
                hotels.append({
                    "name": hotel.get('hotel_name', 'Unknown'),
                    "price": price,
                    "currency": hotel.get('price_breakdown', {}).get('currency', 'USD'),
                    "stars": hotel.get('hotel_class', 0),
                    "address": hotel.get('address', 'Unknown'),
                    "review_score": hotel.get('review_score', 0),
                    "checkin_date": check_in_str,
                    "checkout_date": check_out_str
                })
        
        return {
            "success": True,
            "message": "Successfully retrieved hotel prices",
            "hotels": hotels[:5]  # Return top 5 options
        }
        
    except Exception as e:
        logging.error(f"Error getting hotel prices: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "hotels": []
        }

@cache_expensive_operation(key="airport_code", ttl_seconds=86400)  # Cache for 24 hours
def get_airport_code(city_name):
    """
    Get airport code for a city.
    
    Args:
        city_name: Name of the city
        
    Returns:
        str: Airport code (e.g., 'JFK')
    """
    # Hardcoded mapping for common cities
    city_to_airport = {
        "new york": "JFK",
        "los angeles": "LAX",
        "chicago": "ORD",
        "san francisco": "SFO",
        "boston": "BOS",
        "london": "LHR",
        "paris": "CDG",
        "berlin": "BER",
        "rome": "FCO",
        "madrid": "MAD",
        "tokyo": "HND",
        "beijing": "PEK",
        "sydney": "SYD",
        "dubai": "DXB"
    }
    
    # Normalize city name
    city_normalized = city_name.lower().strip()
    
    # Check if in mapping
    if city_normalized in city_to_airport:
        return city_to_airport[city_normalized]
    
    # If not found, use an API call (limited implementation for now)
    try:
        if FLIGHT_API_KEY:
            url = "https://skyscanner-api.p.rapidapi.com/v3/geo/hierarchy/flights"
            
            headers = {
                "X-RapidAPI-Key": FLIGHT_API_KEY,
                "X-RapidAPI-Host": "skyscanner-api.p.rapidapi.com"
            }
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                # Search for the city in the response
                if 'places' in data:
                    for place in data['places']:
                        if place.get('type') == 'PLACE_TYPE_CITY' and city_normalized in place.get('name', '').lower():
                            # Find the associated airport
                            for airport in data['places']:
                                if airport.get('type') == 'PLACE_TYPE_AIRPORT' and airport.get('parentId') == place.get('id'):
                                    return airport.get('iata')
        
        # Fallback to a default code
        logging.warning(f"Could not find airport code for {city_name}, using default")
        return city_name[:3].upper()
        
    except Exception as e:
        logging.error(f"Error getting airport code: {str(e)}")
        return city_name[:3].upper()

@cache_expensive_operation(key="destination_id", ttl_seconds=86400)  # Cache for 24 hours
def get_destination_id(city, country):
    """
    Get destination ID for hotel search.
    
    Args:
        city: City name
        country: Country name
        
    Returns:
        str: Destination ID
    """
    if not HOTEL_API_KEY:
        return None
    
    try:
        url = "https://booking-com.p.rapidapi.com/v1/hotels/locations"
        
        params = {
            "name": f"{city}, {country}",
            "locale": "en-us"
        }
        
        headers = {
            "X-RapidAPI-Key": HOTEL_API_KEY,
            "X-RapidAPI-Host": "booking-com.p.rapidapi.com"
        }
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code != 200:
            logging.error(f"Location API error: {response.status_code} - {response.text}")
            return None
            
        data = response.json()
        
        # Find the first city result
        for location in data:
            if location.get('dest_type') == 'city':
                return location.get('dest_id')
        
        return None
        
    except Exception as e:
        logging.error(f"Error getting destination ID: {str(e)}")
        return None