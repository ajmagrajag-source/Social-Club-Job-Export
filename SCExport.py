import streamlit as st
import re
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType  
from st_copy_to_clipboard import st_copy_to_clipboard
from io import StringIO
import csv
import time
import json
import streamlit as st

# Page config
st.set_page_config(
    page_title="Rockstar Job Scraper",
    page_icon="🎮",
    layout="wide"
)

# Default settings
DEFAULT_SETTINGS = {
    # BBCode settings
    'bbcode_jobnumbering': True,
    'bbcode_jobname': True,
    'bbcode_jobcreator': True,
    'bbcode_jobicon': True,
    'bbcode_jobtype': True,
    'bbcode_maxplayers': True,
    'bbcode_gtalens': False,
    'bbcode_jobimage': False,
    'bbcode_jobdescription': False,
    'bbcode_creationdate': False,
    'bbcode_lastupdated': False,
    'bbcode_linebreak': True,
    'bbcode_custom': '',
    'bbcode_use_custom': False,
    
    # Markdown settings
    'markdown_jobnumbering': True,
    'markdown_title': False,
    'markdown_jobname': True,
    'markdown_jobcreator': True,
    'markdown_jobtype': True,
    'markdown_maxplayers': True,
    'markdown_gtalens': False,
    'markdown_jobimage': False,
    'markdown_jobdescription': False,
    'markdown_creationdate': False,
    'markdown_lastupdated': False,
    'markdown_linebreak': True,
    
    # YouTube settings
    'youtube_jobnumbering': True,
    'youtube_jobtimestamp': False,
    'youtube_jobname': True,
    'youtube_jobcreator': True,
    'youtube_jobtype': True,
    'youtube_maxplayers': False,
    'youtube_gtalens': False,
    'youtube_jobdescription': False,
    'youtube_creationdate': False,
    'youtube_lastupdated': False,
    'youtube_linebreak': False,
    
    # Text settings
    'text_jobnumbering': True,
    'text_jobname': True,
    'text_jobcreator': True,
    'text_joburl': False,
    'text_jobtype': False,
    'text_maxplayers': False,
    'text_gtalens': False,
    'text_jobdescription': False,
    'text_creationdate': False,
    'text_lastupdated': False,
    'text_linebreak': False,
    
    # CSV settings
    'csv_headers': True,
    'csv_jobname': True,
    'csv_joburl': True,
    'csv_jobcreator': True,
    'csv_jobtype': True,
    'csv_maxplayers': False,
    'csv_gtalens': False,
    'csv_jobimage': False,
    'csv_jobdescription': False,
    'csv_creationdate': False,
    'csv_lastupdated': False,
    'csv_custom': '',
    'csv_use_custom': False,
}

# Initialize session state for settings
def initialize_session_state():
    """Initialize session state variables"""
    if 'settings' not in st.session_state:
        st.session_state.settings = DEFAULT_SETTINGS.copy()
        
    if 'current_export_format' not in st.session_state:
        st.session_state.current_export_format = 'BBCode'

# URL processing functions
def extract_job_hash(job_url):
    """Extract job hash from Rockstar Social Club URL"""
    try:
        match = re.search(r'/job/gtav/([a-zA-Z0-9_-]+)', job_url)
        return match.group(1) if match else None
    except:
        return None

def extract_max_players(player_string):
    """Extract the maximum number from a player count string like '1 to 30'"""
    if not player_string:
        return ""
    numbers = re.findall(r'\d+', player_string)
    if not numbers:
        return player_string
    return numbers[-1]

def validate_and_clean_urls(text):
    """Extract and validate Rockstar Social Club URLs from input text"""
    job_pattern = r'https://socialclub\.rockstargames\.com/job/gtav/[a-zA-Z0-9_-]+'
    playlist_pattern = r'https://socialclub\.rockstargames\.com/games/gtav/[a-zA-Z0-9_/\?=&-]+'
    
    job_urls = re.findall(job_pattern, text)
    playlist_urls = re.findall(playlist_pattern, text)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_urls = []
    
    for url in job_urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)
    
    return unique_urls, playlist_urls

