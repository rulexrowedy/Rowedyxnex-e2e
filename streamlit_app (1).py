import streamlit as st
import time
import threading
import uuid
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import database as db

st.set_page_config(
    page_title="FB Multi-Session Manager",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed"
)

custom_css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');
    
    * {
        font-family: 'Poppins', sans-serif;
    }
    
    .stApp {
        background-image: url('https://i.ibb.co/7t2b2TpC/1751604019030.jpg');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }
    
    .main-header {
        background: rgba(0, 0, 0, 0.6);
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 1.5rem;
        backdrop-filter: blur(10px);
    }
    
    .main-header h1 {
        color: white;
        font-size: 2rem;
        font-weight: 700;
        margin: 0;
    }
    
    .main-header p {
        color: rgba(255,255,255,0.8);
        font-size: 1rem;
        margin-top: 0.3rem;
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1.5rem;
        font-weight: 600;
        font-size: 0.9rem;
    }
    
    .stButton>button:hover {
        opacity: 0.9;
    }
    
    .config-box {
        background: rgba(0, 0, 0, 0.6);
        padding: 1.5rem;
        border-radius: 10px;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.1);
    }
    
    .task-card {
        background: rgba(30, 30, 30, 0.8);
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 0.8rem;
        border: 1px solid rgba(255,255,255,0.1);
    }
    
    .task-id {
        color: #667eea;
        font-weight: 700;
        font-size: 0.8rem;
        text-transform: uppercase;
    }
    
    .status-running {
        color: #00ff00;
        font-weight: 600;
    }
    
    .status-inactive {
        color: #ff6b6b;
        font-weight: 600;
    }
    
    .log-container {
        background: rgba(0, 0, 0, 0.9);
        color: #00ff00;
        padding: 1rem;
        border-radius: 8px;
        font-family: 'Courier New', monospace;
        font-size: 12px;
        max-height: 200px;
        overflow-y: auto;
        line-height: 1.5;
    }
    
    .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stNumberInput>div>div>input {
        background: rgba(255, 255, 255, 0.15) !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
        border-radius: 6px !important;
        color: white !important;
    }
    
    .stTextInput>div>div>input::placeholder, .stTextArea>div>div>textarea::placeholder {
        color: rgba(255,255,255,0.5) !important;
    }
    
    label {
        color: white !important;
    }
    
    .footer {
        text-align: center;
        padding: 1rem;
        color: rgba(255,255,255,0.7);
        font-size: 0.8rem;
        margin-top: 2rem;
    }
