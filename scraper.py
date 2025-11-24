import requests
import pandas as pd
import json
import argparse
import re  # For regex
import os
os.makedirs("output", exist_ok=True)
from utils.db import create_connection, ensure_schema, insert_auction_item, insert_auction



# === CONFIGURATION ===
BEARER_TOKEN = 'Bearer 606F1EE38127BE28F9646A9BFE8F2E0BD0002C3D017EE956B02A619374895C06270ADC99707D946E90B56418B0DF48F6A2735CB918357EC48855881332A0699553F355279766E3A7BA63D7A9A553F0D176C12630B6857E2D90D205AFB871B25598419DD77AA93A4A34A82B1AFAB801D7978FB69B1A414121713C9531C362AAC13EB63A1B9E79751536162840116102A1E036C2E63D1D19A8929ECD473970FF41AD3225B23D8A993F24D07BA5CA8A785AF4F9942C36FFA567CDA50F8D08693FAAEA95A52B38455C26B7C7CCCDC8012E9D4D998EB959E615C66BC18AC85D14051143C506BD3CB2EDAD4E34C7459E1325FDB863771C6AEE8FF564D860F9010CD245EEC01A3029EA1B9742E83A80BAA7585AA8B86166E6CB40FC1921DD11547522F451BBE6A39EE1F201815D88A020DBD6CBFC436891ECF77962B76393B31F636B460A7453D74AD9ED693DFD47959069A3C5986C5854D747795FE33A3B79D17B3931190B7059'

graphql_url = "https://hibid.com/graphql"

headers_template = {
    'authority': 'hibid.com',
    'method': 'POST',
    'path': '/graphql',
    'scheme': 'https',
    'accept': 'application/json, text/plain, */*',
    'accept-encoding': 'gzip, deflate, br, zstd',
    'accept-language': 'en-US,en;q=0.9',
    'authorization': BEARER_TOKEN,
    'content-type': 'application/json',
    'origin': 'https://hibid.com',
    'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Chrome OS"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'site_subdomain': 'hibid.com',
    'user-agent': 'Mozilla/5.0 (X11; CrOS x86_64 14541.0.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
}

cookies = {
    '_cq_duid': '1.1740059255.RYtXvKLAuzifedS4',
    '_cq_suid': '1.1740059255.PbHQAuoyQBy4y0no',
    '_pin_unauth': 'dWlkPU1HRTFObUZpWVRRdE5HVTFZeTAwTW1RekxUbGlNRGt0TnpFMk5UQmxORFF5WkRWaQ',
    '_hjSessionUser_1002726': 'eyJpZCI6ImExM2QzYTliLTc0ZmItNWQyOS05MGE0LTgxNDkxY2I1Zjc3ZiIsImNyZWF0ZWQiOjE3NDAwNjAxMTU2MTIsImV4aXN0aW5nIjp0cnVlfQ==',
    'HBCookieTracking': 'DefaultCookieSet-Exp:3/22/2025 9:03:14 AM',
    'HBIsLoggedIn': '1',
    'navCounter': '3',
    'subDoNotPrompt': 'true',
    'lotViewMode': '0',
    'UseInfiniteScroll': 'true',
    'lotsperpage': '100',
    '_ga_6MG77QNJZX': 'GS1.1.1740181624.3.0.1740182446.0.0.0',
    '_gid': 'GA1.2.1150965580.1740546808',
    '__gads': 'ID=c967a7ba2cd5cba1:T=1740060112:RT=1740711145:S=ALNI_MbaL9Yc0lXWI5sTsiYfJeHbR8UUSw',
    '__eoi': 'ID=77b2d2f33d297f0c:T=1740060112:RT=1740711145:S=AA-AfjZqQXB3p-_6U6TayZRks5Ua',
    '__cf_bm': 'DPZnaaXFUGCKUsFGvzOUL6r7q7L5pqetrTeqAusdc3s-1740736285-1.0.1.1-gj0cxCUFynQOhlkOehjH2_ha_1Zw.01KFFyFfZNHgHjKHtGWoF.qSs7p3tC25LahP2wXXlN9Mzzm.D1k1zOYTQ',
    '_gat_UA-772246-8': '1',
    '_gat_gtag_UA_772246_5': '1',
    '_ga_WDTLCRKGW8': 'GS1.1.1740736657.29.1.1740736659.0.0.0',
    '_ga': 'GA1.1.1022542906.1740059254',
    '_hjSession_1002726': 'eyJpZCI6IjYyOGY1ZTBlLTY1MWYtNDAwMS1iNmM2LWE3MTgyZWExMjNhNSIsImMiOjE3NDA3MzY2NTk4MjAsInMiOjAsInIiOjAsInNiIjowLCJzciI6MCwic2UiOjAsImZzIjowLCJzcCI6MH0=',
    '_uetsid': '6a470970f40011ef99e8f3f2da8fe138',
    '_uetvid': '3ddd11f0ef9111ef9dd9dde7cb131fcf',
    '_derived_epik': 'dj0yJnU9TnZwTDhrYVVpMU40anBnNTVTcHNhWTl6eEprQVlQS0wmbj16MEdISkQ1UGZNSDFkemNqU2ZnMTNBJm09MSZ0PUFBQUFBR2ZCaUpVJnJtPTEmcnQ9QUFBQUFHZkJpSlUmc3A9Mg',
}