# Web scraping functions
def setup_driver():
    """Set up and return a Chrome driver instance"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # Use ChromeType.CHROMIUM to match the installed browser
    service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_window_size(1366, 768)
    
    return driver
def bypass_age_gate(driver):
    """Try to bypass Rockstar Social Club age gate"""
    try:
        month_select = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'select[aria-label="Month"]'))
        )
        
        Select(month_select).select_by_value('1')
        Select(driver.find_element(By.CSS_SELECTOR, 'select[aria-label="Day"]')).select_by_value('1')
        Select(driver.find_element(By.CSS_SELECTOR, 'select[aria-label="Year"]')).select_by_value('1990')
        
        time.sleep(0.5)
        submit_button = driver.find_element(By.CSS_SELECTOR, 'button[data-ui-name="submitButton"]')
        submit_button.click()
        time.sleep(2)
        
        return True
    except:
        return False

def extract_playlist_jobs(driver, playlist_url):
    """Extract job links from a playlist page"""
    try:
        driver.get(playlist_url)
        
        # Try to bypass age gate if present
        bypass_age_gate(driver)
        
        # Wait for the page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'body'))
        )
        time.sleep(3)
        
        # Find all mission links with data-id attribute
        mission_elements = driver.find_elements(By.CSS_SELECTOR, 'a.mission[data-id]')
        
        job_links = []
        for element in mission_elements:
            data_id = element.get_attribute('data-id')
            if data_id:
                job_url = f"https://socialclub.rockstargames.com/job/gtav/{data_id}"
                job_links.append(job_url)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_job_links = []
        for url in job_links:
            if url not in seen:
                seen.add(url)
                unique_job_links.append(url)
        
        return unique_job_links
    except Exception as e:
        st.error(f"Error extracting playlist jobs: {str(e)}")
        return []

def safe_get_text(driver, selectors):
    """Try multiple selectors to get text"""
    for selector in selectors:
        try:
            element = driver.find_element(By.CSS_SELECTOR, selector)
            text = element.text.strip()
            if text:
                return text
        except:
            continue
    return ''

def safe_get_attribute(driver, selectors, attribute):
    """Try multiple selectors to get an attribute"""
    for selector in selectors:
        try:
            element = driver.find_element(By.CSS_SELECTOR, selector)
            attr = element.get_attribute(attribute)
            if attr:
                return attr
        except:
            continue
    return ''

def get_stat_value(driver, label_text):
    """Get the value for a specific stat label"""
    try:
        stat_rows = driver.find_elements(By.CSS_SELECTOR, 'div[class*="statRow"]')
        for row in stat_rows:
            try:
                label_element = row.find_element(By.CSS_SELECTOR, 'div:first-child')
                label = label_element.text.strip()
                if label == label_text:
                    value_element = row.find_element(By.CSS_SELECTOR, 'div[class*="statValue"]')
                    return value_element.text.strip()
            except:
                continue
        return ''
    except:
        return ''

def get_job_icon(job_type):
    """Return the appropriate BBCode smiley for job type (designed for gccc.boards.net)"""
    icons = {
        'Race': ':race:',
        'Deathmatch': ':dm:',
        'Team Deathmatch': ':tdm:',
        'Vehicle Deathmatch': ':vdm:',
        'King of the Hill': ':koth:',
        'Team King of the Hill': ':koth:',
        'Open Wheel Race': ':open:',
        'Stunt Race': ':stunt:',
        'Land Race': ':land:',
        'Air Race': ':air:',
        'Sea Race': ':sea:',
        'Bike Race': ':bike:',
        'Last Team Standing': ':lts:',
        'Capture': ':capture:',
        'Parachuting': ':parachute:',
        'Survival': ':survival:',
    }
    return icons.get(job_type, ':race:')

def scrape_job_data(driver, job_url):
    """Scrape job data from the loaded page"""
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'h1'))
        )
        time.sleep(2)
        
        job_name = safe_get_text(driver, [
            'h1[class*="title"]',
            'h1[class*="Ugc__title"]',
            'h1'
        ])
        
        job_creator = safe_get_text(driver, [
            'span[class*="PlayerCard"] span[class*="markedText"]',
            'span[class*="username"] span[class*="markedText"]',
            '.markedText'
        ])
        
        job_description = safe_get_text(driver, [
            'p[class*="description"]',
            'p[class*="Ugc__description"]',
            '.Ugc__stats__ p'
        ])
        
        job_image = safe_get_attribute(driver, [
            'img[class*="missionImage"]',
            'img[class*="Ugc__missionImage"]',
            'img[src*="ugc"]'
        ], 'src')
        
        job_type = get_stat_value(driver, "Game Mode")
        raw_max_players = get_stat_value(driver, "Players")
        creation_date = get_stat_value(driver, "Creation Date")
        last_updated = get_stat_value(driver, "Last Updated")
        
        job_data = {
            "jobName": job_name,
            "jobCreator": job_creator,
            "jobType": job_type,
            "jobIcon": get_job_icon(job_type),
            "jobDescription": job_description,
            "jobImage": job_image,
            "maxPlayers": extract_max_players(raw_max_players),
            "creationDate": creation_date,
            "lastUpdated": last_updated,
        }
        
        job_hash = extract_job_hash(job_url)
        job_data["GTALens"] = f"https://gtalens.com/job/{job_hash}" if job_hash else ""
        job_data["originalURL"] = job_url
        
        return job_data
    except Exception as e:
        st.error(f"Error scraping: {str(e)}")
        return None

def scrape_multiple_jobs(urls, progress_bar, status_text):
    """Scrape multiple job URLs"""
    results = []
    driver = None
    
    try:
        driver = setup_driver()
        age_gate_bypassed = False
        
        for i, url in enumerate(urls):
            status_text.text(f"Scraping job {i+1} of {len(urls)}...")
            progress_bar.progress((i + 1) / len(urls))
            
            try:
                driver.get(url)
                
                if not age_gate_bypassed:
                    age_gate_bypassed = bypass_age_gate(driver)
                
                job_data = scrape_job_data(driver, url)
                
                if job_data and job_data.get('jobName') and job_data.get('jobCreator'):
                    results.append(job_data)
                else:
                    results.append({
                        "jobName": "Failed to scrape",
                        "jobCreator": "",
                        "jobType": "",
                        "jobIcon": "❌",
                        "jobDescription": "",
                        "jobImage": "",
                        "maxPlayers": "",
                        "creationDate": "",
                        "lastUpdated": "",
                        "GTALens": "",
                        "originalURL": url
                    })
                
                if i < len(urls) - 1:
                    time.sleep(2)
                    
            except Exception as e:
                st.error(f"Error processing {url}: {str(e)}")
                results.append({
                    "jobName": "Error",
                    "jobCreator": "",
                    "jobType": "",
                    "jobIcon": "❌",
                    "jobDescription": str(e),
                    "jobImage": "",
                    "maxPlayers": "",
                    "creationDate": "",
                    "lastUpdated": "",
                    "GTALens": "",
                    "originalURL": url
                })
        
        return results
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

# Data display functions
def create_clickable_table(jobs_df):
    """Create a table with clickable links"""
    display_df = jobs_df.copy()
    
    display_df['Job Name'] = display_df.apply(
        lambda row: f'<a href="{row["originalURL"]}" target="_blank">{row["jobName"]}</a>',
        axis=1
    )
    
    display_df['GTALens'] = display_df.apply(
        lambda row: f'<a href="{row["GTALens"]}" target="_blank">GTALens Link</a>' if row["GTALens"] else "",
        axis=1
    )
    
    display_df = display_df[['Job Name', 'jobCreator', 'jobType', 'maxPlayers', 'creationDate', 'GTALens']]
    display_df.columns = ['Job Name', 'Creator', 'Game Mode', 'Max Players', 'Creation Date', 'GTALens']
    
    return display_df

def display_table_view(scraped_jobs):
    """Display jobs in a table format"""
    df = pd.DataFrame(scraped_jobs)
    display_df = create_clickable_table(df)
    st.markdown(display_df.to_html(escape=False, index=False), unsafe_allow_html=True)

def display_card_view(scraped_jobs):
    """Display jobs in a card format"""
    for i, job in enumerate(scraped_jobs, 1):
        with st.expander(f"🎮 {job['jobName']} - by {job['jobCreator']}", expanded=False):
            col1, col2 = st.columns([1, 2])
            
            with col1:
                if job['jobImage']:
                    st.image(job['jobImage'], use_container_width=True)
                else:
                    st.info("No image available")
            
            with col2:
                st.markdown(f"**Job Name:** {job['jobName']}")
                st.markdown(f"**Creator:** {job['jobCreator']}")
                st.markdown(f"**Game Mode:** {job['jobType']}")
                st.markdown(f"**Max Players:** {job['maxPlayers']}")
                st.markdown(f"**Creation Date:** {job['creationDate']}")
                st.markdown(f"**Last Updated:** {job['lastUpdated']}")
                
                if job['jobDescription']:
                    st.markdown(f"**Description:** {job['jobDescription']}")
                
                st.markdown(f"**Original URL:** [Open in Social Club]({job['originalURL']})")
                
                if job['GTALens']:
                    st.markdown(f"**GTALens:** [View in GTALens]({job['GTALens']})")

# Export generation functions
def generate_bbcode(jobs, settings):
    """Generate BBCode format"""
    content = ''
    for index, job in enumerate(jobs):
        if settings['bbcode_jobnumbering']:
            content += f"{index + 1}. "
        if settings['bbcode_jobicon']:
            content += f"{job['jobIcon']} "
        if settings['bbcode_jobtype']:
            content += f"{job['jobType']} - "
        if settings['bbcode_jobname']:
            content += f"[b][url={job['originalURL']}]{job['jobName']}[/url][/b] "
        if settings['bbcode_jobcreator']:
            content += f"by @{job['jobCreator']} "
        if settings['bbcode_maxplayers'] and job['maxPlayers'] != "30":
            content += f"(Max: {job['maxPlayers']}) "
        if settings['bbcode_gtalens'] and job['GTALens']:
            content += f"| [url={job['GTALens']}]GTALens[/url] "
        if settings['bbcode_jobimage']:
            content += f"\n\n[img]{job['jobImage']}[/img]\n\n"
        if settings['bbcode_jobdescription']:
            content += f"{job['jobDescription']} "
        if settings['bbcode_creationdate']:
            content += f"\n[b]Created:[/b] {job['creationDate']} "
        if settings['bbcode_lastupdated']:
            content += f"\n[b]Last Updated:[/b] {job['lastUpdated']} "
        if settings['bbcode_use_custom'] and settings['bbcode_custom']:
            content += settings['bbcode_custom'] + ' '
        if settings['bbcode_linebreak']:
            content += '[br]'
        content += '\n'
    return content.strip()

def generate_markdown(jobs, settings):
    """Generate Markdown format"""
    content = ''
    for index, job in enumerate(jobs):
        if settings['markdown_jobnumbering']:
            content += f"{index + 1}. "
        if settings['markdown_title']:
            content += f"{job['jobName']} - {job['originalURL']}\n\n"
        if settings['markdown_jobtype']:
            content += f"{job['jobType']} - "
        if settings['markdown_jobname']:
            content += f"**[{job['jobName']}]({job['originalURL']})** "
        if settings['markdown_jobcreator']:
            content += f"**by @{job['jobCreator']}** "
        if settings['markdown_maxplayers'] and job['maxPlayers'] != "30":
            content += f"(Max: {job['maxPlayers']}) "
        if settings['markdown_gtalens'] and job['GTALens']:
            content += f"| [GTALens]({job['GTALens']}) "
        if settings['markdown_jobimage']:
            content += f"\n{job['jobImage']}"
        if settings['markdown_jobdescription']:
            content += f"\n\n{job['jobDescription']} "
        if settings['markdown_creationdate']:
            content += f"\n\n**Created:** {job['creationDate']} "
        if settings['markdown_lastupdated']:
            content += f"\n**Last Updated:** {job['lastUpdated']} "
        if settings['markdown_linebreak']:
            content += '\n\n'
        else:
            content += '\n'
    return content.strip()

def generate_youtube(jobs, settings):
    """Generate YouTube description format"""
    content = ''
    for index, job in enumerate(jobs):
        line = ''
        if settings['youtube_jobtimestamp']:
            line += 'HH:MM:SS '
        if settings['youtube_jobnumbering']:
            line += f"{index + 1}. "
        if settings['youtube_jobname']:
            line += f"{job['jobName']} "
        if settings['youtube_jobcreator']:
            line += f"by {job['jobCreator']} "
        if settings['youtube_jobtype']:
            line += f"| {job['jobType']} "
        if settings['youtube_maxplayers'] and job['maxPlayers'] != "30":
            line += f"| Max Players: {job['maxPlayers']} "
        if settings['youtube_gtalens'] and job['GTALens']:
            line += f"| GTALens: {job['GTALens']} "
        if settings['youtube_jobdescription']:
            line += f"\n{job['jobDescription']} "
        if settings['youtube_creationdate']:
            line += f"\nCreated: {job['creationDate']} "
        if settings['youtube_lastupdated']:
            line += f"\nLast Updated: {job['lastUpdated']} "
        line += f"\n{job['originalURL']}"
        if settings['youtube_linebreak']:
            line += '\n\n'
        else:
            line += '\n'
        content += line
    return content.strip()

def generate_text(jobs, settings):
    """Generate plain text format"""
    content = ''
    for index, job in enumerate(jobs):
        line = ''
        if settings['text_jobnumbering']:
            line += f"{index + 1}. "
        if settings['text_jobname']:
            line += f"{job['jobName']} "
        if settings['text_jobcreator']:
            line += f"by {job['jobCreator']} "
        if settings['text_joburl']:
            line += f"- {job['originalURL']} "
        if settings['text_jobtype']:
            line += f"| Type: {job['jobType']} "
        if settings['text_maxplayers']:
            line += f"| Max Players: {job['maxPlayers']} "
        if settings['text_gtalens'] and job['GTALens']:
            line += f"| GTALens: {job['GTALens']} "
        if settings['text_jobdescription']:
            line += f"\nDescription: {job['jobDescription']}"
        if settings['text_creationdate']:
            line += f"\nCreated: {job['creationDate']}"
        if settings['text_lastupdated']:
            line += f"\nLast Updated: {job['lastUpdated']}"
        if settings['text_linebreak']:
            line += '\n\n'
        else:
            line += '\n'
        content += line
    return content.strip()

def generate_csv(jobs, settings):
    """Generate CSV format with proper escaping using Python's csv module"""
    # Create StringIO object to write CSV data
    output = StringIO()
    
    # Define header mappings
    header_mappings = {
        'csv_jobname': 'Job Name',
        'csv_joburl': 'Job URL',
        'csv_jobcreator': 'Job Creator',
        'csv_jobtype': 'Job Type',
        'csv_maxplayers': 'Max Players',
        'csv_gtalens': 'GTALens Link',
        'csv_jobimage': 'Job Image',
        'csv_jobdescription': 'Job Description',
        'csv_creationdate': 'Date Created',
        'csv_lastupdated': 'Date Updated',
    }
    
    # Get enabled headers
    enabled_headers = [key for key in header_mappings.keys() if settings.get(key, False)]
    
    if settings.get('csv_use_custom', False) and settings.get('csv_custom', ''):
        enabled_headers.append('csv_custom')
        header_mappings['csv_custom'] = 'Custom'
    
    # Create CSV writer with proper escaping
    # QUOTE_MINIMAL only quotes fields when necessary (commas, quotes, newlines)
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
    
    # Write headers if enabled
    if settings.get('csv_headers', True):
        writer.writerow([header_mappings[key] for key in enabled_headers])
    
    # Write data rows
    for job in jobs:
        row = []
        for key in enabled_headers:
            if key == 'csv_jobname':
                row.append(job['jobName'] or '')
            elif key == 'csv_joburl':
                row.append(job['originalURL'] or '')
            elif key == 'csv_jobcreator':
                row.append(job['jobCreator'] or '')
            elif key == 'csv_jobtype':
                row.append(job['jobType'] or '')
            elif key == 'csv_maxplayers':
                row.append(job['maxPlayers'] or '')
            elif key == 'csv_gtalens':
                row.append(job['GTALens'] or '')
            elif key == 'csv_jobimage':
                row.append(job['jobImage'] or '')
            elif key == 'csv_jobdescription':
                row.append(job['jobDescription'] or '')
            elif key == 'csv_creationdate':
                row.append(job['creationDate'] or '')
            elif key == 'csv_lastupdated':
                row.append(job['lastUpdated'] or '')
            elif key == 'csv_custom':
                row.append(settings.get('csv_custom', ''))
        
        writer.writerow(row)
    
    # Get the CSV content
    csv_content = output.getvalue()
    output.close()
    
    return csv_content.strip()

