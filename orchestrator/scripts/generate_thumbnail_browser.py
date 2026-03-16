#!/usr/bin/env python3
"""
Generate thumbnail via ChatGPT browser automation.

This script is called by the orchestrator during the thumbnail stage.
It opens ChatGPT in the OpenClaw browser, types the prompt, waits for
image generation, downloads the best image, and saves it.

Workflow:
1. Start OpenClaw browser (if not running)
2. Navigate to chatgpt.com
3. Type prompt and wait for response
4. Extract generated images via JS
5. Download the first (best) image
6. Save to output directory

Usage:
    python3 generate_thumbnail_browser.py --title "Title" --subtitle "Sub" [--output path]

If browser fails, exits with code 1 for API fallback.
"""

import argparse
import json
import os
import sys
import subprocess
import time
import base64
import urllib.request

WORKSPACE = os.path.expanduser("~/.openclaw")
OUTPUT_DIR = os.path.join(WORKSPACE, "workspace-orchestrator/outputs")
THUMBNAILS_DIR = os.path.join(WORKSPACE, "workspace-orchestrator/thumbnails")
CDP_URL = "http://127.0.0.1:18800"

PROMPT_TEMPLATE = (
    "Generate a YouTube tech thumbnail image. 16:9 aspect ratio, 1536x1024 resolution. "
    "Dark navy blue background, metallic robotic claw/hand on the left "
    "with blue and cyan neon glow, futuristic holographic elements. "
    "Bold white and cyan text on the right. Professional tech YouTube channel aesthetic. "
    "Render the following text EXACTLY as written — do not modify it:\n\n"
    "Main title: {title}\n"
    "Subtitle: {subtitle}"
)


def cdp_send(ws_url, method, params=None, timeout=5):
    """Send a CDP command via websocket (simplified with curl)."""
    # Use HTTP endpoints instead of websocket for simplicity
    pass


