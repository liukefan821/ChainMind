"""
agent_simulator.py — Simulates an LLM-powered DeFi agent generating decisions.

Uses Ollama (local LLM) to generate DeFi risk assessments and trade recommendations,
then creates DecisionRecord objects for Merkle tree commitment.

Author: Kefan Liu
Project: ChainMind — NBC'26
"""

import json
import time
import requests
from typing import List, Optional
from merkle_tree import DecisionRecord


# ======================== Configuration ========================

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:7b"
MODEL_VERSION = "qwen2.5-7b-instruct"

# DeFi scenarios for simulation
DEFI_SCENARIOS = [
    {
        "protocol": "Uniswap V3",
        "action": "Provide liquidity",
        "pair": "ETH/USDC",
        "context": "ETH price is $3,200, 24h volume is $1.2B, current pool TVL is $450M. "
                   "The fee tier is 0.3%. Recent impermanent loss for this range is -2.1%."
    },
    {
        "protocol": "Aave V3",
        "action": "Supply & Borrow",
        "pair": "WBTC collateral / USDT borrow",
        "context": "WBTC supply APY is 0.12%, USDT borrow APY is 4.8%. "
                   "Health factor would be 1.65. Liquidation threshold is 75%."
    },
    {
        "protocol": "Compound V3",
        "action": "Leverage yield farming",
        "pair": "ETH/USDC loop",
        "context": "Base supply rate 2.1%, reward rate 1.8%. Net APY after 3x leverage: ~8.2%. "
                   "Gas costs for rebalancing: ~$15 per tx. Portfolio size: $50,000."
    },
    {
        "protocol": "MakerDAO",
        "action": "Open CDP vault",
        "pair": "ETH collateral / DAI mint",
        "context": "Stability fee is 3.5%. Liquidation ratio 150%. "
                   "ETH 30d volatility is 45%. Current collateral ratio would be 185%."
    },
    {
        "protocol": "Curve Finance",
        "action": "Stablecoin swap",
        "pair": "USDC → USDT via 3pool",
        "context": "Pool balance: USDC 35%, USDT 33%, DAI 32%. Swap size: $500,000. "
                   "Expected slippage: 0.01%. Recent depeg risk score: LOW."
    },
    {
        "protocol": "Lido",
        "action": "Liquid staking",
        "pair": "ETH → stETH",
        "context": "Current staking APR: 3.8%. stETH/ETH peg: 0.9998. "
                   "Withdrawal queue: ~3 days. Validator set size: 370,000."
    },
    {
        "protocol": "GMX",
        "action": "Perpetual long",
        "pair": "ETH-USD 5x long",
        "context": "Entry price $3,200, liquidation at $2,720. Funding rate: +0.01%/hr. "
                   "Open interest: $180M long vs $120M short. 24h volume: $890M."
    },
    {
        "protocol": "Pendle Finance",
        "action": "Yield tokenization",
        "pair": "stETH PT/YT split",
        "context": "PT discount: 4.2% (maturity: 6 months). Implied yield: 8.4% APY. "
                   "YT price: 0.038 ETH. Underlying stETH yield: 3.8%."
    },
    {
        "protocol": "Morpho Blue",
        "action": "Optimized lending",
        "pair": "WETH/USDC market",
        "context": "Utilization rate: 87%. Supply APY: 3.2% (vs Aave 1.8%). "
                   "Liquidation LTV: 86%. Oracle: Chainlink ETH/USD."
    },
    {
        "protocol": "Eigenlayer",
        "action": "Restaking",
        "pair": "stETH restake",
        "context": "Restaking points: active. TVL: $12B. Slashing risk: theoretical. "
                   "No guaranteed yield yet. Opportunity cost vs pure staking: ~0%."
    },
]


def build_prompt(scenario: dict) -> str:
    """Build the DeFi risk assessment prompt for the LLM."""
    return f"""You are a DeFi risk assessment agent. Analyze the following scenario and provide:
1. Risk level (LOW / MEDIUM / HIGH / CRITICAL)
2. Recommended action (EXECUTE / HOLD / REJECT)
3. Key risk factors (2-3 bullet points)
4. Confidence score (0-100)

Protocol: {scenario['protocol']}
Action: {scenario['action']}
Trading Pair: {scenario['pair']}
Market Context: {scenario['context']}

Respond in JSON format with keys: risk_level, action, risk_factors, confidence_score, reasoning."""