def display_code_with_copy_button(content, format_name, key_prefix):
    """Display code with a working copy button using st-copy-to-clipboard"""
    # Create columns for the header and copy button
    col1, col2 = st.columns([5, 1])
    with col1:
        st.markdown(f"#### 📋 {format_name} Output")
    with col2:
        # Use the streamlit-copy-to-clipboard component
        st_copy_to_clipboard(
            text=content,
            before_copy_label="📋 Copy",
            after_copy_label="✅ Copied!",
            key=f"copy_{key_prefix}"
        )
    
    # Display the code (this will update when checkboxes change)
    st.code(content, language=None, line_numbers=False)
    
    st.info("💡 Use the '📋 Copy' button above or the small copy icon in the code block corner!")

# Settings management functions
def reset_settings_to_default():
    """Reset settings to default values"""
    st.session_state.settings = DEFAULT_SETTINGS.copy()
    st.success("✅ Settings reset to default!")
    time.sleep(0.5)
    st.rerun()

def export_settings():
    """Export settings as JSON"""
    settings_json = json.dumps(st.session_state.settings, indent=2)
    return settings_json

def import_settings(uploaded_file):
    """Import settings from JSON file"""
    try:
        loaded_settings = json.loads(uploaded_file.read())
        st.session_state.settings.update(loaded_settings)
        st.success("✅ Settings imported!")
        time.sleep(1)
        st.rerun()
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# Export format UI functions with auto-generation
def display_bbcode_settings():
    """Display BBCode export settings with auto-generation"""
    st.markdown("### BBCode Settings")
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.settings['bbcode_jobnumbering'] = st.checkbox("Job Numbering", value=st.session_state.settings['bbcode_jobnumbering'], key='bb_num')
        st.session_state.settings['bbcode_jobname'] = st.checkbox("Job Name", value=st.session_state.settings['bbcode_jobname'], key='bb_name')
        st.session_state.settings['bbcode_jobcreator'] = st.checkbox("Job Creator", value=st.session_state.settings['bbcode_jobcreator'], key='bb_creator')
        st.session_state.settings['bbcode_jobicon'] = st.checkbox("Job Icon", value=st.session_state.settings['bbcode_jobicon'], key='bb_icon')
        st.session_state.settings['bbcode_jobtype'] = st.checkbox("Job Type", value=st.session_state.settings['bbcode_jobtype'], key='bb_type')
        st.session_state.settings['bbcode_maxplayers'] = st.checkbox("Max Players", value=st.session_state.settings['bbcode_maxplayers'], key='bb_max')
    with col2:
        st.session_state.settings['bbcode_gtalens'] = st.checkbox("GTALens Link", value=st.session_state.settings['bbcode_gtalens'], key='bb_lens')
        st.session_state.settings['bbcode_jobimage'] = st.checkbox("Job Image", value=st.session_state.settings['bbcode_jobimage'], key='bb_img')
        st.session_state.settings['bbcode_jobdescription'] = st.checkbox("Job Description", value=st.session_state.settings['bbcode_jobdescription'], key='bb_desc')
        st.session_state.settings['bbcode_creationdate'] = st.checkbox("Creation Date", value=st.session_state.settings['bbcode_creationdate'], key='bb_create')
        st.session_state.settings['bbcode_lastupdated'] = st.checkbox("Last Updated", value=st.session_state.settings['bbcode_lastupdated'], key='bb_update')
        st.session_state.settings['bbcode_linebreak'] = st.checkbox("Line Break", value=st.session_state.settings['bbcode_linebreak'], key='bb_break')
    
    st.session_state.settings['bbcode_use_custom'] = st.checkbox("Use Custom BBCode", value=st.session_state.settings['bbcode_use_custom'], key='bb_custom_check')
    if st.session_state.settings['bbcode_use_custom']:
        st.session_state.settings['bbcode_custom'] = st.text_area("Custom BBCode", value=st.session_state.settings['bbcode_custom'], key='bb_custom_text')
    
    # Auto-generate output with copy button
    bbcode_output = generate_bbcode(st.session_state['scraped_jobs'], st.session_state.settings)
    display_code_with_copy_button(bbcode_output, "BBCode", "bbcode")


