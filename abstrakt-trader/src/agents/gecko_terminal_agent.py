import json
import requests
import pandas as pd

INTERVAL = "5m"
DEX = "pump-fun"
NETWORK = "solana"
LLM_MODEL = "0xroyce/plutus"
HOST = "http://localhost:11434"
STREAM = False

CUSTOM_ARGS = {"temperature": 0.5, "top_p": 0.9}

#make function that return the data in a dictionary from the csv file   
def get_data_from_csv(csv_file):
    try:
        # Read CSV file into DataFrame
        df = pd.read_csv(csv_file)
        
        # Convert DataFrame to dictionary format
        data_dict = df.to_dict('records')
        
        return data_dict
    except Exception as e:
        print(f"Error reading CSV file: {str(e)}")
        return None

def get_geckoterminal_data():
    try:
        url = f"https://api.geckoterminal.com/api/v2/networks/{NETWORK}/trending_pools?include={DEX}&page=1&duration={INTERVAL}"
        headers = {"Accept": "application/json"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx, 5xx)
        return response.json()  # Return JSON directly instead of converting to string
    except requests.RequestException as e:
        print(f"Error fetching data from GeckoTerminal: {str(e)}")
        return None


def extract_important_data(item):
    return {
        "id": item["id"],
        "pair_name": item["attributes"]["name"],
        "base_token_price_usd": item["attributes"]["base_token_price_usd"],
      #  "quote_token_price_usd": item["attributes"]["quote_token_price_usd"],
        "price_change_percentage": item["attributes"]["price_change_percentage"],
        "volume_usd": item["attributes"]["volume_usd"],
        "reserve_in_usd": item["attributes"]["reserve_in_usd"],
        "transactions": item["attributes"]["transactions"]
    }


def send_to_ollama(CUSTOM_PROMPT, CUSTOM_ARGS, LLM_MODEL, HOST, STREAM):
    """
    Send a prompt to an Ollama-hosted LLM and return the response.
    """
    # Remove the health check as it's not a standard endpoint in Ollama
    url = f"{HOST}/api/generate"
    payload = {
        "model": LLM_MODEL,
        "prompt": CUSTOM_PROMPT,
        "stream": STREAM,
        **CUSTOM_ARGS
    }
    
    try:
        print(f"Sending request to: {url}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(url, json=payload, stream=STREAM)
        print(f"Response status code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Error response: {response.text}")
            return None
            
        if STREAM:
            def generate():
                for line in response.iter_lines():
                    if line:
                        chunk = json.loads(line)
                        yield chunk.get("response", "")
            return generate()
        else:
            data = response.json()
            return data.get("response", "")
            
    except requests.exceptions.RequestException as e:
        print(f"Request error: {str(e)}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding response: {str(e)}")
        return None

#make a function that extracts the data and creates a csv file with the data and saves it in the data folder,the file name should be the current date and time     
def create_csv_file(data):
    if data is None:
        print("No data to save to CSV")
        return
    # Extract data from the 'data' key in the API response
    items = data.get('data', [])
    important_data_list = [extract_important_data(item) for item in items]

    df = pd.DataFrame(important_data_list)
    print(df)
    df.to_csv(f"src/data/trending_pools.csv", index=False)

data = get_geckoterminal_data()


create_csv_file(data)

market_data = get_data_from_csv("src/data/trending_pools.csv")

CUSTOM_PROMPT =  """
You are AbstrakT Strategy Research Assistant 🌙

Im giving you a list with the treding tokens in the solana network in the last 5 minutes:
{market_data}

I want you to analyze the data and give me the most promising pool to invest in, base on the data im giving you,
You're working in a very volatile market, so you need to be very careful with your decisions, and you need to be very confident in your decisions, 
so you need to be very careful with your reasoning and your decisions.

Right now, my balance is less than a 100$, so the decision should be very low risk, and the pool should have a high volume, and a high reserve, and a low price change percentage, and a high price.
This tokens are very unpredicatable, in the next days I will give you more data, like sentiment, and other data, so you can make a better decision.

Your task:
1. Evaluate all the variables in the data 
2. Look for confirmation/contradiction between different strategies
3. Consider risk factors

I need you that you give me this information:
    Then explain your reasoning:
    - Signal analysis
    - Market alignment
    - Risk assessment
    - Confidence in each decision (0-100%)
    - The pair name
    - The base token price
    - The quote token price
    - The volume
    - The reserve
    - The transactions
    - The price change percentage
    - The pair name
    
    And explain me how do you calculte the stability index and risk index
    and give a porcentage of confidence that you have on the decision
Remember:
- AbstrakT prioritizes risk management! 🛡️
- Multiple confirming signals increase confidence
- Contradicting signals require deeper analysis
- Better to reject a signal than risk a bad trade
"""


print(send_to_ollama(CUSTOM_PROMPT, CUSTOM_ARGS, LLM_MODEL, HOST, STREAM))



