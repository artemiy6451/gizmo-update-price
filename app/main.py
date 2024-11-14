from dataclasses import dataclass
import requests
import json

BASE_URL = "http://192.168.88.100:607"

@dataclass
class User:
    id: int
    name: str
    discount: float

@dataclass
class Product:
    id: int
    name: str
    price: int
    cost: int | None

@dataclass
class UserPrices:
    user_id: int
    price: int
    user_price_id: int

@dataclass
class Prices:
    product_id: int
    product_name: str
    base_price: int
    user_prices: list[UserPrices]

users: list[User] = [
    User(3, "Boss", 0.50),
    User(5, "Администрация", 0.75),
    User(6, "-10%", 1.10),
    User(8, "5%", 0.95),
    User(9, "15%", 0.85),
    User(10, "3%", 0.97),
    User(11, "7%", 0.93),
]

headers = {
    "Authorization": "Basic YWRtaW46YWRtaW4=",
    "Content-Type": "application/json",
    "accept": "application/json"
}


def custom_round(number: int):
    return round(number / 5) * 5


def get_all_avaliable_products() -> list[Product]:
    url = f"{BASE_URL}/api/products"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return []
    
    raw_products = response.json()
    parsed_products: list[Product] = []
    for product in raw_products["result"]:
        if product["isDeleted"]:
            continue
        parsed_products.append(
            Product(
                product["id"], 
                product["name"],
                product["price"], 
                product["cost"]
            )
        )

    return parsed_products


def get_user_price_id(product_id, user_id) -> int | None:
    url = f"{BASE_URL}/api/v2.0/products/{product_id}/userprices"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return None
    
    users = response.json()
    for user in users["result"]:
        if int(user["userGroupId"]) == user_id:
            return user["id"]

    return None


def get_prices_for_all_users(products: list[Product]) -> list[Prices]:
    prices: list[Prices] = []
    for product in products:
        user_prices: list[UserPrices] = []
        for user in users:
            user_price_id=get_user_price_id(product.id, user.id)
            if user_price_id is None:
                continue

            # if user.id == 3:
                # if product.cost is None:
                    # product.cost = 0
                # user_prices.append(
                    # UserPrices(
                        # user_id=user.id,
                        # price=int(product.cost),
                        # user_price_id=user_price_id
                    # )
                # )
            # else:
            user_prices.append(
                UserPrices(
                    user_id=user.id,
                    price=custom_round(int(product.price*user.discount)),
                    user_price_id=user_price_id
                )
            )
            
        prices.append(
            Prices(
                product_id=product.id,
                product_name=product.name,
                base_price=int(product.price),
                user_prices=user_prices
            )
        )
    return prices


def update_price(prices: Prices):
    url = f"{BASE_URL}/api/v2.0/products/userprices"
    for user in prices.user_prices:
        data = {
          "id": user.user_price_id,
          "productId": prices.product_id,
          "userGroupId": user.user_id,
          "price": user.price,
          "pointsPrice": 0,
          "purchaseOptions": 0,
          "isEnabled": True
        }
        data = json.dumps(data)
        response = requests.put(url, headers=headers, data=data)
        if not response.ok:
            print(f"""
            Can not update price for product: {prices.product_name}
            With error {response.json()}
            """)
            break
    else:
        print(f"{prices.product_id}) Updated all prices for item: {prices.product_name}")


products = get_all_avaliable_products()
prices = get_prices_for_all_users(products)
for price in prices:
    update_price(price)
