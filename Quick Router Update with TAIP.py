#This Python Script allows you to easily modify the basics of a Cradlepoint Router for a installer without having direct NCM access. This is perfect for vehicle router swaps since we have the TAIP ID element.
#Change the API Keys with your Account Keys. This Script is by Robert Edwards.

import requests
from getpass import getpass

# API Credentials (Replace with your actual credentials)
HEADERS = {
    "X-CP-API-ID":   "YOUR_CP_API_ID",
    "X-CP-API-KEY":  "YOUR_CP_API_KEY",
    "X-ECM-API-ID":  "YOUR_ECM_API_ID",
    "X-ECM-API-KEY": "YOUR_ECM_API_KEY",
    "Content-Type":  "application/json"
}

BASE_URL = "https://www.cradlepointecm.com/api/v2"


def find_router():
    """Find router by MAC or Serial Number"""
    user_input = input("Enter Router MAC Address or Serial Number: ").strip()
    mac = user_input.replace(":", "").replace("-", "").lower()
    lookup_field = "mac" if len(mac) == 12 else "serial_number"

    url = f"{BASE_URL}/routers/"
    params = {"fields": "id,name,serial_number,product,configuration_manager", lookup_field: user_input}
    response = requests.get(url, headers=HEADERS, params=params)

    if response.ok:
        routers = response.json().get("data", [])
        if routers:
            router = routers[0]
            print(f"\n✅ Found Router: {router['name']} ({router['serial_number']})")
            return router
        else:
            print("\n❌ Router not found.")
            return None
    else:
        print(f"\n❌ Error: {response.status_code} - {response.text}")
        return None


def rename_router(router_id):
    """Rename the router"""
    new_name = input("Enter new router name: ").strip()
    url = f"{BASE_URL}/routers/{router_id}/"
    payload = {"name": new_name}

    response = requests.put(url, headers=HEADERS, json=payload)
    if response.ok:
        print(f"✅ Router renamed to {new_name}")
    else:
        print(f"❌ Failed to rename router: {response.text}")


def get_valid_groups(product):
    """Fetch valid groups that match the router's product type"""
    url = f"{BASE_URL}/groups/"
    params = {"limit": 200, "fields": "id,name,product"}
    response = requests.get(url, headers=HEADERS, params=params)

    if response.ok:
        groups = response.json().get("data", [])
        valid_groups = [group for group in groups if group.get("product") == product]

        if valid_groups:
            print("\nAvailable Groups:")
            for i, group in enumerate(valid_groups, start=1):
                print(f"{i}. {group['name']} (ID: {group['id']})")

            return valid_groups
        else:
            print("\n❌ No valid groups found for this router type.")
            return []
    else:
        print(f"\n❌ Error fetching groups: {response.text}")
        return []


def move_router(router_id, product):
    """Move the router to a valid group"""
    valid_groups = get_valid_groups(product)
    if not valid_groups:
        return

    choice = input("\nSelect a group number (or press ENTER to skip): ").strip()
    if choice.isdigit() and 1 <= int(choice) <= len(valid_groups):
        group_id = valid_groups[int(choice) - 1]["id"]
        group_url = f"{BASE_URL}/groups/{group_id}/"
        url = f"{BASE_URL}/routers/{router_id}/"
        payload = {"group": group_url}

        response = requests.put(url, headers=HEADERS, json=payload)
        if response.ok:
            print(f"✅ Router moved to group {valid_groups[int(choice) - 1]['name']}")
        else:
            print(f"❌ Failed to move router: {response.text}")
    else:
        print("❌ Invalid group selection. Skipping group change.")


def update_taip(router_id):
    """Update the TAIP ID"""
    new_taip = input("Enter new TAIP Vehicle ID: ").strip()
    url = f"{BASE_URL}/configuration_managers/"
    params = {"router.id": router_id, "fields": "id"}

    response = requests.get(url, headers=HEADERS, params=params)
    if not response.ok:
        print(f"❌ Failed to retrieve configuration manager: {response.status_code}")
        return

    config_managers = response.json().get("data", [])
    if not config_managers:
        print("❌ Configuration Manager ID not found.")
        return

    config_manager_id = config_managers[0]["id"]

    update_url = f"{BASE_URL}/configuration_managers/{config_manager_id}/?fields=configuration"
    payload = {
        "configuration": [
            {
                "system": {
                    "gps": {
                        "taip_vehicle_id": new_taip
                    }
                }
            },
            []
        ]
    }

    response = requests.patch(update_url, headers=HEADERS, json=payload)
    if response.ok:
        print(f"✅ TAIP ID updated to {new_taip}")
    else:
        print(f"❌ Failed to update TAIP ID: {response.text}")


def main():
    print("\n🚀 Cradlepoint Router Management CLI 🚀")

    router = find_router()
    if not router:
        return

    router_id = router["id"]
    product = router.get("product", "Unknown")

    print("\n🔹 Options:")
    print("1. Rename Router")
    print("2. Move to a Group")
    print("3. Update TAIP ID")
    print("4. Exit")

    while True:
        choice = input("\nSelect an option: ").strip()
        if choice == "1":
            rename_router(router_id)
        elif choice == "2":
            move_router(router_id, product)
        elif choice == "3":
            update_taip(router_id)
        elif choice == "4":
            print("✅ Exiting CLI. Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please select a valid option.")


if __name__ == "__main__":
    main()