def display_markdown_settings():
    """Display Markdown export settings with auto-generation"""
    st.markdown("### Markdown Settings")
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.settings['markdown_jobnumbering'] = st.checkbox("Job Numbering", value=st.session_state.settings['markdown_jobnumbering'], key='md_num')
        st.session_state.settings['markdown_title'] = st.checkbox("Post Title", value=st.session_state.settings['markdown_title'], key='md_title')
        st.session_state.settings['markdown_jobname'] = st.checkbox("Job Name", value=st.session_state.settings['markdown_jobname'], key='md_name')
        st.session_state.settings['markdown_jobcreator'] = st.checkbox("Job Creator", value=st.session_state.settings['markdown_jobcreator'], key='md_creator')
        st.session_state.settings['markdown_jobtype'] = st.checkbox("Job Type", value=st.session_state.settings['markdown_jobtype'], key='md_type')
        st.session_state.settings['markdown_maxplayers'] = st.checkbox("Max Players", value=st.session_state.settings['markdown_maxplayers'], key='md_max')
    with col2:
        st.session_state.settings['markdown_gtalens'] = st.checkbox("GTALens Link", value=st.session_state.settings['markdown_gtalens'], key='md_lens')
        st.session_state.settings['markdown_jobimage'] = st.checkbox("Job Image", value=st.session_state.settings['markdown_jobimage'], key='md_img')
        st.session_state.settings['markdown_jobdescription'] = st.checkbox("Job Description", value=st.session_state.settings['markdown_jobdescription'], key='md_desc')
        st.session_state.settings['markdown_creationdate'] = st.checkbox("Creation Date", value=st.session_state.settings['markdown_creationdate'], key='md_create')
        st.session_state.settings['markdown_lastupdated'] = st.checkbox("Last Updated", value=st.session_state.settings['markdown_lastupdated'], key='md_update')
        st.session_state.settings['markdown_linebreak'] = st.checkbox("Line Break", value=st.session_state.settings['markdown_linebreak'], key='md_break')
    
    # Auto-generate output with copy button
    markdown_output = generate_markdown(st.session_state['scraped_jobs'], st.session_state.settings)
    display_code_with_copy_button(markdown_output, "Markdown", "markdown")


