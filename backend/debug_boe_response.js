const axios = require('axios');
const cheerio = require('cheerio');
const fs = require('fs');

async function debugBOEResponse() {
  console.log('🔍 Debugging BOE Response Structure...\n');
  
  const baseUrl = 'https://www.boe.es/buscar/boe.php';
  const headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'en-US,en;q=0.9,co;q=0.8',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'Pragma': 'no-cache',
    'Referer': 'https://www.boe.es/buscar/boe.php?lang=es',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'Cookie': 'BOElang=es'
  };
  
  const searchData = {
    'campo[0]': 'ORIS',
    'dato[0][1]': '1',
    'dato[0][2]': '2',
    'dato[0][3]': '3',
    'dato[0][4]': '4',
    'dato[0][5]': '5',
    'dato[0][T]': 'T',
    'operador[0]': 'and',
    'campo[1]': 'TITULOS',
    'dato[1]': '',
    'operador[1]': 'and',
    'campo[2]': 'DEM',
    'dato[2]': '',
    'operador[2]': 'and',
    'campo[3]': 'DOC',
    'dato[3]': 'Plurinacional Sumar y Mixto del',
    'operador[3]': 'and',
    'campo[4]': 'NBOS',
    'dato[4]': '',
    'operador[4]': 'and',
    'campo[5]': 'NOF',
    'dato[5]': '',
    'operador[5]': 'and',
    'operador[6]': 'and',
    'campo[6]': 'FPU',
    'dato[6][0]': '',
    'dato[6][1]': '',
    'page_hits': '50',
    'sort_field[0]': 'FPU',
    'sort_order[0]': 'desc',
    'sort_field[1]': 'ORI',
    'sort_order[1]': 'asc',
    'sort_field[2]': 'REF',
    'sort_order[2]': 'asc',
    'accion': 'Buscar'
  };
  
  try {
    console.log('📡 Making request to BOE...');
    const response = await axios.post(baseUrl, searchData, {
      headers: headers,
      timeout: 30000
    });
    
    console.log('✅ Response received');
    console.log('Status:', response.status);
    console.log('Content-Type:', response.headers['content-type']);
    console.log('Content Length:', response.data.length);
    
    // Save full HTML to file for inspection
    fs.writeFileSync('boe_response.html', response.data);
    console.log('💾 Full HTML saved to boe_response.html');
    
    // Parse HTML and look for various result containers
    const $ = cheerio.load(response.data);
    
    console.log('\n🔍 Analyzing HTML structure...');
    
    // Check for various possible result containers
    const possibleSelectors = [
      '#listadoResult',
      '#listado',
      '.listado',
      '.resultado',
      '.resultados',
      '.search-results',
      '.boe-result',
      '[class*="result"]',
      '[id*="result"]',
      '[class*="listado"]',
      '[id*="listado"]'
    ];
    
    possibleSelectors.forEach(selector => {
      const elements = $(selector);
      if (elements.length > 0) {
        console.log(`✅ Found ${elements.length} elements with selector: ${selector}`);
        elements.each((index, element) => {
          const text = $(element).text().trim();
          console.log(`  Element ${index + 1}: ${text.substring(0, 100)}...`);
        });
      } else {
        console.log(`❌ No elements found with selector: ${selector}`);
      }
    });
    
    // Look for any div with substantial text content
    console.log('\n🔍 Looking for divs with substantial content...');
    const divs = $('div');
    let foundContent = false;
    
    divs.each((index, element) => {
      const text = $(element).text().trim();
      if (text.length > 100) {
        const id = $(element).attr('id') || 'no-id';
        const className = $(element).attr('class') || 'no-class';
        console.log(`📄 Div with id="${id}" class="${className}": ${text.substring(0, 200)}...`);
        foundContent = true;
      }
    });
    
    if (!foundContent) {
      console.log('❌ No divs with substantial content found');
    }
    
    // Check for form elements or messages
    console.log('\n🔍 Checking for forms and messages...');
    const forms = $('form');
    console.log(`Found ${forms.length} forms`);
    
    const messages = $('.mensaje, .message, .error, .warning, .info');
    if (messages.length > 0) {
      console.log('📝 Messages found:');
      messages.each((index, element) => {
        console.log(`  ${$(element).text().trim()}`);
      });
    }
    
    // Check if we're getting a search form instead of results
    const searchForm = $('form[action*="boe.php"]');
    if (searchForm.length > 0) {
      console.log('⚠️  It looks like we got the search form page, not results');
    }
    
    console.log('\n📊 Summary:');
    console.log(`- Total HTML length: ${response.data.length}`);
    console.log(`- Total divs: ${$('div').length}`);
    console.log(`- Total forms: ${$('form').length}`);
    console.log(`- Title: ${$('title').text()}`);
    
  } catch (error) {
    console.error('❌ Error:', error.message);
    if (error.response) {
      console.error('Response status:', error.response.status);
      console.error('Response headers:', error.response.headers);
    }
  }
}

// Run the debug
debugBOEResponse().catch(console.error);