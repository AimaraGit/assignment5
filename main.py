
from app import suggest_product

def main():
    print("=" * 40)
    print("  Welcome to Weather-Based Order System")
    print("=" * 40)

    name = input("\nEnter your name: ")
    city = input("Enter your city: ")
    
    print("\nWhat is the weather like?")
    print("  1. Rain")
    print("  2. Sunny")
    print("  3. Snow")
    
    choice = input("\nEnter 1, 2 or 3: ").strip()

    conditions = {
        "1": "rain",
        "2": "sunny",
        "3": "snow"
    }

    if choice not in conditions:
        print("\n❌ Invalid choice. Please enter 1, 2 or 3.")
        return

    condition = conditions[choice]

    temperature = input("Enter the temperature (e.g. 25): ").strip()

    weather = {"condition": condition, "temperature": float(temperature)}
    product = suggest_product(weather)

    print("\n" + "=" * 40)
    print(f"  Hello, {name} from {city}!")
    print(f"  Weather: {condition}, {temperature}°C")
    print(f"  🛍️  We suggest you buy: {product.upper()}")
    print("=" * 40)

if __name__ == "__main__":
    main()