def display_youtube_settings():
    """Display YouTube export settings with auto-generation"""
    st.markdown("### YouTube Description Settings")
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.settings['youtube_jobnumbering'] = st.checkbox("Job Numbering", value=st.session_state.settings['youtube_jobnumbering'], key='yt_num')
        st.session_state.settings['youtube_jobtimestamp'] = st.checkbox("Job Timestamp (HH:MM:SS)", value=st.session_state.settings['youtube_jobtimestamp'], key='yt_time')
        st.session_state.settings['youtube_jobname'] = st.checkbox("Job Name", value=st.session_state.settings['youtube_jobname'], key='yt_name')
        st.session_state.settings['youtube_jobcreator'] = st.checkbox("Job Creator", value=st.session_state.settings['youtube_jobcreator'], key='yt_creator')
        st.session_state.settings['youtube_jobtype'] = st.checkbox("Job Type", value=st.session_state.settings['youtube_jobtype'], key='yt_type')
        st.session_state.settings['youtube_maxplayers'] = st.checkbox("Max Players", value=st.session_state.settings['youtube_maxplayers'], key='yt_max')
    with col2:
        st.session_state.settings['youtube_gtalens'] = st.checkbox("GTALens Link", value=st.session_state.settings['youtube_gtalens'], key='yt_lens')
        st.session_state.settings['youtube_jobdescription'] = st.checkbox("Job Description", value=st.session_state.settings['youtube_jobdescription'], key='yt_desc')
        st.session_state.settings['youtube_creationdate'] = st.checkbox("Creation Date", value=st.session_state.settings['youtube_creationdate'], key='yt_create')
        st.session_state.settings['youtube_lastupdated'] = st.checkbox("Last Updated", value=st.session_state.settings['youtube_lastupdated'], key='yt_update')
        st.session_state.settings['youtube_linebreak'] = st.checkbox("Line Break", value=st.session_state.settings['youtube_linebreak'], key='yt_break')
    
    # Auto-generate output with copy button
    youtube_output = generate_youtube(st.session_state['scraped_jobs'], st.session_state.settings)
    display_code_with_copy_button(youtube_output, "YouTube", "youtube")


