const axios = require('axios');
const cheerio = require('cheerio');

async function testDirectBOEAccess() {
  console.log('🔍 Testing Direct BOE Access...\n');
  
  // First, let's get the search form page to understand its structure
  console.log('📡 Getting search form page...');
  
  try {
    const formResponse = await axios.get('https://www.boe.es/buscar/boe.php', {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8'
      },
      timeout: 30000
    });
    
    console.log('✅ Form page received');
    console.log('Status:', formResponse.status);
    console.log('Content Length:', formResponse.data.length);
    
    const $ = cheerio.load(formResponse.data);
    
    // Analyze the form structure
    console.log('\n🔍 Analyzing form structure...');
    const form = $('form');
    
    if (form.length > 0) {
      console.log(`Found ${form.length} form(s)`);
      
      form.each((index, element) => {
        const action = $(element).attr('action') || 'no action';
        const method = $(element).attr('method') || 'GET';
        console.log(`Form ${index + 1}: action="${action}", method="${method}"`);
        
        // Get all input fields
        const inputs = $(element).find('input, select, textarea');
        console.log(`  Found ${inputs.length} input fields:`);
        
        inputs.each((i, input) => {
          const name = $(input).attr('name');
          const type = $(input).attr('type') || 'text';
          const value = $(input).attr('value') || '';
          const id = $(input).attr('id') || 'no-id';
          
          if (name) {
            console.log(`    ${name}: type="${type}", value="${value}", id="${id}"`);
          }
        });
      });
    }
    
    // Try to find any existing search results or examples
    console.log('\n🔍 Looking for any existing results or examples...');
    
    // Check if there are any links to actual BOE documents
    const boeLinks = $('a[href*="BOE-A-"]');
    if (boeLinks.length > 0) {
      console.log(`Found ${boeLinks.length} BOE document links`);
      boeLinks.slice(0, 3).each((index, link) => {
        const href = $(link).attr('href');
        const text = $(link).text().trim();
        console.log(`  ${index + 1}. ${href}: ${text}`);
      });
    }
    
    // Let's try to access a known BOE URL pattern to see the actual result format
    console.log('\n📡 Trying to access latest BOE documents...');
    
    // Try to get today's BOE
    const today = new Date();
    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const day = String(today.getDate()).padStart(2, '0');
    
    const boeUrl = `https://www.boe.es/diario_boe/txt.php?id=BOE-S-${year}-${month}${day}`;
    console.log(`Trying: ${boeUrl}`);
    
    try {
      const boeResponse = await axios.get(boeUrl, {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36'
        },
        timeout: 15000
      });
      
      console.log('✅ BOE document accessed successfully');
      console.log('Status:', boeResponse.status);
      console.log('Content preview:', boeResponse.data.substring(0, 200) + '...');
      
    } catch (boeError) {
      console.log('❌ Could not access BOE document:', boeError.message);
    }
    
  } catch (error) {
    console.error('❌ Error accessing BOE:', error.message);
  }
}

testDirectBOEAccess().catch(console.error);