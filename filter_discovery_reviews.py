import os
import sys
import csv
import re
from typing import List, Dict, Any

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_PATH = os.path.join(BASE_DIR, "blinkit_reviews_clean.csv")
OUTPUT_PATH = os.path.join(BASE_DIR, "blinkit_discovery_reviews.csv")

# Define the positive topics, regex patterns, and rationales
TOPIC_TAXONOMY = [
    {
        "topic": "Repeat Purchase & Habits",
        "patterns": [
            r"\brepeat[s]?\b", r"\breorder[s]?\b", r"\border[s]?\s+again\b", r"\bbuy[s]?\s+again\b", 
            r"\bdaily\b", r"\bmorning[s]?\b", r"\beveryday\b", r"\bregular\b", r"\balways\s+order[s]?\b", 
            r"\bhabit[s]?\b", r"\broutine[s]?\b", r"\bstaple[s]?\b", r"\bmilk\b", r"\begg[s]?\b", r"\bbread[s]?\b", r"\bbutter\b"
        ],
        "why_selected": "Discusses recurring/habitual purchase patterns and daily grocery routines."
    },
    {
        "topic": "Product & Category Exploration",
        "patterns": [
            r"\bdiscover[sy]?\b", r"\bexploration[s]?\b", r"\bexplore[sd]?\b", r"\bexploring\b", r"\bcategory\b", r"\bcategories\b", 
            r"\bnew\s+product[s]?\b", r"\bvariet(y|ies)\b", r"\boption[s]?\b", r"\bcatalog[s]?\b", r"\bselection[s]?\b", 
            r"\bcuration\b", r"\bchoice[s]?\b", r"\bbrowse[sd]?\b", r"\bbrowsing\b"
        ],
        "why_selected": "Discusses user journey in exploring new categories and catalog variety."
    },
    {
        "topic": "Search & Navigation Experience",
        "patterns": [
            r"\bsearch(es)?\b", r"\bsearching\b", r"\bfind[s]?\b", r"\bfinding\b", r"\bnavigation\b", r"\bnavigate[sd]?\b", r"\bnavigating\b", r"\bfilter[s]?\b", 
            r"\bsort[s]?\b", r"\bsorting\b", r"\blayout[s]?\b", r"\bhomepage[s]?\b", r"\bscreen[s]?\b", r"\bbutton[s]?\b", r"\bui\b", r"\bux\b"
        ],
        "why_selected": "Evaluates the ease of searching and finding products inside the catalog."
    },
    {
        "topic": "Pricing & Value Influence",
        "patterns": [
            r"\bprice[s]?\b", r"\bpricing\b", r"\bcharge[s]?\b", r"\bcharging\b", r"\bcost[s]?\b", r"\bexpensive\b", r"\bcheap\b", r"\boverprice[d]?\b", r"\boverpricing\b", 
            r"\bdiscount[s]?\b", r"\bcoupon[s]?\b", r"\bpromo[s]?\b", r"\bpromotion[s]?\b", r"\boffer[s]?\b", r"\btrial\s+price[s]?\b"
        ],
        "why_selected": "Analyzes how pricing and discount structures influence new category trial."
    },
    {
        "topic": "Quality, Trust & Freshness",
        "patterns": [
            r"\bquality\b", r"\btrust\b", r"\brotten\b", r"\bstale\b", r"\bfreshness\b", r"\bbruised\b", 
            r"\bexpiry\b", r"\bexpiration\b", r"\bsubstitute[s]?\b", r"\bsubstitution[s]?\b"
        ],
        "why_selected": "Examines quality trust barriers that prevent users from exploring fresh categories."
    },
    {
        "topic": "Competitor Comparison",
        "patterns": [
            r"\bzepto\b", r"\binstamart\b", r"\bbigbasket\b", r"\bdunzo\b", r"\bbb\b", 
            r"\bblinkit\s+vs\b", r"\bzepto\s+vs\b"
        ],
        "why_selected": "Compares shopping experience and category layout with competitor platforms."
    },
    {
        "topic": "Recommendations & Personalization",
        "patterns": [
            r"\brecommend[s]?\b", r"\brecommendation[s]?\b", r"\bsuggestion[s]?\b", r"\bsuggest[s]?\b", r"\bsuggested\b", r"\bpersonalize[sd]?\b", r"\bpersonalization\b", 
            r"\brelevant\b", r"\binterest[s]?\b", r"\bprompt\b"
        ],
        "why_selected": "Focuses on app-driven product recommendations and personalization."
    },
    {
        "topic": "Brand Switching",
        "patterns": [
            r"\bbrand[s]?\b", r"\bswitch(es)?\b", r"\bswitching\b", r"\bshift[s]?\b", r"\bshifted\b", r"\bshifting\b", 
            r"\bmoved\b", r"\bmove[s]?\b", r"\bmoving\b", r"\bmigrated?\b", r"\bmigrating\b", r"\balternate[s]?\b", r"\balternative[s]?\b"
        ],
        "why_selected": "Discusses shifting preferences from one brand to another or brand substitution."
    },
    {
        "topic": "Wishlist & Favourites",
        "patterns": [
            r"\bwishlist[s]?\b", r"\bfavourite[s]?\b", r"\bfavorite[s]?\b", r"\bsave[d]?\s+for\s+later\b", r"\bsaved\s+item[s]?\b", r"\bheart[s]?\b", r"\bbookmark[s]?\b"
        ],
        "why_selected": "Discusses wishlisting, bookmarking, or saving products for later."
    }
]