def display_text_settings():
    """Display Text export settings with auto-generation"""
    st.markdown("### Plain Text Settings")
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.settings['text_jobnumbering'] = st.checkbox("Job Numbering", value=st.session_state.settings['text_jobnumbering'], key='txt_num')
        st.session_state.settings['text_jobname'] = st.checkbox("Job Name", value=st.session_state.settings['text_jobname'], key='txt_name')
        st.session_state.settings['text_jobcreator'] = st.checkbox("Job Creator", value=st.session_state.settings['text_jobcreator'], key='txt_creator')
        st.session_state.settings['text_joburl'] = st.checkbox("Job URL", value=st.session_state.settings['text_joburl'], key='txt_url')
        st.session_state.settings['text_jobtype'] = st.checkbox("Job Type", value=st.session_state.settings['text_jobtype'], key='txt_type')
        st.session_state.settings['text_maxplayers'] = st.checkbox("Max Players", value=st.session_state.settings['text_maxplayers'], key='txt_max')
    with col2:
        st.session_state.settings['text_gtalens'] = st.checkbox("GTALens Link", value=st.session_state.settings['text_gtalens'], key='txt_lens')
        st.session_state.settings['text_jobdescription'] = st.checkbox("Job Description", value=st.session_state.settings['text_jobdescription'], key='txt_desc')
        st.session_state.settings['text_creationdate'] = st.checkbox("Creation Date", value=st.session_state.settings['text_creationdate'], key='txt_create')
        st.session_state.settings['text_lastupdated'] = st.checkbox("Last Updated", value=st.session_state.settings['text_lastupdated'], key='txt_update')
        st.session_state.settings['text_linebreak'] = st.checkbox("Line Break", value=st.session_state.settings['text_linebreak'], key='txt_break')
    
    # Auto-generate output with copy button
    text_output = generate_text(st.session_state['scraped_jobs'], st.session_state.settings)
    display_code_with_copy_button(text_output, "Text", "text")


