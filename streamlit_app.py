import streamlit as st
import time
import threading
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

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
        background-repeat: no-repeat;
    }
    
    .main-header {
        background: rgba(0, 0, 0, 0.7);
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 1.5rem;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.1);
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
        background: rgba(0, 0, 0, 0.7);
        padding: 1.5rem;
        border-radius: 10px;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.1);
        margin-bottom: 1rem;
    }
    
    .task-card {
        background: rgba(30, 30, 30, 0.85);
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 0.8rem;
        border: 1px solid rgba(255,255,255,0.15);
    }
    
    .task-id-badge {
        color: #667eea;
        font-weight: 700;
        font-size: 0.85rem;
        text-transform: uppercase;
        background: rgba(102, 126, 234, 0.2);
        padding: 4px 10px;
        border-radius: 4px;
        display: inline-block;
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
        background: rgba(0, 0, 0, 0.95);
        color: #00ff00;
        padding: 1rem;
        border-radius: 8px;
        font-family: 'Courier New', monospace;
        font-size: 11px;
        max-height: 250px;
        overflow-y: auto;
        line-height: 1.4;
        border: 1px solid rgba(0, 255, 0, 0.2);
    }
    
    .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stNumberInput>div>div>input {
        background: rgba(255, 255, 255, 0.15) !important;
        border: 1px solid rgba(255,255,255,0.25) !important;
        border-radius: 6px !important;
        color: white !important;
    }
    
    .stTextInput>div>div>input::placeholder, .stTextArea>div>div>textarea::placeholder {
        color: rgba(255,255,255,0.5) !important;
    }
    
    label, .stMarkdown p, h1, h2, h3, h4, h5, h6 {
        color: white !important;
    }
    
    .stFileUploader {
        background: rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px;
        padding: 10px;
    }
    
    .profile-info {
        background: rgba(102, 126, 234, 0.3);
        padding: 10px 15px;
        border-radius: 8px;
        color: white;
        border-left: 4px solid #667eea;
        margin: 10px 0;
    }
    
    .footer {
        text-align: center;
        padding: 1rem;
        color: rgba(255,255,255,0.6);
        font-size: 0.8rem;
        margin-top: 2rem;
    }
    
    div[data-testid="stExpander"] {
        background: rgba(0, 0, 0, 0.5);
        border-radius: 8px;
        border: 1px solid rgba(255,255,255,0.1);
    }
    
    .element-container {
        color: white;
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
        self.profile_name = None
        self.profile_id = None

def generate_task_id():
    st.session_state.task_counter += 1
    return f"AUTO-{st.session_state.task_counter}"

def log_message(msg, task_state=None):
    timestamp = time.strftime("%H:%M:%S")
    formatted_msg = f"[{timestamp}] {msg}"
    if task_state:
        task_state.logs.append(formatted_msg)
        if len(task_state.logs) > 500:
            task_state.logs = task_state.logs[-500:]

def find_message_input(driver, process_id, task_state=None):
    log_message(f'{process_id}: Finding message input...', task_state)
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
        log_message(f'{process_id}: Page Title: {page_title}', task_state)
        log_message(f'{process_id}: Page URL: {page_url}', task_state)
    except Exception as e:
        log_message(f'{process_id}: Could not get page info: {e}', task_state)
    
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
    
    log_message(f'{process_id}: Trying {len(message_input_selectors)} selectors...', task_state)
    
    for idx, selector in enumerate(message_input_selectors):
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            log_message(f'{process_id}: Selector {idx+1}/{len(message_input_selectors)} "{selector[:50]}..." found {len(elements)} elements', task_state)
            
            for element in elements:
                try:
                    is_editable = driver.execute_script("""
                        return arguments[0].contentEditable === 'true' || 
                               arguments[0].tagName === 'TEXTAREA' || 
                               arguments[0].tagName === 'INPUT';
                    """, element)
                    
                    if is_editable:
                        log_message(f'{process_id}: Found editable element with selector #{idx+1}', task_state)
                        
                        try:
                            element.click()
                            time.sleep(0.5)
                        except:
                            pass
                        
                        element_text = driver.execute_script("return arguments[0].placeholder || arguments[0].getAttribute('aria-label') || arguments[0].getAttribute('aria-placeholder') || '';", element).lower()
                        
                        keywords = ['message', 'write', 'type', 'send', 'chat', 'msg', 'reply', 'text', 'aa']
                        if any(keyword in element_text for keyword in keywords):
                            log_message(f'{process_id}: Found message input with text: {element_text[:50]}', task_state)
                            return element
                        elif idx < 10:
                            log_message(f'{process_id}: Using primary selector editable element (#{idx+1})', task_state)
                            return element
                        elif selector == '[contenteditable="true"]' or selector == 'textarea' or selector == 'input[type="text"]':
                            log_message(f'{process_id}: Using fallback editable element', task_state)
                            return element
                except Exception as e:
                    log_message(f'{process_id}: Element check failed: {str(e)[:50]}', task_state)
                    continue
        except Exception as e:
            continue
    
    try:
        page_source = driver.page_source
        log_message(f'{process_id}: Page source length: {len(page_source)} characters', task_state)
        if 'contenteditable' in page_source.lower():
            log_message(f'{process_id}: Page contains contenteditable elements', task_state)
        else:
            log_message(f'{process_id}: No contenteditable elements found in page', task_state)
    except Exception:
        pass
    
    return None

def setup_browser(task_state=None):
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

def get_next_message(messages, task_state=None):
    if not messages or len(messages) == 0:
        return 'Hello!'
    
    if task_state:
        message = messages[task_state.message_rotation_index % len(messages)]
        task_state.message_rotation_index += 1
    else:
        message = messages[0]
    
    return message

def fetch_profile_info(driver, task_id, task_state):
    try:
        log_message(f'{task_id}: Fetching Facebook profile info...', task_state)
        
        driver.get('https://www.facebook.com/me')
        time.sleep(5)
        
        profile_name = None
        profile_id = None
        
        try:
            current_url = driver.current_url
            log_message(f'{task_id}: Profile URL: {current_url}', task_state)
            if '/profile.php?id=' in current_url:
                profile_id = current_url.split('id=')[1].split('&')[0]
            elif 'facebook.com/' in current_url:
                parts = current_url.split('facebook.com/')[-1].split('?')[0].split('/')[0]
                if parts and parts != 'me':
                    profile_id = parts
        except:
            pass
        
        try:
            name_selectors = ['h1', 'span.x1lliihq', 'div[role="main"] h1']
            for sel in name_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, sel)
                    for el in elements:
                        text = el.text.strip()
                        if text and len(text) > 1 and len(text) < 100:
                            profile_name = text
                            break
                    if profile_name:
                        break
                except:
                    continue
        except:
            pass
        
        if not profile_name:
            try:
                profile_name = driver.title.replace(' | Facebook', '').replace(' - Facebook', '').strip()
            except:
                pass
        
        if profile_name:
            task_state.profile_name = profile_name
            log_message(f'{task_id}: Profile Name: {profile_name}', task_state)
        
        if profile_id:
            task_state.profile_id = profile_id
            log_message(f'{task_id}: Profile ID: {profile_id}', task_state)
        
        if profile_name or profile_id:
            log_message(f'{task_id}: Logged in as: {profile_name or profile_id}', task_state)
            return True
        else:
            log_message(f'{task_id}: Could not fetch profile - cookies may be invalid', task_state)
            return False
            
    except Exception as e:
        log_message(f'{task_id}: Error fetching profile: {str(e)[:50]}', task_state)
        return False

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
                        except Exception:
                            pass
            
            log_message(f'{task_id}: Cookies added, refreshing...', task_state)
            driver.refresh()
            time.sleep(5)
            
            fetch_profile_info(driver, task_id, task_state)
        
        if config['chat_id']:
            chat_id = config['chat_id'].strip()
            log_message(f'{task_id}: Opening conversation {chat_id}...', task_state)
            driver.get(f'https://www.facebook.com/messages/t/{chat_id}')
        else:
            log_message(f'{task_id}: Opening messages...', task_state)
            driver.get('https://www.facebook.com/messages')
        
        time.sleep(15)
        
        message_input = find_message_input(driver, task_id, task_state)
        
        if not message_input:
            log_message(f'{task_id}: Message input not found!', task_state)
            task_state.running = False
            return 0
        
        delay = int(config['delay'])
        messages_sent = 0
        
        messages_list = config.get('messages_list', [])
        if not messages_list:
            messages_list = [msg.strip() for msg in config['messages'].split('\n') if msg.strip()]
        
        if not messages_list:
            messages_list = ['Hello!']
        
        log_message(f'{task_id}: Loaded {len(messages_list)} messages', task_state)
        log_message(f'{task_id}: Delay: {delay} seconds', task_state)
        
        while task_state.running:
            base_message = get_next_message(messages_list, task_state)
            
            if config['name_prefix']:
                message_to_send = f"{config['name_prefix']} {base_message}"
            else:
                message_to_send = base_message
            
            try:
                driver.execute_script("""
                    const element = arguments[0];
                    const message = arguments[1];
                    
                    element.scrollIntoView({behavior: 'smooth', block: 'center'});
                    element.focus();
                    element.click();
                    
                    if (element.tagName === 'DIV') {
                        element.textContent = message;
                        element.innerHTML = message;
                    } else {
                        element.value = message;
                    }
                    
                    element.dispatchEvent(new Event('input', { bubbles: true }));
                    element.dispatchEvent(new Event('change', { bubbles: true }));
                    element.dispatchEvent(new InputEvent('input', { bubbles: true, data: message }));
                """, message_input, message_to_send)
                
                time.sleep(1)
                
                sent = driver.execute_script("""
                    const sendButtons = document.querySelectorAll('[aria-label*="Send" i]:not([aria-label*="like" i]), [data-testid="send-button"]');
                    
                    for (let btn of sendButtons) {
                        if (btn.offsetParent !== null) {
                            btn.click();
                            return 'button_clicked';
                        }
                    }
                    return 'button_not_found';
                """)
                
                if sent == 'button_not_found':
                    log_message(f'{task_id}: Send button not found, using Enter key...', task_state)
                    driver.execute_script("""
                        const element = arguments[0];
                        element.focus();
                        
                        const events = [
                            new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }),
                            new KeyboardEvent('keypress', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }),
                            new KeyboardEvent('keyup', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true })
                        ];
                        
                        events.forEach(event => element.dispatchEvent(event));
                    """, message_input)
                else:
                    log_message(f'{task_id}: Send button clicked', task_state)
                
                time.sleep(1)
                
                messages_sent += 1
                task_state.message_count = messages_sent
                log_message(f'{task_id}: Message {messages_sent} sent: {message_to_send[:30]}...', task_state)
                
                time.sleep(delay)
                
            except Exception as e:
                log_message(f'{task_id}: Error sending message: {str(e)}', task_state)
                break
        
        log_message(f'{task_id}: Automation stopped! Total messages sent: {messages_sent}', task_state)
        task_state.running = False
        return messages_sent
        
    except Exception as e:
        log_message(f'{task_id}: Fatal error: {str(e)}', task_state)
        task_state.running = False
        return 0
    finally:
        if driver:
            try:
                driver.quit()
                log_message(f'{task_id}: Browser closed', task_state)
            except:
                pass

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
    name_prefix = st.text_input("Name Prefix (Optional)", placeholder="Prefix before each message")

