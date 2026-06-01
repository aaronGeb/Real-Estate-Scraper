'''
This file contains the scraper for Zillow.
'''
import random
import asyncio
import time
import re
from typing import Optional
from playwright.async_api import async_playwright, Page, Browser
from bs4 import BeautifulSoup
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential
from config import settings

async def get_browser(playwright: async_playwright) -> Browser:
  '''Launch a stealth-ish Chromium browser'''
  browser = await playwright.chromium.launch(
    headless=True,
    args=[
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-blink-features=AutomationControlled',
    ],
  )
  return browser
async def get_page(browser: Browser) -> Page:
  '''Get a new page from the browser'''
  context = await browser.new_context(
    user_agent=(
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
      "Chrome/120.0.0.0 Safari/537.36"
    ),
    viewport={'width': 1200, 'height': 800},
    locale='en-US',
  )
  await context.add_init_script(
    "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
  return await context.new_page()

async def polite_delay()->None:
  '''Wait a random amount of time between requests'''
  delay = random.uniform(settings.request_delay_min, settings.request_delay_max)
  logger.debug(f'Waiting {delay:.2f} seconds...')
  await asyncio.sleep(delay)

def parse_price(raw: str) -> Optional[float]:
  '''Parse the price from the price string'''
  try:
    price = float(raw.replace('$', '').replace(',', '').replace('+', '').strip())
    return price
  except ValueError:
    logger.warning(f'Failed to parse price from: {raw}')
    return None

def parse_int(raw: str) -> Optional[int]:
  '''Parse the int from the string'''
  try:
    return int("".join(filter(str.isdigit, raw.strip())))
  except ValueError:
    logger.warning(f'Failed to parse int from: {raw}')
    return None

def parse_float(raw: str) -> Optional[float]:
  '''Parse the float from the string'''
  try:
    cleaned = "".join(c for c in raw if c.isdigit() or c == ".")
    return float(cleaned) if cleaned else None
  except ValueError:
    logger.warning(f'Failed to parse float from: {raw}')
    return None

def parse_listing_card(card: BeautifulSoup) -> Optional[str]:
  '''Extract data from a single Zillow listing card (BeautifulSoup tag)'''
  try:
    price_tag = card.select_one('[data_test="property-card-price"]')
    price = parse_price(price_tag.text) if price_tag else None

    address_tag = card.select_one('[data_test="property-card-addr"]')
    address_text = address_tag.text.strip() if address_tag else None
    parts = [p.strip() for p in address_text.split(',')]
    address = parts[0] if len(parts) > 0 else ''
    city = parts[1] if len(parts) >1 else ''
    state_zip = parets[2].split() if len(parts) > 2 else []
    state = state_zip[0] if state_zip else ''
    zip_code = state_zip[1] if len(state_zip) >1 else None


    status = card.select('[data_test="property-card-status"]')
    beds = baths = sqrt = None
    for stat in status:
      txt = stat.text.lower()
      if 'bd' in txt or 'bed' in txt:
        beds =  parse_int(txt)
      elif 'ba' in txt or 'bath' in txt:
        baths = parse_int(txt)
      elif 'sqft' in txt or 'sq ft' in txt:
        sqrt = parse_float(txt)
    link_tag = card.select_one('a[href*="/homedetails/"]')
    url = f"https://www.zillow.com{link_tag['href']}" if link_tag else None
    external_id = None
    if url:
      match = re.search(r'/(\d+)_zpid', url)
      external_id = match.group(1) if match else None
    type_tag = card.select_one("[data-test='property-card-statusTpe']")
    prop_type = type_tag.strip().lower() if type_tag else None
    if not address or not price:
      return None
    return {
      'external-id': external_id or address,
      'source':'zillow',
      'url': url,
      'address': address,
      'city': city,
      'state': state,
      'zip_code': zip_code,
      'property_type': prop_type,
      'bedrooms': beds,
      'sqft': sqft,
      'status': 'for_sale',
      'price': price
    }
  except Exception as exc:
    logger.warning(f'card parse error:{ exc}')
    return None



@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=4, max=30))
async def scrape_zillow_city(city_query: str):
  '''scape the first few pages of zillow listing for a given city return a list of property dicts'''
  slug =  city_query.lower().replace(', ', '-').replace(' ', '-')
  base_url = f'https://www.zillow.com/homes{slug}_rb/'
  results= []
  async with async_playwright() as pw:
    browser = await get_browser(pw)
    page = await get_page(browser)

    try:
        for page_num in range(1,4):
          url = base_url if page_num == 1 else f'{base_url}{page_num}_p'
          logger.info(f'Zillow = {url}')
          response = await page.goto(url, wait_until='domcontentloadded', timeout=30_000)
          if response and response.status == 429:
            raise RuntimeError('Rate limited by Zillow (429)')
          await polite_delay()
          try:

             await page.wait_for_selector(
              '[date-test="property-card"]', timeout=15_000
             )
          except Exception:
            logger.warning(f'No listing found on page { page_num}, stopping.')
            break
          html =  await page.context()
          soup =  BeautifulSoup(html, 'lxml')
          cards = soup. select('[data-test="property-card"]')
          logger.info(f'Found {len(cards)} cards on page {page_num}')
          

          page_results = [r for card in cards if (r := parse_listing_card(card))]
          results.extend(page_results)
          next_btn = soup.select_one('a[title="Next Page"]')
          if not next_btn:
            break
    finally:
      await browser.close()
  logger.success(f'Zillow: scraped {len((results))} listing for "{city_query}"')
  return results