def display_csv_settings():
    """Display CSV export settings with auto-generation"""
    st.markdown("### CSV Settings")
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.settings['csv_headers'] = st.checkbox("Include Headers", value=st.session_state.settings['csv_headers'], key='csv_head')
        st.session_state.settings['csv_jobname'] = st.checkbox("Job Name", value=st.session_state.settings['csv_jobname'], key='csv_name')
        st.session_state.settings['csv_joburl'] = st.checkbox("Job URL", value=st.session_state.settings['csv_joburl'], key='csv_url')
        st.session_state.settings['csv_jobcreator'] = st.checkbox("Job Creator", value=st.session_state.settings['csv_jobcreator'], key='csv_creator')
        st.session_state.settings['csv_jobtype'] = st.checkbox("Job Type", value=st.session_state.settings['csv_jobtype'], key='csv_type')
        st.session_state.settings['csv_maxplayers'] = st.checkbox("Max Players", value=st.session_state.settings['csv_maxplayers'], key='csv_max')
    with col2:
        st.session_state.settings['csv_gtalens'] = st.checkbox("GTALens Link", value=st.session_state.settings['csv_gtalens'], key='csv_lens')
        st.session_state.settings['csv_jobimage'] = st.checkbox("Job Image URL", value=st.session_state.settings['csv_jobimage'], key='csv_img')
        st.session_state.settings['csv_jobdescription'] = st.checkbox("Job Description", value=st.session_state.settings['csv_jobdescription'], key='csv_desc')
        st.session_state.settings['csv_creationdate'] = st.checkbox("Creation Date", value=st.session_state.settings['csv_creationdate'], key='csv_create')
        st.session_state.settings['csv_lastupdated'] = st.checkbox("Last Updated", value=st.session_state.settings['csv_lastupdated'], key='csv_update')
    
    st.session_state.settings['csv_use_custom'] = st.checkbox("Use Custom CSV Column", value=st.session_state.settings['csv_use_custom'], key='csv_custom_check')
    if st.session_state.settings['csv_use_custom']:
        st.session_state.settings['csv_custom'] = st.text_input("Custom CSV Text (repeated for each job)", value=st.session_state.settings['csv_custom'], key='csv_custom_text')
    
    # Auto-generate output with copy button
    csv_output = generate_csv(st.session_state['scraped_jobs'], st.session_state.settings)
    display_code_with_copy_button(csv_output, "CSV", "csv")

