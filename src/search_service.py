import requests
import re
import tempfile
import warnings
from pathlib import Path
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

class SECSearchService:
    def __init__(self):
        # SEC requires a specific User-Agent format: "Name Email"
        self.headers = {"User-Agent": "vasyloki vasyloki888@gmail.com"}
        # Map for common tickers to CIKs (Optimized for speed)
        self.cik_map = {
            "NVDA": "0001045810", 
            "TSM": "0001103034",   
            "TSMC": "0001103034",  
            "META": "0001326801",  
            "AAPL": "0000320193",
            "GOOG": "0001652044",
            "GOOGL": "0001652044",
            "MSFT": "0000789019"
        }

    def get_filing_list(self, ticker):
        ticker = ticker.upper()
        cik = self.cik_map.get(ticker)
        
        # --- AUTO-SCOUT FALLBACK ---
        if not cik:
            try:
                ticker_url = "https://www.sec.gov/files/company_tickers.json"
                res = requests.get(ticker_url, headers=self.headers)
                if res.status_code == 200:
                    data = res.json()
                    for _, val in data.items():
                        if val['ticker'] == ticker:
                            cik = str(val['cik_str']).zfill(10)
                            self.cik_map[ticker] = cik
                            break
            except Exception as e:
                print(f"Auto-Scout failed: {e}")

        if not cik: return []

        url = f"https://data.sec.gov/submissions/CIK{cik}.json"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            recent = data.get('filings', {}).get('recent', {})
            acc_nums = recent.get('accessionNumber', [])
            forms = recent.get('form', [])
            dates = recent.get('filingDate', [])
            descriptions = recent.get('primaryDescription', [])
            items = recent.get('items', [])
            
            results = []
            for i in range(len(acc_nums)):
                f_type = forms[i] if i < len(forms) else "Unknown"
                if f_type in ["10-K", "10-Q", "8-K", "20-F", "6-K"]:
                    acc_no = acc_nums[i].replace('-', '')
                    landing_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc_no}/"
                    f_date = dates[i] if i < len(dates) else "N/A"
                    title = descriptions[i] if i < len(descriptions) and descriptions[i] else ""
                    if not title:
                        item_val = items[i] if i < len(items) else ""
                        title = f"{f_type} - {item_val}" if item_val else f"{f_type} Filing"

                    results.append({
                        "type": f_type,
                        "date": f_date,
                        "title": title,
                        "url": landing_url,
                        "ticker": ticker 
                    })
                if len(results) >= 15: break 
            return results
        except Exception as e:
            print(f"JSON Scout failed: {e}")
            return []

    def download_filing(self, filing_data):
        """
        Modified to handle both string URLs and full filing dictionaries.
        Includes high-precision whitelisting to bypass SEC 404 ghost links.
        """
        try:
            # --- TYPE CHECK: The fix for 'string indices must be integers' ---
            if isinstance(filing_data, str):
                landing_url = filing_data
                ticker = ""
            else:
                landing_url = filing_data.get('url', '')
                ticker = filing_data.get('ticker', '').lower()

            if not landing_url:
                return None

            warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
            res = requests.get(landing_url, headers=self.headers)
            res.raise_for_status()
            
            soup = BeautifulSoup(res.text, "xml")
            all_links = [a['href'] for a in soup.find_all('a', href=True)]
            
            if not all_links:
                all_links = re.findall(r'href="([^"]+\.(?:htm|html|pdf))"', res.text)

            target_file = None
            
            # --- 1. EXHIBIT PRIORITY (The CFO Alpha) ---
            for link in all_links:
                l_lower = link.lower()
                if any(ex in l_lower for ex in ["ex99-1", "ex99_1", "ex991"]):
                    target_file = link
                    break
                if any(ex in l_lower for ex in ["ex99-2", "ex99_2", "ex992"]):
                    target_file = link
                    break

            # --- 2. THE TICKER WHITELIST (Primary Reports) ---
            if not target_file and ticker:
                for link in all_links:
                    l_lower = link.lower()
                    if ticker in l_lower and any(ext in l_lower for ext in [".htm", ".html", ".pdf"]):
                        if not any(junk in l_lower for junk in ["index", "hdr", "search", "howinvestigationswork"]):
                            target_file = link
                            break

            # --- 3. THE "DIGIT" HEURISTIC (Final Fallback) ---
            if not target_file:
                for link in all_links:
                    l_lower = link.lower()
                    if any(junk in l_lower for junk in ["howinvestigationswork", "search", "index", "hdr", "banner"]):
                        continue
                    
                    if any(ext in l_lower for ext in [".htm", ".html", ".pdf"]):
                        if any(char.isdigit() for char in l_lower):
                            target_file = link
                            break
            
            if target_file:
                # Handle relative path resolution
                doc_url = target_file if target_file.startswith("http") else landing_url + target_file.split('/')[-1]
                doc_res = requests.get(doc_url, headers=self.headers)
                doc_res.raise_for_status()
                
                suffix = Path(target_file).suffix
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(doc_res.content)
                    return Path(tmp.name)
                    
            return None
        except Exception as e:
            print(f"Document extraction failed: {e}")
            return None