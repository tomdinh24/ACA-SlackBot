import os
from datetime import datetime
from pycoingecko import CoinGeckoAPI
from pathlib import Path
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler


env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)


# Initializes app with bot token handler
app = App(token=os.environ.get("oauthToken"))



def get_Crypto_Dict(option):
    
    web = CoinGeckoAPI()
    coinlist = web.get_coins_list()
    coin_id_symbol = {}
    coin_symbol_id = {}

    for item in coinlist:
        symbol = item["symbol"]
        id = item["id"]

        coin_id_symbol[id] = symbol
        coin_symbol_id[symbol] = id

    if option == "id":
        return coin_id_symbol

    elif option == "symbol":
        return coin_symbol_id

    else:
        return None


@app.event("message")
def message_events(body, logger):
    logger.info(body)


@app.event("app_mention")
def mention_handler(body, say):
    try:
        label = body["event"]["blocks"][0]["elements"][0]["elements"][1]["text"].lower().strip(" \t\n\r")
        coin_dict = get_Crypto_Dict("symbol")

        if label in coin_dict:
            id = coin_dict[label]

        else:
            say(f"The coin: {label} does not exist, please enter a valid coin")

        say(
            f"For more info about {label} and crypto, please select from the following options below")

        say(
            blocks=[
                {
                    "type": "actions",
                    "block_id": "actions1",
                    "elements": [
                        {
                            "type": "static_select",
                            "placeholder": {
                                "type": "plain_text",
                                "text": "Select An Option Below",
                            },
                            "action_id": "selection",
                            "options": [
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": "Coin Description",
                                    },
                                    "value": "description",
                                },
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": "Coin Price",
                                    },
                                    "value": "price",
                                },
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": "Global Market Overview",
                                    },
                                    "value": "global",
                                },
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": "Trending Cryptocurrencies",
                                    },
                                    "value": "trending",
                                },
                            ],
                        },
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "Go"},
                            "value": "Go",
                            "action_id": "selected_option",
                        },
                    ],
                }
            ],
            text=f"{id}",
        )
    except IndexError:
        say(f"Ticker is missing, please enter a ticker. See example below:")
        say(f"```i.e. @CryptoBot btc```")
        return None


@app.action("selection")
def handle_selection(ack, body, logger):
    ack()
    logger.info(body)


@app.action("selected_option")
def select_Option(body, ack, say):

    ack()
    web = CoinGeckoAPI()
    coin_id_symbol = get_Crypto_Dict("id")
    coin_symbol_id = get_Crypto_Dict("symbol")

    id = body["message"]["text"]
    input = body["state"]["values"]["actions1"]["selection"]["selected_option"]["value"]

    if input == "description":
        coin_info = web.get_coin_by_id(id)
        say(f"```{coin_info['description']['en']}```")


    elif input == "global":
        global_data = web.get_global()
        updated_at = global_data["updated_at"]
        request_time = datetime.fromtimestamp(updated_at).strftime("%m-%d-%y %H:%M:%S")
        say(f"Crypto Market Overview - Last Updated at: {request_time}")

        say(f"There are {global_data['active_cryptocurrencies']} active cryptocurrencies.")
        
        say(f"Cryptocurrency Market Cap % (Top 10 cryptocurrencies)")

        top_coins = global_data["market_cap_percentage"].items()
        top_ten = list(top_coins)[:10]

        for coin in top_ten:
            ticker = coin[0]
            id = coin_symbol_id[ticker]
            coin_price_info = web.get_price(id,"usd")

            for key in coin_price_info.keys():
                coin_price = coin_price_info[key]["usd"]
                say(
                    f"{coin[0]:6}market cap is {coin[1]:.2f}% of the total"
                    f" supply. (USD) ${coin_price:.4f}"
                )


    elif input == "price":
        coin_value = web.get_price(id,"usd")

        for key in coin_value.keys():
            say(
                f"{ coin_id_symbol[key]} is currently trading"
                f" at USD ${coin_value[key]['usd']}"
            )


    elif input == "trending":
        coin_trends = web.get_search_trending()

        say("Trending Coins: ")

        for topic in coin_trends["coins"]:
            topic_id = str(topic["item"]["name"])
            coin_price_value = web.get_price(topic_id,"usd")

            for key in coin_price_value.keys():
                say(
                    f"{key} ({ coin_id_symbol[key]}) Price in USD ${coin_price_value[key]['usd']:.4f}"
                )


@app.action("info")
def action_info(body, ack, say):
    ack()
    web = CoinGeckoAPI()
    id = body["state"]["values"]["actions1"]["selection"]["selected_option"][
        "value"
    ]
    info = web.get_coin_by_id(id)
    say(f"```{info['description']['en']}```")


if __name__ == "__main__":
    SocketModeHandler(app, os.environ["socketToken"]).start()
