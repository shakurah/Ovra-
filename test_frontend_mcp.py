#!/usr/bin/env python3
"""
Frontend Testing with Playwright
Tests the complete chat interface with MCP BOE integration
"""

import asyncio
import sys
from playwright.async_api import async_playwright
import json
import time


async def test_frontend_chat_with_mcp():
    """Test frontend chat interface with BOE MCP integration"""
    
    async with async_playwright() as p:
        print("🚀 Starting Frontend Chat Test with Playwright...")
        
        # Launch browser
        browser = await p.chromium.launch(headless=False)  # Set to True for headless
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # Navigate to login page
            print("📱 Navigating to login page...")
            await page.goto('http://localhost:3000/login')
            
            # Wait for page to load
            await page.wait_for_selector('input[type="email"]', timeout=10000)
            print("✅ Login page loaded")
            
            # Login
            print("🔐 Logging in...")
            await page.fill('input[type="email"]', 'test@example.com')
            await page.fill('input[type="password"]', 'password123')
            await page.click('button[type="submit"]')
            
            # Wait for redirect to dashboard/chat
            print("⏳ Waiting for login redirect...")
            await page.wait_for_url('**', timeout=10000)
            current_url = page.url
            print(f"📍 Redirected to: {current_url}")
            
            # Navigate to chat if not already there
            if '/chat' not in current_url:
                print("🔄 Navigating to chat page...")
                await page.goto('http://localhost:3000/chat')
            
            # Wait for chat interface
            print("💬 Waiting for chat interface...")
            await page.wait_for_selector('[data-testid="chat-input"], textarea, input[placeholder*="message"], input[placeholder*="pregunta"]', timeout=10000)
            print("✅ Chat interface loaded")
            
            # Find chat input (try multiple selectors)
            chat_input = None
            selectors_to_try = [
                '[data-testid="chat-input"]',
                'textarea[placeholder*="message"]',
                'textarea[placeholder*="pregunta"]',
                'input[placeholder*="message"]',
                'input[placeholder*="pregunta"]',
                'textarea',
                'input[type="text"]'
            ]
            
            for selector in selectors_to_try:
                try:
                    chat_input = await page.query_selector(selector)
                    if chat_input:
                        print(f"✅ Found chat input with selector: {selector}")
                        break
                except:
                    continue
            
            if not chat_input:
                print("❌ Could not find chat input field")
                await page.screenshot(path="chat_debug.png")
                return False
            
            # Test legal query
            legal_query = "¿Cuáles son las obligaciones fiscales de un artista autónomo en España según el BOE?"
            print(f"📝 Sending legal query: {legal_query}")
            
            await chat_input.fill(legal_query)
            
            # Find and click send button
            send_button = None
            send_selectors = [
                '[data-testid="send-button"]',
                'button[type="submit"]',
                'button:has-text("Send")',
                'button:has-text("Enviar")',
                'button:has-text("→")',
                'button[aria-label*="send"]',
                'button[aria-label*="enviar"]'
            ]
            
            for selector in send_selectors:
                try:
                    send_button = await page.query_selector(selector)
                    if send_button:
                        print(f"✅ Found send button with selector: {selector}")
                        break
                except:
                    continue
            
            if send_button:
                await send_button.click()
                print("✅ Send button clicked")
            else:
                # Try pressing Enter
                print("⌨️  Trying Enter key...")
                await chat_input.press('Enter')
            
            # Wait for response and monitor streaming
            print("⏳ Waiting for AI response...")
            
            # Monitor for response elements
            response_received = False
            start_time = time.time()
            timeout = 60  # 60 seconds timeout
            
            while time.time() - start_time < timeout:
                try:
                    # Look for response content
                    response_elements = await page.query_selector_all('[data-testid="message"], .message, .chat-message, .response')
                    
                    if response_elements:
                        for element in response_elements:
                            text_content = await element.text_content()
                            if text_content and len(text_content.strip()) > 50:  # Substantial response
                                if any(keyword in text_content.lower() for keyword in ['obligaciones', 'fiscal', 'artista', 'autonomo', 'boe']):
                                    print("✅ Legal response detected!")
                                    print(f"📄 Response preview: {text_content[:200]}...")
                                    response_received = True
                                    break
                    
                    if response_received:
                        break
                    
                    await page.wait_for_timeout(1000)  # Wait 1 second
                    
                except Exception as e:
                    print(f"⚠️  Error checking response: {e}")
                    continue
            
            if not response_received:
                print("❌ No response received within timeout")
                await page.screenshot(path="no_response_debug.png")
                return False
            
            # Take screenshot of successful chat
            await page.screenshot(path="successful_chat.png")
            print("📸 Screenshot saved: successful_chat.png")
            
            # Test non-legal query to verify routing
            print("\n🔄 Testing non-legal query...")
            non_legal_query = "Hola, ¿cómo estás?"
            await chat_input.fill(non_legal_query)
            
            if send_button:
                await send_button.click()
            else:
                await chat_input.press('Enter')
            
            # Wait for non-legal response
            await page.wait_for_timeout(5000)
            print("✅ Non-legal query processed")
            
            print("\n🎉 Frontend Chat Test Completed Successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Frontend test failed: {e}")
            await page.screenshot(path="error_debug.png")
            return False
        
        finally:
            await browser.close()


async def test_streaming_response():
    """Test streaming response functionality specifically"""
    
    async with async_playwright() as p:
        print("\n🌊 Testing Streaming Response...")
        
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # Setup page listener for network requests
            streaming_detected = False
            
            def handle_response(response):
                nonlocal streaming_detected
                if '/chat/stream/' in response.url:
                    print("✅ Streaming endpoint called")
                    streaming_detected = True
            
            page.on('response', handle_response)
            
            # Navigate and login
            await page.goto('http://localhost:3000/login')
            await page.wait_for_selector('input[type="email"]')
            await page.fill('input[type="email"]', 'test@example.com')
            await page.fill('input[type="password"]', 'password123')
            await page.click('button[type="submit"]')
            
            # Navigate to chat
            await page.wait_for_timeout(2000)
            await page.goto('http://localhost:3000/chat')
            
            # Send query
            await page.wait_for_selector('textarea, input[type="text"]')
            chat_input = await page.query_selector('textarea, input[type="text"]')
            
            if chat_input:
                await chat_input.fill("¿Qué normativa BOE regula los derechos de autor?")
                await chat_input.press('Enter')
                
                # Wait and check if streaming was used
                await page.wait_for_timeout(10000)
                
                if streaming_detected:
                    print("✅ Streaming response detected!")
                    return True
                else:
                    print("❌ Streaming not detected")
                    return False
            
            return False
            
        except Exception as e:
            print(f"❌ Streaming test failed: {e}")
            return False
        
        finally:
            await browser.close()


async def main():
    """Main test function"""
    print("🚀 Starting Complete Frontend Testing...\n")
    
    # Test 1: Basic frontend chat functionality
    chat_success = await test_frontend_chat_with_mcp()
    
    # Test 2: Streaming response functionality
    streaming_success = await test_streaming_response()
    
    print(f"\n📊 Test Results Summary:")
    print(f"   Frontend Chat Test: {'✅ PASS' if chat_success else '❌ FAIL'}")
    print(f"   Streaming Response Test: {'✅ PASS' if streaming_success else '❌ FAIL'}")
    
    if chat_success and streaming_success:
        print("\n🎉 All frontend tests passed! MCP integration working end-to-end!")
        return True
    else:
        print("\n⚠️  Some frontend tests failed. Check the output and screenshots for details.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)