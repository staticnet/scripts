#!/usr/bin/env python3
import requests
import json
import os
import sys

# Pre-configured API keys (replace with your actual credentials)
API_CREDENTIALS = {
    "X-CP-API-ID": "YOUR_CP_API_ID",
    "X-CP-API-KEY": "YOUR_CP_API_KEY",
    "X-ECM-API-ID": "YOUR_ECM_API_ID",
    "X-ECM-API-KEY": "YOUR_ECM_API_KEY"
}

BASE_URL = "https://www.cradlepointecm.com/api/v2"

def get_headers():
    """Return the headers with API credentials"""
    headers = API_CREDENTIALS.copy()
    headers["Content-Type"] = "application/json"
    return headers

def find_router():
    """Interactive function to find a router by MAC or Serial Number"""
    print("\n🔍 Router Lookup")
    print("----------------")
    
    while True:
        user_input = input("Enter Router MAC Address or Serial Number (or 'q' to quit): ").strip()
        
        if user_input.lower() == 'q':
            print("Exiting...")
            sys.exit(0)
            
        identifier = user_input.replace(":", "").replace("-", "").lower()
        
        # Determine search method based on input format
        if len(identifier) == 12 and all(c in "0123456789abcdef" for c in identifier):
            url = f"{BASE_URL}/routers/"
            params = {"mac": identifier, "fields": "id,name,serial_number,product"}
            search_type = "MAC Address"
        else:
            url = f"{BASE_URL}/routers/"
            params = {"serial_number": identifier, "fields": "id,name,serial_number,product"}
            search_type = "Serial Number"
        
        print(f"\nSearching for router with {search_type}: {user_input}...")
        
        try:
            response = requests.get(url, headers=get_headers(), params=params)
            response.raise_for_status()
            
            routers = response.json().get("data", [])
            if routers:
                router = routers[0]
                print(f"\n✅ Found Router: {router['name']} (S/N: {router['serial_number']})")
                return router
            else:
                print(f"\n❌ No router found with that {search_type}. Please try again.")
                
        except requests.exceptions.RequestException as e:
            print(f"\n❌ API Error: {str(e)}")
            print("Please check your API credentials and try again.")
            if input("Try again? (y/n): ").lower() != 'y':
                sys.exit(1)

def get_tos_text():
    """Interactive function to get Terms of Service text directly from user input"""
    print("\n📝 Terms of Service Text Entry")
    print("---------------------------")
    print("You can either enter the text directly, paste it, or enter a file path.")
    
    choice = input("How would you like to provide the Terms of Service text?\n1. Enter/paste text now\n2. Load from file\nEnter choice (1 or 2): ").strip()
    
    if choice == "2":
        return select_tos_file()
        
    print("\nEnter your Terms of Service text below. When finished, type ':done' on a new line and press Enter.")
    print("-----------------------------------------------")
    
    lines = []
    while True:
        line = input()
        if line.strip() == ':done':
            break
        lines.append(line)
    
    tos_content = "\n".join(lines)
    
    print(f"\n✅ Captured {len(tos_content)} characters of Terms of Service text.")
    
    preview_length = min(200, len(tos_content))
    print(f"\nPreview of content (first {preview_length} characters):")
    print("-" * 50)
    print(tos_content[:preview_length] + "..." if len(tos_content) > preview_length else tos_content)
    print("-" * 50)
    
    if input("\nIs this the correct text? (y/n): ").lower() != 'y':
        print("Let's try again.")
        return get_tos_text()
        
    return tos_content

def select_tos_file():
    """Function to select a Terms of Service file"""
    print("\n📝 Terms of Service File Selection")
    print("--------------------------------")
    
    while True:
        file_path = input("Enter the path to your Terms of Service file (or 'q' to quit): ").strip()
        
        if file_path.lower() == 'q':
            print("Exiting...")
            sys.exit(0)
        
        try:
            if not os.path.exists(file_path):
                print(f"\n❌ File not found: {file_path}")
                continue
                
            with open(file_path, 'r') as f:
                tos_content = f.read()
                
            print(f"\n✅ Loaded file: {file_path}")
            print(f"File size: {len(tos_content)} characters")
            
            preview_length = min(200, len(tos_content))
            print(f"\nPreview of content (first {preview_length} characters):")
            print("-" * 50)
            print(tos_content[:preview_length] + "..." if len(tos_content) > preview_length else tos_content)
            print("-" * 50)
            
            if input("\nIs this the correct file? (y/n): ").lower() == 'y':
                return tos_content
                
        except Exception as e:
            print(f"\n❌ Error reading file: {str(e)}")