# Main app
def main():
    """Main application function"""
    # Initialize session state
    initialize_session_state()
    
    # Title and description
    st.title("🎮 Rockstar Social Club Job Scraper")
    st.markdown("""
    This tool scrapes job information from Rockstar Social Club URLs and displays them in an organized format.
    Perfect for sharing jobs on forums, Discord, YouTube, and more!
    """)
    
    st.markdown("---")
    
    # Single Input Section at the top
    st.header("🔍 Input URLs")
    st.markdown("**Paste individual job URLs or playlist URLs:**")
    input_text = st.text_area(
        "Accepts both individual job URLs and playlist URLs",
        height=150,
        placeholder="https://socialclub.rockstargames.com/job/gtav/xyz123\nhttps://socialclub.rockstargames.com/games/gtav/your-playlist-url"
    )

    # Process button
    if st.button("🔎 Extract & Scrape Jobs", type="primary", use_container_width=True):
        if input_text:
            job_urls, playlist_urls = validate_and_clean_urls(input_text)
            
            all_job_urls = job_urls.copy()
            
            # If there are playlist URLs, extract jobs from them
            if playlist_urls:
                st.info(f"📄 Found {len(playlist_urls)} playlist(s). Extracting jobs...")
                
                driver = None
                try:
                    driver = setup_driver()
                    
                    for i, playlist_url in enumerate(playlist_urls, 1):
                        st.text(f"Extracting playlist {i}/{len(playlist_urls)}...")
                        extracted_jobs = extract_playlist_jobs(driver, playlist_url)
                        
                        if extracted_jobs:
                            st.success(f"✅ Extracted {len(extracted_jobs)} jobs from playlist {i}")
                            all_job_urls.extend(extracted_jobs)
                        else:
                            st.warning(f"⚠️ No jobs found in playlist {i}")
                
                finally:
                    if driver:
                        try:
                            driver.quit()
                        except:
                            pass
                
                # Remove duplicates from combined list
                seen = set()
                unique_all_urls = []
                for url in all_job_urls:
                    if url not in seen:
                        seen.add(url)
                        unique_all_urls.append(url)
                all_job_urls = unique_all_urls
            
            if all_job_urls:
                # Check for limits
                if len(all_job_urls) >= 17:
                    st.warning(f"⚠️ **Please use this tool responsibly!** You're about to scrape {len(all_job_urls)} jobs. Consider whether you need all of them.")
                
                if len(all_job_urls) > 50:
                    st.error(f"❌ **Hard limit exceeded!** You're trying to scrape {len(all_job_urls)} jobs, but the limit is 50 jobs at once. Please reduce the number of URLs.")
                    st.stop()
                
                st.success(f"✅ Found {len(all_job_urls)} valid job URL(s)")
                
                with st.expander("📋 Extracted Job URLs", expanded=True):
                    for i, url in enumerate(all_job_urls, 1):
                        st.text(f"{i}. {url}")
                
                st.info("🔄 Scraping job data... This may take a moment.")
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                scraped_jobs = scrape_multiple_jobs(all_job_urls, progress_bar, status_text)
                
                progress_bar.empty()
                status_text.empty()
                
                st.session_state['scraped_jobs'] = scraped_jobs
                
                st.success(f"✅ Scraped {len(scraped_jobs)} job(s)!")
                st.rerun()
            else:
                st.error("❌ No valid Rockstar Social Club URLs found in the input.")
        else:
            st.warning("⚠️ Please enter some URLs first.")
    
    st.markdown("---")
    
    # Three tabs underneath: Export Format, Table View, Card View
    if 'scraped_jobs' in st.session_state and st.session_state['scraped_jobs']:
        main_tabs = st.tabs(["📤 Export Formats", "📊 Table View", "🎴 Card View"])
        
        # TAB 1: Export Formats
        with main_tabs[0]:
            st.header("Export Formats")
            
            # Settings management
            st.markdown("**Manage Settings:**")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("↻ Reset to Default", key="reset_settings_export", use_container_width=True):
                    reset_settings_to_default()
            
            with col2:
                settings_json = export_settings()
                st.download_button(
                    label="💾 Export Settings",
                    data=settings_json,
                    file_name="rockstar_scraper_settings.json",
                    mime="application/json",
                    help="Download settings as backup",
                    use_container_width=True
                )
            
            with col3:
                uploaded_settings = st.file_uploader(
                    "📂 Import Settings", 
                    type=['json'], 
                    help="Load settings from file",
                    label_visibility="collapsed"
                )
                if uploaded_settings is not None:
                    import_settings(uploaded_settings)
            
            st.info("💡 **Tip:** Your settings automatically persist during your current session. Use Export/Import to save them permanently.")
            
            st.markdown("---")
            
            # Export format sub-tabs
            export_tabs = st.tabs(["BBCode", "Markdown", "YouTube", "Text", "CSV"])
            
            with export_tabs[0]:
                display_bbcode_settings()
            
            with export_tabs[1]:
                display_markdown_settings()
            
            with export_tabs[2]:
                display_youtube_settings()
            
            with export_tabs[3]:
                display_text_settings()
            
            with export_tabs[4]:
                display_csv_settings()
        
        # TAB 2: Table View
        with main_tabs[1]:
            st.header("📊 Table View")
            display_table_view(st.session_state['scraped_jobs'])
        
        # TAB 3: Card View
        with main_tabs[2]:
            st.header("🎴 Card View")
            display_card_view(st.session_state['scraped_jobs'])
    
    else:
        st.info("👆 Please scrape some jobs first using the input section above")
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666;'>
        Made for the GTA Creator & Playlist Community | Scrapes data from Rockstar Social Club<br>
        <small>💡 Settings automatically persist during your session. Export them to save permanently!</small>
        </div>
        """,
        unsafe_allow_html=True
    )

# Run the app
if __name__ == "__main__":
    main()