def get_browser_tabs():
    """Get list of open tabs from OpenClaw browser."""
    try:
        result = subprocess.run(
            ["curl", "-s", "--max-time", "3", f"{CDP_URL}/json/list"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout)
    except:
        pass
    return []


def navigate_browser(url):
    """Navigate the browser to a URL using CDP."""
    tabs = get_browser_tabs()
    if not tabs:
        print("   ❌ Browser non attivo", file=sys.stderr)
        return None
    
    # Use the first tab or find a ChatGPT tab
    tab = tabs[0]
    for t in tabs:
        if "chatgpt" in t.get("url", ""):
            tab = t
            break
    
    ws_url = tab.get("webSocketDebuggerUrl", "")
    tab_id = tab.get("id", "")
    
    # Navigate using CDP HTTP endpoint
    nav_url = f"{CDP_URL}/json/activate/{tab_id}"
    subprocess.run(["curl", "-s", "--max-time", "3", nav_url], capture_output=True)
    
    # Use CDP protocol via Python
    try:
        import websocket  # type: ignore
        ws = websocket.create_connection(ws_url, timeout=10)
        
        # Navigate
        ws.send(json.dumps({
            "id": 1,
            "method": "Page.navigate",
            "params": {"url": url}
        }))
        response = ws.recv()
        ws.close()
        
        return tab_id
    except ImportError:
        # Fallback: use JavaScript evaluation via CDP
        print("   ⚠️  websocket module non disponibile", file=sys.stderr)
        return tab_id  # Return tab_id anyway, might already be on correct page
    except Exception as e:
        print(f"   ⚠️  Navigation error: {str(e)[:50]}", file=sys.stderr)
        return tab_id


def inject_and_type_prompt(tab_id, prompt):
    """Inject prompt into ChatGPT input field and submit."""
    try:
        import websocket
        
        tabs = get_browser_tabs()
        ws_url = None
        for t in tabs:
            if t.get("id") == tab_id:
                ws_url = t.get("webSocketDebuggerUrl")
                break
        
        if not ws_url:
            return False
        
        ws = websocket.create_connection(ws_url, timeout=10)
        
        # Type into the input field
        js_code = f"""
        (function() {{
            // Find the contenteditable input
            var input = document.querySelector('#prompt-textarea') || 
                        document.querySelector('[contenteditable="true"]') ||
                        document.querySelector('textarea');
            if (!input) return 'no input found';
            
            // Set text
            if (input.tagName === 'TEXTAREA') {{
                var nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                    window.HTMLTextAreaElement.prototype, 'value').set;
                nativeInputValueSetter.call(input, {json.dumps(prompt)});
                input.dispatchEvent(new Event('input', {{ bubbles: true }}));
            }} else {{
                input.innerText = {json.dumps(prompt)};
                input.dispatchEvent(new Event('input', {{ bubbles: true }}));
            }}
            
            // Find and click submit button
            setTimeout(function() {{
                var btn = document.querySelector('[data-testid="send-button"]') ||
                          document.querySelector('button[aria-label*="Send"]') ||
                          document.querySelector('button[aria-label*="Invia"]');
                if (btn) btn.click();
            }}, 500);
            
            return 'typed';
        }})()
        """
        
        ws.send(json.dumps({
            "id": 2,
            "method": "Runtime.evaluate",
            "params": {"expression": js_code, "returnByValue": True}
        }))
        
        response = json.loads(ws.recv())
        ws.close()
        
        result = response.get("result", {}).get("result", {}).get("value", "")
        return "typed" in str(result)
        
    except Exception as e:
        print(f"   ⚠️  Type error: {str(e)[:50]}", file=sys.stderr)
        return False


def wait_and_extract_images(tab_id, max_wait=180):
    """Wait for image generation and extract image URLs."""
    try:
        import websocket
        
        tabs = get_browser_tabs()
        ws_url = None
        for t in tabs:
            if t.get("id") == tab_id:
                ws_url = t.get("webSocketDebuggerUrl")
                break
        
        if not ws_url:
            return []
        
        ws = websocket.create_connection(ws_url, timeout=15)
        
        # Wait for images to appear
        start_time = time.time()
        while time.time() - start_time < max_wait:
            js_check = """
            (function() {
                var imgs = document.querySelectorAll('img[alt*="generat"]');
                var urls = [];
                imgs.forEach(function(img) {
                    if (img.src && img.src.startsWith('blob:')) {
                        // Convert blob to data URL
                        var canvas = document.createElement('canvas');
                        canvas.width = img.naturalWidth;
                        canvas.height = img.naturalHeight;
                        canvas.getContext('2d').drawImage(img, 0, 0);
                        urls.push(canvas.toDataURL('image/png'));
                    } else if (img.src && img.src.includes('chatgpt.com/backend-api')) {
                        urls.push(img.src);
                    }
                });
                return urls.length > 0 ? urls : 'waiting';
            })()
            """
            
            ws.send(json.dumps({
                "id": 3,
                "method": "Runtime.evaluate",
                "params": {"expression": js_check, "returnByValue": True, "awaitPromise": False}
            }))
            
            response = json.loads(ws.recv())
            result = response.get("result", {}).get("result", {}).get("value", "")
            
            if isinstance(result, list) and len(result) > 0:
                ws.close()
                print(f"   📷 Trovate {len(result)} immagini")
                return result
            
            # Check if still generating
            js_status = """
            (function() {
                var status = document.querySelector('[class*="generating"]') ||
                             document.querySelector('[class*="loading"]');
                return status ? 'generating' : 'idle';
            })()
            """
            
            ws.send(json.dumps({
                "id": 4,
                "method": "Runtime.evaluate",
                "params": {"expression": js_status, "returnByValue": True}
            }))
            
            status_resp = json.loads(ws.recv())
            status = status_resp.get("result", {}).get("result", {}).get("value", "")
            
            if status == 'idle':
                # Check one more time
                time.sleep(2)
                continue
            
            time.sleep(3)
        
        ws.close()
        print("   ⏱️  Timeout attesa generazione", file=sys.stderr)
        return []
        
    except Exception as e:
        print(f"   ❌ Extract error: {str(e)[:60]}", file=sys.stderr)
        return []


def download_image(image_data, output_path):
    """Download image from data URL or direct URL."""
    try:
        if image_data.startswith("data:image"):
            # Base64 data URL
            _, b64data = image_data.split(",", 1)
            img_bytes = base64.b64decode(b64data)
        elif image_data.startswith("http"):
            # Direct URL
            req = urllib.request.Request(image_data)
            with urllib.request.urlopen(req, timeout=30) as resp:
                img_bytes = resp.read()
        else:
            return False
        
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(img_bytes)
        
        size_kb = len(img_bytes) / 1024
        print(f"   💾 Salvata: {output_path} ({size_kb:.0f} KB)")
        return True
        
    except Exception as e:
        print(f"   ❌ Download error: {str(e)[:60]}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description="Generate thumbnail via ChatGPT browser")
    parser.add_argument("--title", required=True)
    parser.add_argument("--subtitle", default="")
    parser.add_argument("--output", default=os.path.join(OUTPUT_DIR, "thumbnail.png"))
    parser.add_argument("--max-wait", type=int, default=180, help="Max seconds to wait")
    args = parser.parse_args()
    
    print(f"🌐 ChatGPT browser: {args.title[:40]}...")
    
    os.makedirs(THUMBNAILS_DIR, exist_ok=True)
    
    prompt = PROMPT_TEMPLATE.format(title=args.title, subtitle=args.subtitle)
    
    # Step 1: Navigate to ChatGPT
    print("   Navigazione a ChatGPT...")
    tab_id = navigate_browser("https://chatgpt.com")
    if not tab_id:
        print("   ❌ Impossibile navigare a ChatGPT", file=sys.stderr)
        sys.exit(1)
    
    time.sleep(3)  # Wait for page load
    
    # Step 2: Type prompt and submit
    print("   Invio prompt...")
    if not inject_and_type_prompt(tab_id, prompt):
        print("   ⚠️  Invio prompt fallito, provo comunque...")
    
    # Step 3: Wait for images
    print(f"   Attesa generazione (max {args.max_wait}s)...")
    images = wait_and_extract_images(tab_id, args.max_wait)
    
    if not images:
        print("   ❌ Nessuna immagine generata", file=sys.stderr)
        sys.exit(1)
    
    # Step 4: Download first image (usually the best)
    output_path = args.output
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    
    if download_image(images[0], output_path):
        # Also save to thumbnails folder with timestamp
        timestamp = int(time.time())
        cache_path = os.path.join(THUMBNAILS_DIR, f"chatgpt_{timestamp}.png")
        download_image(images[0], cache_path)
        
        print(f"\n✅ Thumbnail salvata: {output_path}")
        sys.exit(0)
    else:
        print("   ❌ Download fallito", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n   Interrotto")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Errore: {str(e)[:80]}", file=sys.stderr)
        sys.exit(1)