query = """
    query LotSearch($auctionId: Int = null, $pageNumber: Int!, $pageLength: Int!, $category: CategoryId = null, $searchText: String = null, $zip: String = null, $miles: Int = null, $shippingOffered: Boolean = false, $countryName: String = null, $status: AuctionLotStatus = null, $sortOrder: EventItemSortOrder = null, $filter: AuctionLotFilter = null, $isArchive: Boolean = false, $dateStart: DateTime, $dateEnd: DateTime, $countAsView: Boolean = true, $hideGoogle: Boolean = false) {
      lotSearch(
        input: {auctionId: $auctionId, category: $category, searchText: $searchText, zip: $zip, miles: $miles, shippingOffered: $shippingOffered, countryName: $countryName, status: $status, sortOrder: $sortOrder, filter: $filter, isArchive: $isArchive, dateStart: $dateStart, dateEnd: $dateEnd, countAsView: $countAsView, hideGoogle: $hideGoogle}
        pageNumber: $pageNumber
        pageLength: $pageLength
        sortDirection: DESC
      ) {
        pagedResults {
          pageLength
          pageNumber
          totalCount
          filteredCount
          results {
            auction {
              ...auctionMinimum
              __typename
            }
            bidAmount
            bidList
            bidQuantity
            description
            estimate
            featuredPicture {
              description
              fullSizeLocation
              height
              hdThumbnailLocation
              thumbnailLocation
              width
              __typename
            }
            forceLiveCatalog
            fr8StarUrl
            hideLeadWithDescription
            id
            itemId
            lead
            links {
              description
              id
              type
              url
              videoId
              __typename
            }
            linkTypes
            lotNumber
            lotState {
              bidCount
              biddingExtended
              bidMax
              bidMaxTotal
              buyerBidStatus
              buyerHighBid
              buyerHighBidTotal
              buyNow
              choiceType
              highBid
              highBuyerId
              isArchived
              isClosed
              isHidden
              isLive
              isNotYetLive
              isOnLiveCatalog
              isPosted
              isPublicHidden
              isRegistered
              isWatching
              linkedSoftClose
              mayHaveWonStatus
              minBid
              priceRealized
              priceRealizedMessage
              priceRealizedPerEach
              productStatus
              productUrl
              quantitySold
              reserveSatisfied
              sealed
              showBidStatus
              showReserveStatus
              softCloseMinutes
              softCloseSeconds
              status
              timeLeft
              timeLeftLead
              timeLeftSeconds
              timeLeftTitle
              timeLeftWithLimboSeconds
              watchNotes
              __typename
            }
            pictureCount
            quantity
            ringNumber
            rv
            shippingOffered
            simulcastStatus
            site {
              domain
              fr8StarUrl
              isDomainRequest
              isExtraWWWRequest
              siteType
              subdomain
              __typename
            }
            distanceMiles
            __typename
          }
          __typename
        }
        __typename
      }
    }

    fragment auctionMinimum on Auction {
      id
      altBiddingUrl
      altBiddingUrlCaption
      amexAccepted
      discoverAccepted
      mastercardAccepted
      visaAccepted
      regType
      holdAmount
      auctioneer {
        ...auctioneer
        __typename
      }
      auctionOptions {
        bidding
        altBidding
        catalog
        liveCatalog
        shippingType
        preview
        registration
        webcast
        useLotNumber
        useSaleOrder
        __typename
      }
      auctionState {
        auctionStatus
        bidCardNumber
        isRegistered
        openLotCount
        timeToOpen
        __typename
      }
      bidAmountType
      bidIncrements {
        minBidIncrement
        upToAmount
        __typename
      }
      bidOpenDateTime
      bidCloseDateTime
      bidType
      buyerPremium
      buyerPremiumRate
      checkoutDateInfo
      previewDateInfo
      currencyAbbreviation
      description
      eventAddress
      eventCity
      eventDateBegin
      eventDateEnd
      eventDateInfo
      eventName
      eventState
      eventZip
      featuredPicture {
        description
        fullSizeLocation
        height
        hdThumbnailLocation
        thumbnailLocation
        width
        __typename
      }
      links {
        description
        id
        type
        url
        videoId
        __typename
      }
      lotCount
      showBuyerPremium
      audioVideoChatInfo {
        aVCEnabled
        blockChat
        __typename
      }
      hidden
      sourceType
      distanceMiles
      __typename
    }

    fragment auctioneer on Auctioneer {
      address
      bidIncrementDisclaimer
      buyerRegNotesCaption
      city
      countryId
      country
      cRMID
      email
      fax
      id
      internetAddress
      missingThumbnail
      name
      noMinimumCaption
      phone
      state
      postalCode
      __typename
    }
"""