with col2:
    delay = st.number_input("Delay (seconds)", min_value=1, max_value=300, value=30)

cookies = st.text_area("Cookies", placeholder="Paste your Facebook cookies here", height=80)

st.markdown("#### Messages")
message_option = st.radio("Message Source:", ["Upload TXT File", "Type Messages"], horizontal=True, label_visibility="collapsed")

messages_list = []
messages_text = ""

if message_option == "Upload TXT File":
    uploaded_file = st.file_uploader("Upload messages.txt file (one message per line)", type=['txt'])
    if uploaded_file is not None:
        try:
            content = uploaded_file.read().decode('utf-8')
            messages_list = [m.strip() for m in content.split('\n') if m.strip()]
            messages_text = content
            st.success(f"Loaded {len(messages_list)} messages from file")
            with st.expander("Preview Messages"):
                for i, msg in enumerate(messages_list[:10], 1):
                    st.text(f"{i}. {msg[:50]}...")
                if len(messages_list) > 10:
                    st.text(f"... and {len(messages_list) - 10} more")
        except Exception as e:
            st.error(f"Error reading file: {e}")
else:
    messages_text = st.text_area("Messages (one per line)", placeholder="Enter messages, one per line", height=100)
    if messages_text:
        messages_list = [m.strip() for m in messages_text.split('\n') if m.strip()]