def call_ollama(prompt: str, model: str = MODEL_NAME,
                timeout: int = 60) -> Optional[str]:
    """
    Call Ollama API to generate LLM response.
    Returns the full response text, or None if failed.
    """
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,  # Low temp for consistent analysis
                    "num_predict": 512,
                }
            },
            timeout=timeout
        )
        response.raise_for_status()
        return response.json().get("response", "")
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to Ollama. Is it running?")
        print("  Start it with: ollama serve")
        return None
    except requests.exceptions.Timeout:
        print(f"ERROR: Ollama timed out after {timeout}s")
        return None
    except Exception as e:
        print(f"ERROR: Ollama call failed: {e}")
        return None


def generate_decisions(num_decisions: int = 10,
                       use_ollama: bool = True) -> List[DecisionRecord]:
    """
    Generate a batch of DeFi decisions using the LLM agent.

    Args:
        num_decisions: Number of decisions to generate
        use_ollama: If True, call Ollama; if False, use mock responses

    Returns:
        List of DecisionRecord objects ready for Merkle tree
    """
    records = []

    for i in range(num_decisions):
        scenario = DEFI_SCENARIOS[i % len(DEFI_SCENARIOS)]
        prompt = build_prompt(scenario)

        if use_ollama:
            print(f"  [{i+1}/{num_decisions}] Querying {MODEL_NAME} "
                  f"for {scenario['protocol']}...", end=" ", flush=True)
            response = call_ollama(prompt)
            if response is None:
                print("FAILED — using mock response")
                response = _mock_response(scenario)
            else:
                print(f"OK ({len(response)} chars)")
        else:
            response = _mock_response(scenario)

        record = DecisionRecord(
            input_prompt=prompt,
            output_response=response,
            model_id=MODEL_NAME,
            model_version=MODEL_VERSION,
            timestamp=time.time()
        )
        records.append(record)

    return records


def _mock_response(scenario: dict) -> str:
    """Generate a mock response for testing without Ollama."""
    import random
    risk = random.choice(["LOW", "MEDIUM", "HIGH"])
    action = "EXECUTE" if risk == "LOW" else ("HOLD" if risk == "MEDIUM" else "REJECT")
    confidence = random.randint(55, 95)

    return json.dumps({
        "risk_level": risk,
        "action": action,
        "risk_factors": [
            f"Market volatility for {scenario['pair']}",
            f"Smart contract risk on {scenario['protocol']}",
            "Liquidity depth concerns"
        ],
        "confidence_score": confidence,
        "reasoning": f"Based on current market conditions for {scenario['protocol']}, "
                     f"the {scenario['action']} operation carries {risk} risk."
    })


def save_decisions(records: List[DecisionRecord], filepath: str):
    """Save decision records to a JSON file for reproducibility."""
    data = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "model": MODEL_NAME,
        "model_version": MODEL_VERSION,
        "num_decisions": len(records),
        "decisions": [r.to_dict() for r in records]
    }
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Saved {len(records)} decisions to {filepath}")


# ======================== Main ========================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ChainMind Agent Simulator")
    parser.add_argument("-n", "--num", type=int, default=10,
                        help="Number of decisions to generate")
    parser.add_argument("--mock", action="store_true",
                        help="Use mock responses (no Ollama needed)")
    parser.add_argument("-o", "--output", type=str,
                        default="data/decisions.json",
                        help="Output file path")
    args = parser.parse_args()

    print("=" * 60)
    print("ChainMind Agent Simulator")
    print(f"Model: {MODEL_NAME}")
    print(f"Mode:  {'Mock' if args.mock else 'Ollama (live LLM)'}")
    print(f"Generating {args.num} DeFi decisions...")
    print("=" * 60)

    records = generate_decisions(args.num, use_ollama=not args.mock)

    save_decisions(records, args.output)

    # Preview
    print(f"\nPreview of first decision:")
    d = records[0].to_dict()
    print(f"  Input hash:  {d['input_hash'][:18]}...")
    print(f"  Output hash: {d['output_hash'][:18]}...")
    print(f"  Model hash:  {d['model_hash'][:18]}...")
    print(f"  Leaf hash:   {d['leaf_hash'][:18]}...")