# Exclusion keywords (if matches these, it's likely technical noise primarily and should be removed)
EXCLUSION_KEYWORDS = [
    # Login / OTP
    r"\botp\b", r"\blogin\b", r"\bregister\b", r"\bsign\s*in\b", r"\bverification\b", r"\bverify\b", r"\bsignup\b", r"\bsign\s*up\b",
    # App crashes / freeze
    r"\bcrashed\b", r"\bcrashes\b", r"\bcrashing\b", r"\bcrash\b", r"\bhang\b", r"\bfreeze\b", r"\bbug\b", r"\bbugs\b", r"\bglitch\b", r"\bglitches\b",
    # Payment failures & Refunds
    r"\bpayment\b", r"\bpayments\b", r"\btransaction\b", r"\bupi\b", r"\brefund\b", r"\brefunds\b", r"\bdeducted\b", r"\bpay\b", r"\bpaying\b", r"\bcard\b", r"\bbank\b", r"\bwallet\b",
    # Installation & Updates
    r"\binstall\b", r"\binstallation\b", r"\buninstall\b", r"\bdownload\b", r"\bupdating\b",
    # Server / Network
    r"\bnetwork\b", r"\bserver\b", r"\binternet\b", r"\bconnection\b", r"\bloading\b",
    # Customer Support
    r"\bsupport\b", r"\bchat\b", r"\bbot\b", r"\bchatbot\b", r"\bagent\b", r"\brepresentative\b", r"\bcustomer\s+care\b", r"\bcustomer\s+service\b",
    # Address / Location / Map
    r"\baddress\b", r"\baddresses\b", r"\blocation\b", r"\blocations\b", r"\bgps\b", r"\bmap\b", r"\bmaps\b",
    # Account issues / block
    r"\bblocked\b", r"\bblock\b", r"\baccount\b", r"\baccounts\b"
]

GENERIC_PHRASES = {
    "good", "nice", "bad", "worst", "excellent", "ok", "super", "love", "fast", 
    "quick", "speed", "very good", "best app", "good app", "bad app", "worst app", 
    "great app", "awesome app", "nice app", "very nice", "helpful", "good service"
}

def is_generic_or_noise(text: str) -> bool:
    """Checks if text is too short, generic, or primary technical noise."""
    text_clean = text.lower().strip().replace(".", "").replace("!", "").replace(",", "")
    words = text_clean.split()
    
    # Exclude short reviews
    if len(words) < 5:
        return True
        
    # Exclude generic exact phrases
    if text_clean in GENERIC_PHRASES:
        return True
        
    # Check strict technical noise exclusions
    for pattern in EXCLUSION_KEYWORDS:
        if re.search(pattern, text_clean):
            return True
                
    return False


def classify_relevant_topic(text: str) -> tuple:
    """Finds the first matching relevant topic and its reason, returning (topic, why_selected)."""
    text_lower = text.lower()
    for category in TOPIC_TAXONOMY:
        for pattern in category["patterns"]:
            if re.search(pattern, text_lower):
                return category["topic"], category["why_selected"]
    return None, None

def main():
    if not os.path.exists(INPUT_PATH):
        print(f"ERROR: Input clean dataset not found at {INPUT_PATH}")
        sys.exit(1)
        
    print(f"Reading clean dataset from {INPUT_PATH}...")
    
    original_count = 0
    removed_count = 0
    relevant_reviews = []
    topic_counts = {}
    
    with open(INPUT_PATH, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            original_count += 1
            text = row.get("review_text", "")
            
            # 1. Filter out generic, short, and technical noise
            if is_generic_or_noise(text):
                removed_count += 1
                continue
                
            # 2. Classify by topic
            topic, why_selected = classify_relevant_topic(text)
            if not topic:
                removed_count += 1
                continue
                
            row["relevant_topic"] = topic
            row["why_selected"] = why_selected
            relevant_reviews.append(row)
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
            
    print(f"Filtering complete. Writing relevant dataset to {OUTPUT_PATH}...")
    
    try:
        with open(OUTPUT_PATH, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                "source", "date", "rating", "review_text", 
                "cleaned_text", "relevant_topic", "why_selected", "review_url"
            ])
            for r in relevant_reviews:
                writer.writerow([
                    r["source"],
                    r["date"],
                    r["rating"],
                    r["review_text"],
                    r["cleaned_text"],
                    r["relevant_topic"],
                    r["why_selected"],
                    r.get("review_url", "")
                ])
                
        print("\n" + "=" * 60)
        print("                 DATA FILTERING SUMMARY")
        print("=" * 60)
        print(f"Original review count      : {original_count}")
        print(f"Reviews removed            : {removed_count}")
        print(f"Final relevant review count: {len(relevant_reviews)}")
        print("\nRelevant Count by Topic:")
        for topic, count in sorted(topic_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {topic:30} : {count:4} reviews")
        print("\nLocation of generated file:")
        print(f"  - Relevant file: {OUTPUT_PATH}")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"ERROR: Failed to write output file: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
