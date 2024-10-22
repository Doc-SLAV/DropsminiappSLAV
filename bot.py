# NOT FOR SALE, FREE TO CLONE OR RENAME
# PAY IT FORDWARD!
import requests
import json
import time
import os
from datetime import datetime, timedelta
from colorama import Fore, Style, init
import threading
from concurrent.futures import ThreadPoolExecutor

init(autoreset=True)

TELEGRAM_BOT_TOKEN = 'TELEGRAM_BOT_TOKEN' # 333217932:aoj3poeohdowa201eh10u
CHAT_ID = 'CHAT_ID' # -263218379

class Endpoints:
    AUTH_LOGIN = "/auth/login"
    USER_CURRENT = "/user/current"
    DAILY_BONUS = "/bonus/dailyBonus"
    TASKS = "/quest"
    VERIFY_TASK = "/quest/{task_id}/verify"
    CLAIM_TASK = "/quest/{task_id}/claim"
    CLAIM_REF = "/refLink/claim"  

BASE_API_URL = "https://api.miniapp.dropstab.com/api"
BASE_HEADERS = {
    "accept": "application/json",
    "accept-language": "en-US,en;q=0.9",
    "content-type": "application/json",
    "priority": "u=1, i",
    "sec-ch-ua": "\"Microsoft Edge\";v=\"129\", \"Not=A?Brand\";v=\"8\", \"Chromium\";v=\"129\", \"Microsoft Edge WebView2\";v=\"129\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "Referer": "https://mdkefjwsfepf.dropstab.com/",
    "Referrer-Policy": "strict-origin-when-cross-origin"
}

def get_headers(token=None):
    headers = BASE_HEADERS.copy()
    if token:
        headers["authorization"] = f"Bearer {token}"
    return headers

def retry_request(func, *args, retries=3, delay=5, **kwargs):
    """Retries a function if it raises an exception."""
    for attempt in range(retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"{Fore.YELLOW}Error on attempt {attempt + 1}: {e}{Style.RESET_ALL}")
            if attempt < retries - 1:
                print(f"{Fore.YELLOW}Retrying in {delay} seconds...{Style.RESET_ALL}")
                time.sleep(delay)
            else:
                print(f"{Fore.RED}Max retries reached.{Style.RESET_ALL}")
                raise

def get_token_and_login(payload):
    """Login and return the access token. Retry on failure."""
    time.sleep(5)
    headers = get_headers()
    body = json.dumps({"webAppData": payload})
    print(f"{Fore.CYAN}Attempting to login with payload...{Style.RESET_ALL}")
    
    for attempt in range(3): 
        try:
            response = requests.post(f"{BASE_API_URL}{Endpoints.AUTH_LOGIN}", headers=headers, data=body, timeout=10)
            response.raise_for_status()
            token = response.json().get("jwt", {}).get("access", {}).get("token", None)
            if token:
                print(f"{Fore.GREEN}Login successful.{Style.RESET_ALL}")
                return token
            else:
                raise ValueError("Failed to retrieve token from response.")
        except requests.RequestException as e:
            print(f"{Fore.RED}Request failed during login: {e}{Style.RESET_ALL}")
            if attempt < 2:
                print(f"{Fore.YELLOW}Retrying login in 5 seconds...{Style.RESET_ALL}")
                time.sleep(5)
            else:
                raise
        except ValueError as e:
            print(f"{Fore.RED}Value error: {e}{Style.RESET_ALL}")
            raise