def update_tos(router_id, new_tos_text):
    """Update the Terms of Service for a router using the configuration manager"""
    print("\n🔄 Updating Terms of Service")
    print("--------------------------")
    
    # First, get the configuration manager ID for this router
    print("Looking up configuration manager for this router...")
    config_url = f"{BASE_URL}/configuration_managers/"
    params = {"router.id": router_id, "fields": "id"}
    
    try:
        response = requests.get(config_url, headers=get_headers(), params=params)
        response.raise_for_status()
        
        config_managers = response.json().get("data", [])
        if not config_managers:
            print("\n❌ Configuration Manager not found for this router.")
            return False
            
        config_manager_id = config_managers[0]["id"]
        print(f"Found configuration manager ID: {config_manager_id}")
        
        # Now update using the configuration manager endpoint
        print("Sending Terms of Service update...")
        update_url = f"{BASE_URL}/configuration_managers/{config_manager_id}/"
        
        # Use the correct format with nested text field
        payload = {
            "configuration": [
                {
                    "hotspot": {
                        "tos": {
                            "text": new_tos_text
                        }
                    }
                },
                []  # Second element is for removed configuration items
            ]
        }
        
        response = requests.patch(update_url, headers=get_headers(), json=payload)
        
        # 202 Accepted is a success code for asynchronous operations
        if response.status_code in [200, 202]:
            if response.status_code == 202:
                print("\n✅ Terms of Service update accepted! (Status 202)")
                print("The update has been queued and will be applied when the router connects.")
            else:
                print("\n✅ Terms of Service updated successfully!")
            # Exit immediately on success - don't try alternative approach
            return True
        else:
            # Only try alternative approach if the first attempt failed
            print(f"\n❌ Update failed with status {response.status_code}")
            print(f"Error details: {response.text}")
            
            print("\nTrying alternative approach...")
            alt_payload = {
                "configuration": [
                    {
                        "hotspot": {
                            "tos": new_tos_text
                        }
                    },
                    []
                ]
            }
            
            alt_response = requests.patch(update_url, headers=get_headers(), json=alt_payload)
            
            if alt_response.status_code in [200, 202]:
                if alt_response.status_code == 202:
                    print("\n✅ Terms of Service update accepted with alternative format! (Status 202)")
                    print("The update has been queued and will be applied when the router connects.")
                else:
                    print("\n✅ Terms of Service updated successfully with alternative format!")
                return True
            else:
                print(f"\n❌ All update attempts failed.")
                print(f"Last error: {alt_response.status_code} - {alt_response.text}")
                return False
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ API Error: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Error details: {e.response.text}")
        return False

def main():
    """Main function to run the interactive script"""
    print("\n🚀 Cradlepoint Terms of Service Updater 🚀")
    print("=========================================")
    print("This script will help you update the Terms of Service for a Cradlepoint router.")
    
    # Check if API credentials are set
    if "YOUR_CP_API_ID" in API_CREDENTIALS["X-CP-API-ID"]:
        print("\n⚠️  Warning: Default API credentials detected!")
        print("Please edit the script to add your actual API credentials.")
        if input("Continue anyway? (y/n): ").lower() != 'y':
            sys.exit(1)
    
    # Step 1: Find the router
    router = find_router()
    
    # Step 2: Get the ToS content - either from user input or file
    tos_content = get_tos_text()
    
    # Step 3: Confirm the update
    print("\n📋 Update Summary")
    print("---------------")
    print(f"Router Name: {router['name']}")
    print(f"Serial Number: {router['serial_number']}")
    print(f"Terms of Service: {len(tos_content)} characters")
    
    if input("\nProceed with update? (y/n): ").lower() == 'y':
        update_tos(router['id'], tos_content)
    else:
        print("\nUpdate canceled.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user. Exiting...")
        sys.exit(0)