</style>
"""

st.markdown(custom_css, unsafe_allow_html=True)

if 'tasks' not in st.session_state:
    st.session_state.tasks = {}
if 'task_counter' not in st.session_state:
    st.session_state.task_counter = 0
if 'expanded_console' not in st.session_state:
    st.session_state.expanded_console = None

class TaskState:
    def __init__(self, task_id):
        self.task_id = task_id
        self.running = False
        self.message_count = 0
        self.logs = []
        self.message_rotation_index = 0
        self.thread = None
        self.config = {}

def generate_task_id():
    st.session_state.task_counter += 1
    return f"AUTO-{st.session_state.task_counter}"

def log_message(msg, task_state):
    timestamp = time.strftime("%H:%M:%S")
    formatted_msg = f"[{timestamp}] {msg}"
    task_state.logs.append(formatted_msg)
    if len(task_state.logs) > 500:
        task_state.logs = task_state.logs[-500:]

def find_message_input(driver, task_id, task_state):
    log_message(f'{task_id}: Finding message input...', task_state)
    time.sleep(10)
    
    try:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)
    except Exception:
        pass
    
    try:
        page_title = driver.title
        page_url = driver.current_url
        log_message(f'{task_id}: Page Title: {page_title}', task_state)
        log_message(f'{task_id}: Page URL: {page_url}', task_state)
    except Exception as e:
        log_message(f'{task_id}: Could not get page info: {e}', task_state)
    
    message_input_selectors = [
        'div[contenteditable="true"][role="textbox"]',
        'div[contenteditable="true"][data-lexical-editor="true"]',
        'div[aria-label*="message" i][contenteditable="true"]',
        'div[aria-label*="Message" i][contenteditable="true"]',
        'div[contenteditable="true"][spellcheck="true"]',
        '[role="textbox"][contenteditable="true"]',
        'textarea[placeholder*="message" i]',
        'div[aria-placeholder*="message" i]',
        'div[data-placeholder*="message" i]',
        '[contenteditable="true"]',
        'textarea',
        'input[type="text"]'
    ]
    
    log_message(f'{task_id}: Trying {len(message_input_selectors)} selectors...', task_state)
    
    for idx, selector in enumerate(message_input_selectors):
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            log_message(f'{task_id}: Selector {idx+1}/{len(message_input_selectors)} "{selector[:50]}..." found {len(elements)} elements', task_state)
            
            for element in elements:
                try:
                    is_editable = driver.execute_script("""
                        return arguments[0].contentEditable === 'true' || 
                               arguments[0].tagName === 'TEXTAREA' || 
                               arguments[0].tagName === 'INPUT';
                    """, element)
                    
                    if is_editable:
                        log_message(f'{task_id}: Found editable element with selector #{idx+1}', task_state)
                        
                        try:
                            element.click()
                            time.sleep(0.5)
                        except:
                            pass
                        
                        element_text = driver.execute_script("return arguments[0].placeholder || arguments[0].getAttribute('aria-label') || arguments[0].getAttribute('aria-placeholder') || '';", element).lower()
                        
                        keywords = ['message', 'write', 'type', 'send', 'chat', 'msg', 'reply', 'text', 'aa']
                        if any(keyword in element_text for keyword in keywords):
                            log_message(f'{task_id}: Found message input with text: {element_text[:50]}', task_state)
                            return element
                        elif idx < 10:
                            log_message(f'{task_id}: Using primary selector editable element (#{idx+1})', task_state)
                            return element
                        elif selector == '[contenteditable="true"]' or selector == 'textarea' or selector == 'input[type="text"]':
                            log_message(f'{task_id}: Using fallback editable element', task_state)
                            return element
                except Exception as e:
                    log_message(f'{task_id}: Element check failed: {str(e)[:50]}', task_state)
                    continue
        except Exception as e:
            continue
    
    try:
        page_source = driver.page_source
        log_message(f'{task_id}: Page source length: {len(page_source)} characters', task_state)
        if 'contenteditable' in page_source.lower():
            log_message(f'{task_id}: Page contains contenteditable elements', task_state)
        else:
            log_message(f'{task_id}: No contenteditable elements found in page', task_state)
    except Exception:
        pass
    
    return None

def setup_browser(task_state):
    log_message('Setting up Chrome browser...', task_state)
    
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-setuid-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36')
    
    chromium_paths = [
        '/usr/bin/chromium',
        '/usr/bin/chromium-browser',
        '/usr/bin/google-chrome',
        '/usr/bin/chrome'
    ]
    
    for chromium_path in chromium_paths:
        if Path(chromium_path).exists():
            chrome_options.binary_location = chromium_path
            log_message(f'Found Chromium at: {chromium_path}', task_state)
            break
    
    chromedriver_paths = [
        '/usr/bin/chromedriver',
        '/usr/local/bin/chromedriver'
    ]
    
    driver_path = None
    for driver_candidate in chromedriver_paths:
        if Path(driver_candidate).exists():
            driver_path = driver_candidate
            log_message(f'Found ChromeDriver at: {driver_path}', task_state)
            break
    
    try:
        from selenium.webdriver.chrome.service import Service
        
        if driver_path:
            service = Service(executable_path=driver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)
            log_message('Chrome started with detected ChromeDriver!', task_state)
        else:
            driver = webdriver.Chrome(options=chrome_options)
            log_message('Chrome started with default driver!', task_state)
        
        driver.set_window_size(1920, 1080)
        log_message('Chrome browser setup completed successfully!', task_state)
        return driver
    except Exception as error:
        log_message(f'Browser setup failed: {error}', task_state)
        raise error

def get_next_message(messages, task_state):
    if not messages or len(messages) == 0:
        return 'Hello!'
    
    message = messages[task_state.message_rotation_index % len(messages)]
    task_state.message_rotation_index += 1
    
    return message

def send_messages(config, task_state):
    driver = None
    task_id = task_state.task_id
    try:
        log_message(f'{task_id}: Starting automation...', task_state)
        driver = setup_browser(task_state)
        
        log_message(f'{task_id}: Navigating to Facebook...', task_state)
        driver.get('https://www.facebook.com/')
        time.sleep(8)
        
        if config['cookies'] and config['cookies'].strip():
            log_message(f'{task_id}: Adding cookies...', task_state)
            cookie_array = config['cookies'].split(';')
            for cookie in cookie_array:
                cookie_trimmed = cookie.strip()
                if cookie_trimmed:
                    first_equal_index = cookie_trimmed.find('=')
                    if first_equal_index > 0:
                        name = cookie_trimmed[:first_equal_index].strip()
                        value = cookie_trimmed[first_equal_index + 1:].strip()
                        try:
                            driver.add_cookie({
                                'name': name,
                                'value': value,
                                'domain': '.facebook.com',
                                'path': '/'
                            })
                        except Exception as e:
                            log_message(f'{task_id}: Cookie error: {str(e)[:50]}', task_state)
            
            log_message(f'{task_id}: Refreshing page with cookies...', task_state)
            driver.refresh()
            time.sleep(8)
        
        chat_url = f"https://www.facebook.com/messages/t/{config['chat_id']}"
        log_message(f'{task_id}: Navigating to chat: {chat_url}', task_state)
        driver.get(chat_url)
        time.sleep(10)
        
        messages_list = [m.strip() for m in config['messages'].split('\n') if m.strip()]
        delay = config['delay']
        name_prefix = config['name_prefix']
        
        log_message(f'{task_id}: Messages loaded: {len(messages_list)}', task_state)
        log_message(f'{task_id}: Delay: {delay} seconds', task_state)
        log_message(f'{task_id}: Name prefix: {name_prefix}', task_state)
        
        message_input = find_message_input(driver, task_id, task_state)
        
        if not message_input:
            log_message(f'{task_id}: Could not find message input!', task_state)
            task_state.running = False
            return
        
        log_message(f'{task_id}: Message input found! Starting message loop...', task_state)
        
        while task_state.running:
            try:
                message = get_next_message(messages_list, task_state)
                full_message = f"{name_prefix} {message}" if name_prefix else message
                
                try:
                    message_input.click()
                    time.sleep(0.5)
                except:
                    message_input = find_message_input(driver, task_id, task_state)
                    if message_input:
                        message_input.click()
                        time.sleep(0.5)
                    else:
                        log_message(f'{task_id}: Lost message input, retrying...', task_state)
                        time.sleep(5)
                        continue
                
                driver.execute_script("""
                    arguments[0].focus();
                    arguments[0].innerHTML = '';
                """, message_input)
                time.sleep(0.3)
                
                message_input.send_keys(full_message)
                time.sleep(0.5)
                
                message_input.send_keys(Keys.ENTER)
                
                task_state.message_count += 1
                log_message(f'{task_id}: Sent message #{task_state.message_count}: {full_message[:50]}...', task_state)
                
                log_message(f'{task_id}: Waiting {delay} seconds...', task_state)
                
                for i in range(delay):
                    if not task_state.running:
                        break
                    time.sleep(1)
                
            except Exception as e:
                log_message(f'{task_id}: Error sending message: {str(e)[:100]}', task_state)
                time.sleep(5)
                
                message_input = find_message_input(driver, task_id, task_state)
                if not message_input:
                    log_message(f'{task_id}: Could not recover message input, stopping...', task_state)
                    break
        
        log_message(f'{task_id}: Automation stopped.', task_state)
        
    except Exception as e:
        log_message(f'{task_id}: Fatal error: {str(e)}', task_state)
    finally:
        if driver:
            try:
                driver.quit()
                log_message(f'{task_id}: Browser closed.', task_state)
            except:
                pass
        task_state.running = False

def start_task(config):
    task_id = generate_task_id()
    task_state = TaskState(task_id)
    task_state.config = config.copy()
    task_state.running = True
    
    thread = threading.Thread(target=send_messages, args=(config, task_state), daemon=True)
    task_state.thread = thread
    
    st.session_state.tasks[task_id] = task_state
    thread.start()
    
    return task_id

def stop_task(task_id):
    if task_id in st.session_state.tasks:
        st.session_state.tasks[task_id].running = False

def remove_task(task_id):
    if task_id in st.session_state.tasks:
        task = st.session_state.tasks[task_id]
        if not task.running:
            del st.session_state.tasks[task_id]
            if st.session_state.expanded_console == task_id:
                st.session_state.expanded_console = None

st.markdown("""
<div class="main-header">
    <h1>FB Multi-Session Manager</h1>
    <p>Manage multiple automation sessions simultaneously</p>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="config-box">', unsafe_allow_html=True)