# === CONSTANTS ===
DAMAGE_DESCRIPTION = "Damage Description"
MISSING_PARTS_DESCRIPTION = "Missing Parts Description"
MISSING_PARTS = "Missing Parts"

# === FUNCTION TO EXTRACT AUCTION ID FROM URL ===
def extract_auction_id(url: str) -> int:
    """Extract numeric auction ID from a HiBid URL."""
    pattern = r'/catalog/(\d+)|/lots/(\d+)'
    m = re.search(pattern, url)
    if not m:
        raise ValueError("Could not extract auction ID from URL. Check format.")
    return int(m.group(1) or m.group(2))


def get_current_bid(item: dict) -> float:
    """
    Return actual current bid.
    If no bids exist (bidCount == 0), return 0.0.
    Do NOT fallback to minBid (Starting Price).
    """
    lot_state = item.get('lotState', {})
    bid_count = lot_state.get('bidCount', 0)
    
    if bid_count > 0:
        return lot_state.get('highBid', 0.0)
    return 0.0

def parse_description(description_text: str) -> dict:
    """Parse the description block into a dict."""
    lines = description_text.splitlines()
    data = {}
    field_mappings = {
        "Title:": ("Title", 6),
        "Brand:": ("Brand", 6),
        "Model:": ("Model", 6),
        "In Packaging?:": ("Packaging", 14),
        "Condition:": ("Condition", 10),
        "Functional?:": ("Functional", 12),
        "Missing Parts?:": (MISSING_PARTS, 15),
        "Missing Parts Description:": (MISSING_PARTS_DESCRIPTION, 26),
        "Damaged?:": ("Damaged", 9),
        "Damage Description:": (DAMAGE_DESCRIPTION, 19),
        "Notes:": ("Notes", 6),
        "UPC:": ("UPC", 4),
        "ASIN:": ("ASIN", 5),
        "Retailer Item URL:": ("URL", 18),
    }

    for line in lines:
        line = line.strip()
        for prefix, (key, offset) in field_mappings.items():
            if line.startswith(prefix):
                data[key] = line[offset:].strip()
                break
    return data


def build_condition_notes(parsed_data: dict) -> str:
    """Create the pipe-separated condition string for the DB."""
    order = [
        ("Packaging", "Packaging"),
        ("Condition", "Condition"),
        ("Functional", "Functional"),
        (MISSING_PARTS, MISSING_PARTS),
        (MISSING_PARTS_DESCRIPTION, MISSING_PARTS_DESCRIPTION),
        ("Damaged", "Damaged"),
        (DAMAGE_DESCRIPTION, DAMAGE_DESCRIPTION),
        ("Notes", "Notes"),
        ("UPC", "UPC"),
        ("ASIN", "ASIN"),
        ("Retailer Item URL", "URL"),
    ]
    parts = [f"{label}: {parsed_data[k]}" for label, k in order if parsed_data.get(k)]
    return " | ".join(parts)


