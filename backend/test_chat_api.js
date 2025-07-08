#!/usr/bin/env node

const axios = require('axios');

const BASE_URL = 'http://localhost:8000';

async function testChatAPI() {
  console.log('Testing Chat API...\n');
  
  // Test 1: Login to get token
  console.log('1. Testing login...');
  try {
    const loginResponse = await axios.post(`${BASE_URL}/api/auth/login`, {
      email: 'test@example.com',
      password: 'password123'
    });
    
    console.log('✓ Login successful');
    const token = loginResponse.data.token;
    console.log('Token:', token.substring(0, 20) + '...\n');
    
    // Test 2: Create chat session
    console.log('2. Testing chat session creation...');
    const sessionResponse = await axios.post(`${BASE_URL}/api/chat/sessions`, {
      title: 'Test Chat Session'
    }, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    console.log('✓ Session created successfully');
    const sessionId = sessionResponse.data.session.id;
    console.log('Session ID:', sessionId);
    console.log('Session data:', sessionResponse.data.session, '\n');
    
    // Test 3: Send message
    console.log('3. Testing message sending...');
    const messageResponse = await axios.post(`${BASE_URL}/api/chat/sessions/${sessionId}/messages`, {
      message: '¿Cómo debo facturar como freelancer cultural?'
    }, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    console.log('✓ Message sent successfully');
    console.log('Response:', messageResponse.data.response, '\n');
    
    // Test 4: Get sessions list
    console.log('4. Testing sessions list...');
    const sessionsResponse = await axios.get(`${BASE_URL}/api/chat/sessions`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    console.log('✓ Sessions retrieved successfully');
    console.log('Sessions count:', sessionsResponse.data.sessions.length);
    console.log('Sessions:', sessionsResponse.data.sessions, '\n');
    
    // Test 5: Get session details
    console.log('5. Testing session details...');
    const sessionDetailsResponse = await axios.get(`${BASE_URL}/api/chat/sessions/${sessionId}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    console.log('✓ Session details retrieved successfully');
    console.log('Session:', sessionDetailsResponse.data.session);
    console.log('Messages count:', sessionDetailsResponse.data.messages.length);
    console.log('Messages:', sessionDetailsResponse.data.messages, '\n');
    
    console.log('🎉 All tests passed!');
    
  } catch (error) {
    console.error('❌ Test failed:', error.response?.data || error.message);
  }
}

testChatAPI();