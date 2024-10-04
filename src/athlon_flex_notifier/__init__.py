import requests
from pydantic import BaseModel
import os

username = os.getenv("ATHLON_USERNAME")
password = os.getenv("ATHLON_PASSWORD")
session = requests.Session()
base_url = "https://flex.athlon.com/api/v1"


class Profile(BaseModel):
    class Budget(BaseModel):
        actualBudgetPerMonth: int
        maxBudgetPerMonth: int
        normBudgetPerMonth: int
        normBudgetGasolinePerMonth: int
        normBudgetElectricPerMonth: int
        maxBudgetGasolinePerMonth: int
        maxBudgetElectricPerMonth: int
        normUndershootPercentage: int
        maxNormUndershootPercentage: int
        savedBudget: int
        savedBudgetPayoutAllowed: bool
        holidayCarRaiseAllowed: bool

    requiresIncludeTaxInPrices: bool
    includeMileageCostsInPricing: bool
    includeFuelCostsInPricing: bool
    numberOfKmPerMonth: int
    remainingSwaps: int
    budget: Budget


class Car(BaseModel):
    firstVehicleId: str
    externalTypeId: str
    make: str
    model: str
    latestModelYear: int
    vehicleCount: int
    minPriceInEuroPerMonth: float
    fiscalValueInEuro: float
    additionPercentage: float
    externalFuelTypeId: int
    maxCO2Emission: int
    imageUri: str


def login() -> None:
    endpoint = "MemberLogin"

    response = session.post(
        f"{base_url}/{endpoint}",
        json={"username": "aucke.bos97@gmail.com", "password": ""},
    )
    response.raise_for_status()


def get_profile() -> Profile:
    endpoint = "MemberProfile"
    response = session.get(f"{base_url}/{endpoint}")
    response.raise_for_status()
    return Profile(**response.json())


def get_cars(profile: Profile) -> list[Car]:
    endpoint = "VehicleCluster"
    params = {
        "Filters.Segment": "Cars",
        "Filters.IncludeTaxInPrices": profile.requiresIncludeTaxInPrices,
        "Filters.MaxPricePerMonth": profile.budget.maxBudgetPerMonth,
        "Filters.NumberOfKmPerMonth": profile.numberOfKmPerMonth,
        "Filters.IncludeMileageCostsInPricing": profile.includeMileageCostsInPricing,
        "Filters.IncludeFuelCostsInPricing": profile.includeFuelCostsInPricing,
    }
    response = session.get(f"{base_url}/{endpoint}", params=params)
    response.raise_for_status()
    return [Car(**car) for car in response.json()]


def main():
    login()
    profile = get_profile()
    cars = get_cars(profile)


if __name__ == "__main__":
    main()