def create_csv_row(lot_number: str, current_bid: float, parsed_data: dict) -> dict:
    """One row for the final CSV."""
    return {
        'Lot Number': lot_number,
        'Current Bid': current_bid if abs(current_bid) > 1e-9 else "0",
        'Title': parsed_data.get('Title'),
        'Brand': parsed_data.get('Brand'),
        'Model': parsed_data.get('Model'),
        'Packaging': parsed_data.get('Packaging'),        
        'Condition': parsed_data.get('Condition'),
        'Functional': parsed_data.get('Functional'),
        'Missing Parts': parsed_data.get(MISSING_PARTS),
        'Missing Parts Description': parsed_data.get(MISSING_PARTS_DESCRIPTION),
        'Damaged': parsed_data.get('Damaged'),
        'Damage Description': parsed_data.get(DAMAGE_DESCRIPTION),
        'Notes': parsed_data.get('Notes'),
        'UPC': parsed_data.get('UPC'),
        'ASIN': parsed_data.get('ASIN'),
        'Retailer Item URL': parsed_data.get('URL'),
    }


def handle_database_insert(
    conn,
    auction_id: int,
    lot_number: str,
    current_bid: float,
    parsed_data: dict, 
) -> None:
    """Insert item directly into the flat table."""
    # We no longer need to look up products or create product IDs.
    # We just pass the data straight to the insert function.
    
    insert_auction_item(conn, auction_id, lot_number, current_bid, parsed_data)

def process_items(conn, auction_id: int, items: list) -> None:
    for item in items:
        lot_number = item['lotNumber']
        current_bid = get_current_bid(item)
        parsed = parse_description(item['description'])
        insert_auction_item(conn, auction_id, lot_number, current_bid, parsed)


def create_request_payload(auction_id: int) -> dict:
    """Build the GraphQL payload."""
    return {
        "operationName": "LotSearch",
        "query": query,
        "variables": {
            "auctionId": auction_id,
            "pageNumber": 1,
            "pageLength": 9000,
            "category": None,
            "searchText": None,
            "zip": "",
            "miles": 50,
            "shippingOffered": False,
            "countryName": "",
            "status": "ALL",
            "sortOrder": "LOT_NUMBER",
            "filter": "ALL",
            "isArchive": False,
            "dateStart": None,
            "dateEnd": None,
            "countAsView": True,
            "hideGoogle": False,
        },
    }

# ----------------------------------------------------------------------
# MAIN SCRAPER
# ----------------------------------------------------------------------
def scrape_auction(auction_url: str) -> None:
    # ---- 1. Extract ID -------------------------------------------------
    try:
        auction_id = extract_auction_id(auction_url)
        print(f"Extracted Auction ID: {auction_id}")
    except ValueError as e:
        print(f"Error: {e}")
        return

    # ---- 2. DB setup ---------------------------------------------------
    conn = create_connection()
    if not conn:
        print("Error: Could not connect to database")
        return
    ensure_schema(conn)
    insert_auction(conn, auction_id, auction_url)

    # ---- 3. Request ----------------------------------------------------
    headers = headers_template.copy()
    headers['referer'] = auction_url
    headers.pop('content-length', None)

    payload = create_request_payload(auction_id)
    print(f"Scraping auction: {auction_url}")
    response = requests.post(graphql_url, headers=headers, json=payload, cookies=cookies)

    # ---- 4. Process response -------------------------------------------
    if response.status_code == 200:
        print("Success! Processing items...")
        data = response.json()

        # Ensure output folder exists
        os.makedirs("output", exist_ok=True)

        with open(f"output/graphql_response_{auction_id}.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        items = data['data']['lotSearch']['pagedResults']['results']
        print(f"Found {len(items)} items.")

        csv_rows = process_items(conn, auction_id, items)

        df = pd.DataFrame(csv_rows)
        try:
            df.to_csv(f'output/auction_{auction_id}_data.csv', index=False)
            print(f"Saved CSV and DB entries for auction {auction_id}.")
        except PermissionError:
            print("Warning: Could not save CSV file (file may be open in Excel). Data saved to database only.")
            print(f"Close the file 'output/auction_{auction_id}_data.csv' and run again to save CSV.")
    else:
        print(f"Failed: {response.status_code}")
        os.makedirs("output", exist_ok=True)
        with open(f"output/graphql_error_{auction_id}.html", "wb") as f:
            f.write(response.content)

    if conn:
        conn.close()


# ----------------------------------------------------------------------
# CLI ENTRYPOINT
# ----------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Scrape a HiBid auction using only the URL"
    )
    parser.add_argument(
        "url",
        type=str,
        help="HiBid auction URL, e.g. https://hibid.com/catalog/626395/..."
    )
    args = parser.parse_args()
    scrape_auction(args.url)