st.subheader("New Session Configuration")

col1, col2 = st.columns(2)

with col1:
    chat_id = st.text_input("Chat ID", placeholder="Enter Facebook chat/group ID")
    name_prefix = st.text_input("Name Prefix", placeholder="Optional prefix for messages")

with col2:
    delay = st.number_input("Delay (seconds)", min_value=5, max_value=300, value=30)

cookies = st.text_area("Cookies", placeholder="Paste your Facebook cookies here (format: name=value; name2=value2)", height=80)
messages = st.text_area("Messages (one per line)", placeholder="Enter messages, one per line. They will rotate.", height=100)

col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 3])

with col_btn1:
    if st.button("Start New Session", type="primary"):
        if chat_id and cookies:
            config = {
                'chat_id': chat_id,
                'name_prefix': name_prefix,
                'delay': delay,
                'cookies': cookies,
                'messages': messages
            }
            task_id = start_task(config)
            st.success(f"Session {task_id} started!")
            st.rerun()
        else:
            st.error("Chat ID and Cookies are required!")

with col_btn2:
    if st.button("Clear Form"):
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")
st.subheader("Active Sessions")

if not st.session_state.tasks:
    st.info("No active sessions. Start a new session above.")
else:
    for task_id, task_state in list(st.session_state.tasks.items()):
        with st.container():
            st.markdown(f'<div class="task-card">', unsafe_allow_html=True)
            
            col_id, col_status, col_count, col_actions = st.columns([2, 2, 2, 4])
            
            with col_id:
                st.markdown(f'<span class="task-id">{task_id}</span>', unsafe_allow_html=True)
            
            with col_status:
                if task_state.running:
                    st.markdown('<span class="status-running">Running</span>', unsafe_allow_html=True)
                else:
                    st.markdown('<span class="status-inactive">Inactive</span>', unsafe_allow_html=True)
            
            with col_count:
                st.write(f"Messages: {task_state.message_count}")
            
            with col_actions:
                btn_col1, btn_col2, btn_col3 = st.columns(3)
                
                with btn_col1:
                    if st.button("Console", key=f"console_{task_id}"):
                        if st.session_state.expanded_console == task_id:
                            st.session_state.expanded_console = None
                        else:
                            st.session_state.expanded_console = task_id
                        st.rerun()
                
                with btn_col2:
                    if task_state.running:
                        if st.button("Stop", key=f"stop_{task_id}"):
                            stop_task(task_id)
                            st.rerun()
                
                with btn_col3:
                    if not task_state.running:
                        if st.button("Remove", key=f"remove_{task_id}"):
                            remove_task(task_id)
                            st.rerun()
            
            if st.session_state.expanded_console == task_id:
                st.markdown('<div class="log-container">', unsafe_allow_html=True)
                if task_state.logs:
                    logs_text = "<br>".join(task_state.logs[-100:])
                    st.markdown(logs_text, unsafe_allow_html=True)
                else:
                    st.write("No logs yet...")
                st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.tasks:
    time.sleep(2)
    st.rerun()

st.markdown("""
<div class="footer">
    FB Multi-Session Manager | Server Always Active
</div>
""", unsafe_allow_html=True)
