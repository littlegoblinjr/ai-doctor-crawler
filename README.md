#ai-doctor-crawler

````markdown
# Data Scraper and Google Sheets Updater

This project scrapes data related to various specialists (doctors and fitness trainers) from multiple sources such as Practo, Apollo, and Fittr, processes the data using language models, and updates a Google Sheet with the extracted information.

## Prerequisites

Before you run the scraper, make sure you have the following:

1. **Google Cloud Project**: You will need a Google Cloud project with the Sheets API enabled.
2. **Service Account Credentials**: Create a service account with Google Sheets API access and download the credentials as a JSON file (`credentials.json`).
3. **Dependencies**: Install the required Python libraries.

### Install Dependencies

```bash
pip install asyncio gspread google-auth crawl4ai langchain langchain_groq lmstudio
````

### Files Needed

1. **credentials.json**: Google Sheets API credentials file.
2. **Output JSON**: The scraped data will be saved as `scraped_data.json`.
3. **Google Sheet**: You should have a Google Sheet with the given `SHEET_ID` and a worksheet named `Sheet1` to update with scraped data.

## How to Set Up

1. **Set up your Google Sheets and credentials**:

   * Create a Google Sheets file.
   * Share the sheet with the email associated with your service account (this can be found in the `credentials.json` file).
   * Copy the `SHEET_ID` from the Google Sheets URL and paste it into the `SHEET_ID` variable in the code.

2. **Update the Configuration Variables**:

   * **SHEET\_ID**: Replace with the ID of your Google Sheets document.
   * **WORKSHEET\_NAME**: This is the name of the sheet (usually "Sheet1").
   * **CREDS\_FILE**: Path to your `credentials.json` file.
   * **OUTPUT\_JSON**: The filename to store the scraped data.
   * **SLEEP\_BETWEEN\_REQUESTS**: Time to wait between scrapes to avoid rate limits.

## Code Explanation

### Classes and Functions

#### 1. `DataScraper`

* Handles all the scraping logic and interactions with Google Sheets.

* **`scrape_specialist(self, specialist: str)`**: Scrapes data for a specific specialist from multiple sources like Apollo, Practo, and Fittr.

* **`extract_doctor_info(self, text)`**: Extracts doctor and fitness trainer information from the text using the language model.

* **`update_sheets(self, data: List[Dict])`**: Updates the Google Sheet with the scraped data, adding it as rows in the sheet.

* **`scrape_all(self)`**: Scrapes data for all specified specialists (doctors and fitness trainers).

* **`handle_specialist_recommendation(self)`**: Aggregates scraped data, processes it, and returns doctor recommendations in the required format.

#### 2. `chunk_text(self, text_list, chunk_size=5000)`

* Helper function to split large text into smaller chunks to avoid processing limits or timeouts.

#### 3. `run(self)`

* Main function to run the entire scraping and updating process, which calls the other methods in sequence.

#### 4. `scheduled_scraper()`

* A scheduler that runs the scraper once every 24 hours.

## How to Run

1. **Run Once Immediately**:
   To run the scraper once immediately and update the Google Sheet, use the following:

   ```bash
   python scraper.py
   ```

2. **Run on a Schedule**:
   If you want to run the scraper periodically (e.g., every 24 hours), you can use the scheduled scraper:

   ```bash
   # Uncomment the following in the code:
   # asyncio.run(scheduled_scraper())
   ```

   This will run the scraper every 24 hours.

## Example Output

After scraping data, the results are saved in `scraped_data.json` and also updated in your Google Sheet with columns like:

* **Specialist**: The type of specialist (e.g., "Cardiologist").
* **Doctor Name**: Name of the doctor or coach.
* **Clinic**: Clinic name.
* **Location**: The location of the doctor/coach.
* **Fees**: Consultation fee.
* **Availability**: The availability of the doctor/coach.
* **Profile Link**: URL to the profile.
* **Site Name**: The source of the data (e.g., "Apollo", "Practo", "Fittr").
* **Timestamp**: The timestamp when the data was updated.

## Troubleshooting

1. **Invalid JSON Errors**:

   * If you encounter invalid JSON errors, check the output and ensure the formatting is correct in the `scraped_data.json`.

2. **API Quotas**:

   * Google Sheets API has quotas, so if you're hitting rate limits, consider adding a delay between operations.

3. **Missing Data**:

   * If certain fields are missing in the scraped data (e.g., doctor's name, clinic), ensure that the source page contains the necessary information. You may need to modify the scraping logic for specific sources.

## License

MIT License. See the `LICENSE` file for details.

## Acknowledgements

* This project leverages **LangChain**, **crawl4ai**, and **lmstudio** for web scraping and natural language processing.
* Special thanks to the Google API for Sheets integration and the service account credentials.

```

```
