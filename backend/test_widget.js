const axios = require('axios');

const baseURL = 'http://localhost:8000';

async function testWidget() {
  try {
    console.log('Testing widget functionality...\n');

    // Test 1: Register a new email
    console.log('1. Testing email registration...');
    const registerResponse = await axios.post(`${baseURL}/widget/register/`, {
      email: 'test@example.com',
      privacy_accepted: true,
      terms_accepted: true,
      source_website: 'http://localhost:3000'
    });
    
    console.log('Register response:', registerResponse.data);
    
    // Test 2: Send a chat message
    console.log('\n2. Testing chat message...');
    const chatResponse = await axios.post(`${baseURL}/widget/chat/`, {
      email: 'test@example.com',
      question: '¿Qué es el IVA?',
      source_website: 'http://localhost:3000'
    });
    
    console.log('Chat response:', chatResponse.data);
    
    // Test 3: Send another message with session ID
    console.log('\n3. Testing second message with session...');
    const sessionId = chatResponse.data.data.session_id;
    const secondChatResponse = await axios.post(`${baseURL}/widget/chat/`, {
      email: 'test@example.com',
      question: '¿Cuál es el tipo general del IVA?',
      session_id: sessionId,
      source_website: 'http://localhost:3000'
    });
    
    console.log('Second chat response:', secondChatResponse.data);
    
    // Test 4: Get session messages
    console.log('\n4. Testing get session messages...');
    const messagesResponse = await axios.get(`${baseURL}/widget/messages/${sessionId}`);
    console.log('Messages response:', messagesResponse.data);
    
    // Test 5: Get user sessions
    console.log('\n5. Testing get user sessions...');
    const sessionsResponse = await axios.get(`${baseURL}/widget/sessions/?email=test@example.com`);
    console.log('Sessions response:', sessionsResponse.data);
    
    // Test 6: Test existing email (should update)
    console.log('\n6. Testing existing email registration...');
    const existingEmailResponse = await axios.post(`${baseURL}/widget/register/`, {
      email: 'test@example.com',
      privacy_accepted: true,
      terms_accepted: true,
      source_website: 'http://localhost:3000'
    });
    
    console.log('Existing email response:', existingEmailResponse.data);
    
    console.log('\n✅ All tests completed successfully!');
    
  } catch (error) {
    console.error('❌ Test failed:', error.response?.data || error.message);
  }
}

testWidget();