st.markdown('</div>', unsafe_allow_html=True)

col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 3])

with col_btn1:
    if st.button("Start New Session", type="primary", use_container_width=True):
        if chat_id and cookies:
            if not messages_list:
                st.error("Please add messages!")
            else:
                config = {
                    'chat_id': chat_id.strip(),
                    'name_prefix': name_prefix.strip(),
                    'delay': delay,
                    'cookies': cookies.strip(),
                    'messages': messages_text,
                    'messages_list': messages_list
                }
                task_id = start_task(config)
                st.success(f"Session {task_id} started!")
                time.sleep(0.5)
                st.rerun()
        else:
            st.error("Chat ID and Cookies are required!")

with col_btn2:
    if st.button("Clear Form", use_container_width=True):
        st.rerun()

st.markdown("---")
st.subheader("Active Sessions")

if not st.session_state.tasks:
    st.info("No active sessions. Configure and start a new session above.")
else:
    for task_id, task_state in list(st.session_state.tasks.items()):
        st.markdown(f'<div class="task-card">', unsafe_allow_html=True)
        
        col_id, col_profile, col_status, col_count, col_actions = st.columns([1.5, 2, 1.5, 1.5, 3])
        
        with col_id:
            st.markdown(f'<span class="task-id-badge">{task_id}</span>', unsafe_allow_html=True)
        
        with col_profile:
            if task_state.profile_name:
                st.markdown(f'<div class="profile-info">{task_state.profile_name}</div>', unsafe_allow_html=True)
            elif task_state.profile_id:
                st.markdown(f'<div class="profile-info">ID: {task_state.profile_id}</div>', unsafe_allow_html=True)
            else:
                st.write("Connecting...")
        
        with col_status:
            if task_state.running:
                st.markdown('<span class="status-running">Running</span>', unsafe_allow_html=True)
            else:
                st.markdown('<span class="status-inactive">Stopped</span>', unsafe_allow_html=True)
        
        with col_count:
            st.write(f"Sent: {task_state.message_count}")
        
        with col_actions:
            btn_col1, btn_col2, btn_col3 = st.columns(3)
            
            with btn_col1:
                if st.button("Console", key=f"console_{task_id}", use_container_width=True):
                    if st.session_state.expanded_console == task_id:
                        st.session_state.expanded_console = None
                    else:
                        st.session_state.expanded_console = task_id
                    st.rerun()
            
            with btn_col2:
                if task_state.running:
                    if st.button("Stop", key=f"stop_{task_id}", use_container_width=True):
                        stop_task(task_id)
                        st.rerun()
                else:
                    st.button("Stop", key=f"stop_{task_id}", disabled=True, use_container_width=True)
            
            with btn_col3:
                if not task_state.running:
                    if st.button("Remove", key=f"remove_{task_id}", use_container_width=True):
                        remove_task(task_id)
                        st.rerun()
                else:
                    st.button("Remove", key=f"remove_{task_id}", disabled=True, use_container_width=True)
        
        if st.session_state.expanded_console == task_id:
            st.markdown('<div class="log-container">', unsafe_allow_html=True)
            if task_state.logs:
                logs_html = "<br>".join(task_state.logs[-100:])
                st.markdown(logs_html, unsafe_allow_html=True)
            else:
                st.write("No logs yet...")
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

has_running = any(t.running for t in st.session_state.tasks.values())
if has_running or st.session_state.tasks:
    time.sleep(2)
    st.rerun()

st.markdown("""
<div class="footer">
    FB Multi-Session Manager | Server Always Active
</div>
""", unsafe_allow_html=True)