def get_user_info(token, send_message=True):
    time.sleep(5)
    headers = get_headers(token)
    print(f"{Fore.CYAN}Fetching user info...{Style.RESET_ALL}")
    try:
        response = requests.get(f"{BASE_API_URL}{Endpoints.USER_CURRENT}", headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        print(f"{Fore.GREEN}Account: {data['tgUsername']}, Balance: {data['balance']}{Style.RESET_ALL}")

        if send_message:
            balance_message = f"<b>Account:</b> {data['tgUsername']}\n<b>Balance:</b> {data['balance']}"
            send_telegram_message(balance_message)

        return data
    except requests.RequestException as e:
        print(f"{Fore.RED}Request failed while fetching user info: {e}{Style.RESET_ALL}")
        raise
    except KeyError as e:
        print(f"{Fore.RED}Key error in user info response: {e}{Style.RESET_ALL}")
        raise

def send_telegram_message(message):
    """Send a message to the specified Telegram chat."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': CHAT_ID,
        'text': message,
        'parse_mode': 'HTML' 
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print(f"{Fore.GREEN}Telegram message sent successfully.{Style.RESET_ALL}")
    except requests.RequestException as e:
        print(f"{Fore.RED}Failed to send message to Telegram: {e}{Style.RESET_ALL}")

def daily_bonus(token):
    time.sleep(5)
    headers = get_headers(token)
    print(f"{Fore.CYAN}Attempting to collect daily bonus...{Style.RESET_ALL}")
    try:
        response = requests.post(f"{BASE_API_URL}{Endpoints.DAILY_BONUS}", headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get("result", False):
            print(f"{Fore.GREEN}Daily login successful. Streaks: {data['streaks']}{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}Daily bonus already claimed or not available.{Style.RESET_ALL}")
    except requests.RequestException as e:
        print(f"{Fore.RED}Request failed while claiming daily bonus: {e}{Style.RESET_ALL}")
    except KeyError as e:
        print(f"{Fore.RED}Key error in daily bonus response: {e}{Style.RESET_ALL}")

def process_tasks(token):
    time.sleep(5)
    headers = get_headers(token)
    print(f"{Fore.CYAN}Fetching and checking tasks from the category....{Style.RESET_ALL}")

    try:
        response = requests.get(f"{BASE_API_URL}{Endpoints.TASKS}", headers=headers)
        response.raise_for_status()
        tasks_data = response.json()
        task_categories_count = len(tasks_data)
        print(f"{Fore.GREEN}Fetched {task_categories_count} task categories.{Style.RESET_ALL}")

        any_claimed_or_clicked = False

        for task_category in tasks_data:
            task_count = len(task_category['quests'])
            print(f"{Fore.CYAN}Processing {task_count} tasks in category: {task_category['name']}{Style.RESET_ALL}")

            for task in task_category['quests']:
                print(f"{Fore.BLUE}Task: {task['name']}, Status: {task['status']}, Claim Allowed: {task.get('claimAllowed', 'Not Specified')}{Style.RESET_ALL}")

                if task.get("claimAllowed") is True:
                    print(f"{Fore.CYAN}Attempting to claim task with ID: {task['id']}{Style.RESET_ALL}")
                    claim_response = requests.put(f"{BASE_API_URL}{Endpoints.CLAIM_TASK.format(task_id=task['id'])}", headers=headers)
                    claim_response.raise_for_status()
                    claim_data = claim_response.json()
                    print(f"{Fore.GREEN}Claim response data: {claim_data}{Style.RESET_ALL}") 
                    any_claimed_or_clicked = True

                elif task.get("claimAllowed") is False and task_category['name'] == "Daily":
                    print(f"{Fore.CYAN}Attempting to verify daily task with ID: {task['id']}{Style.RESET_ALL}")
                    verify_response = requests.put(f"{BASE_API_URL}{Endpoints.VERIFY_TASK.format(task_id=task['id'])}", headers=headers)
                    verify_response.raise_for_status()
                    verify_data = verify_response.json()
                    print(f"{Fore.GREEN}Verify response data: {verify_data}{Style.RESET_ALL}") 
                    any_claimed_or_clicked = True

        if not any_claimed_or_clicked:
            print(f"{Fore.YELLOW}No tasks available to claim or click.{Style.RESET_ALL}")
            return False
        return True

    except requests.RequestException as e:
        print(f"{Fore.RED}Request failed while fetching tasks: {e}{Style.RESET_ALL}")
        return False
    except KeyError as e:
        print(f"{Fore.RED}Key error in task fetching response: {e}{Style.RESET_ALL}")
        return False
    except Exception as e:
        print(f"{Fore.RED}An error occurred: {e}{Style.RESET_ALL}")
        return False
        
def claim_referral(token):
    headers = get_headers(token)
    try:
        print(f"{Fore.CYAN}Attempting to claim referral bonus...{Style.RESET_ALL}")
        response = requests.post(f"{BASE_API_URL}{Endpoints.CLAIM_REF}", headers=headers)
        response.raise_for_status()
        data = response.json()
        print(f"{Fore.GREEN}Claim referral response: {data}{Style.RESET_ALL}")
    except requests.RequestException as e:
        print(f"{Fore.RED}Request failed while claiming referral bonus: {e}{Style.RESET_ALL}")
        print(f"{Fore.RED}Response status code: {response.status_code}, Response body: {response.text}{Style.RESET_ALL}")

def process_single_query(query):
    """Process a single account query."""
    try:
        token = retry_request(get_token_and_login, query.strip())
        user_info = retry_request(get_user_info, token, send_message=False)
        old_balance = user_info['balance']

        daily_bonus(token)
        claim_referral(token)
        tasks_available = process_tasks(token)

        if not tasks_available:
            print(f"{Fore.YELLOW}No tasks available to claim for account {user_info['tgUsername']}. Moving to next account.{Style.RESET_ALL}")
            return None

        updated_user_info = retry_request(get_user_info, token)
        new_balance = updated_user_info['balance']

        if new_balance != old_balance:
            account_balance_message = f"<b>Account:</b> {updated_user_info['tgUsername']}\n<b>Balance:</b> {new_balance}"
            return account_balance_message
        else:
            print(f"{Fore.YELLOW}No change in balance for account {updated_user_info['tgUsername']}. Skipping message.{Style.RESET_ALL}")
            return None
    except (requests.RequestException, ValueError) as e:
        print(f"{Fore.RED}Error processing query: {e}. Attempting to re-login...{Style.RESET_ALL}")
        try:
            token = retry_request(get_token_and_login, query.strip())
            user_info = retry_request(get_user_info, token, send_message=False)
            old_balance = user_info['balance']

            daily_bonus(token)
            claim_referral(token)
            tasks_available = process_tasks(token)

            if not tasks_available:
                print(f"{Fore.YELLOW}No tasks available to claim for account {user_info['tgUsername']}. Moving to next account.{Style.RESET_ALL}")
                return None

            updated_user_info = retry_request(get_user_info, token)
            new_balance = updated_user_info['balance']

            if new_balance != old_balance:
                account_balance_message = f"<b>Account:</b> {updated_user_info['tgUsername']}\n<b>Balance:</b> {new_balance}"
                return account_balance_message
            else:
                print(f"{Fore.YELLOW}No change in balance for account {updated_user_info['tgUsername']}. Skipping message.{Style.RESET_ALL}")
                return None
        except Exception as re_login_error:
            print(f"{Fore.RED}Re-login failed: {re_login_error}{Style.RESET_ALL}")
            return None

def process_queries():
    if not os.path.exists('sesi.txt'):
        print(f"{Fore.RED}Error: sesi.txt file not found.{Style.RESET_ALL}")
        return

    all_balances = []

    for run_count in range(2):
        with open('sesi.txt', 'r') as file:
            queries = file.readlines()

        if use_multithreading:
            with ThreadPoolExecutor(max_workers=2) as executor:  
                results = list(executor.map(process_single_query, queries))

            all_balances = [result for result in results if result]
        else:
            for query in queries:
                balance_message = process_single_query(query)
                if balance_message:
                    all_balances.append(balance_message)

        if all_balances:
            final_balance_message = "Here are the balances for all accounts after solving tasks:\n" + "\n".join(all_balances)
            send_telegram_message(final_balance_message)
        else:
            print(f"{Fore.YELLOW}No balances changed, no summary message sent.{Style.RESET_ALL}")

        if run_count < 1:
            print(f"{Fore.YELLOW}Waiting for 1 hour before claiming task (Run {run_count + 1}/2)...{Style.RESET_ALL}")
            time.sleep(3600)

    print(f"{Fore.YELLOW}Completed, now waiting until 00:01 UTC...{Style.RESET_ALL}")
    wait_until_midnight()

def wait_until_midnight():
    now = datetime.utcnow()
    midnight = (now + timedelta(days=1)).replace(hour=0, minute=1, second=0, microsecond=0)
    seconds_until_midnight = (midnight - now).total_seconds()
    print(f"{Fore.YELLOW}Waiting {seconds_until_midnight} seconds until midnight...{Style.RESET_ALL}")
    time.sleep(seconds_until_midnight)

use_multithreading = input("Activate multi-threading (y/n): ").strip().lower() == 'y'

try:
    while True:
        process_queries()
        print(f"{Fore.GREEN}Processing for the current day completed. Waiting until the next midnight to restart...{Style.RESET_ALL}")
        wait_until_midnight()
        print(f"{Fore.CYAN}It's 00:01 UTC, starting the process for the next day...{Style.RESET_ALL}")
except Exception as e:
    print(f"{Fore.RED}Unexpected error occurred: {e}{Style.RESET_ALL}")
