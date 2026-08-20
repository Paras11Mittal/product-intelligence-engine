import asyncio
import json
from app.schemas.input_schema import ProductEnrichRequest
from app.services.orchestrator import ProductIntelligenceOrchestrator

async def main():
    print("=" * 80)
    print(" AI Orchestration & Product Intelligence Engine Demo")
    print("=" * 80)

    test_cases = [
        {
            "brand": "Bosch",
            "mpn": "GSR 18V-55",
            "description": "Professional 18V cordless drill driver with brushless motor and 55Nm max torque"
        },
        {
            "brand": "Apple",
            "mpn": "MRX33LL/A",
            "description": "MacBook Pro 14-inch with M3 Pro chip, 18GB Unified Memory, 512GB SSD"
        },
        {
            "brand": "Fluke",
            "mpn": "Fluke-117",
            "description": "Electricians Multimeter with Non-Contact Voltage Detection CAT III 600V"
        }
    ]

    orchestrator = ProductIntelligenceOrchestrator()

    for idx, tc in enumerate(test_cases, 1):
        print(f"\n[Test Case {idx}] Input: Brand='{tc['brand']}', MPN='{tc['mpn']}'")
        print(f"Description: '{tc['description']}'")
        print("-" * 80)

        req = ProductEnrichRequest(**tc)
        result = await orchestrator.run_pipeline(req)

        print("Output Summary:")
        print(f"  • Product Title      : {result['commerce']['title']}")
        print(f"  • Category Path      : {' > '.join(result['classification']['category_path'])}")
        print(f"  • Total Specs Found  : {len(result['specifications'])}")
        print(f"  • Verified Specs     : {result['confidence']['verified_attributes_count']}")
        print(f"  • Conflicts Handled  : {len(result['conflicts'])}")
        print(f"  • Overall Confidence : {result['confidence']['overall_score']}")

        print("\nFull JSON Payload:")
        print(json.dumps(result, indent=2))
        print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
