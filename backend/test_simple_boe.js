const axios = require('axios');
const cheerio = require('cheerio');

async function testSimpleBOESearch() {
  console.log('🔍 Testing Simple BOE Search...\n');
  
  // Try a GET request first to see if search works with URL parameters
  const getUrl = 'https://www.boe.es/buscar/boe.php';
  const params = {
    'campo[0]': 'DOC',
    'dato[0]': 'impuestos',
    'accion': 'Buscar'
  };
  
  try {
    console.log('📡 Trying GET request with simple parameters...');
    const response = await axios.get(getUrl, { 
      params: params,
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36'
      },
      timeout: 30000
    });
    
    console.log('✅ GET Response received');
    console.log('Status:', response.status);
    console.log('Content Length:', response.data.length);
    
    const $ = cheerio.load(response.data);
    
    // Check for results
    const listadoResult = $('.listadoResult');
    if (listadoResult.length > 0) {
      console.log('✅ Found listadoResult element!');
      const results = listadoResult.find('li.resultado-busqueda');
      console.log(`Found ${results.length} search results`);
      
      results.each((index, element) => {
        const title = $(element).find('h3').text().trim();
        const subtitle = $(element).find('h4').text().trim();
        console.log(`${index + 1}. ${title} - ${subtitle}`);
      });
    } else {
      console.log('❌ No listadoResult found in GET response');
      console.log('Title:', $('title').text());
      
      // Check if it's the form page
      const form = $('form');
      if (form.length > 0) {
        console.log('⚠️  Got form page instead of results');
      }
    }
    
  } catch (error) {
    console.error('❌ GET request failed:', error.message);
  }
  
  // Try POST with minimal data
  console.log('\n📡 Trying POST request with minimal data...');
  
  try {
    const postData = {
      'campo[0]': 'DOC',
      'dato[0]': 'impuestos',
      'accion': 'Buscar'
    };
    
    const response = await axios.post('https://www.boe.es/buscar/boe.php', postData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
        'Referer': 'https://www.boe.es/buscar/boe.php',
        'Origin': 'https://www.boe.es'
      },
      timeout: 30000
    });
    
    console.log('✅ POST Response received');
    console.log('Status:', response.status);
    console.log('Content Length:', response.data.length);
    
    const $ = cheerio.load(response.data);
    
    // Check for results
    const listadoResult = $('.listadoResult');
    if (listadoResult.length > 0) {
      console.log('✅ Found listadoResult element!');
      const results = listadoResult.find('li.resultado-busqueda');
      console.log(`Found ${results.length} search results`);
      
      results.each((index, element) => {
        const title = $(element).find('h3').text().trim();
        const subtitle = $(element).find('h4').text().trim();
        console.log(`${index + 1}. ${title} - ${subtitle}`);
      });
    } else {
      console.log('❌ No listadoResult found in POST response');
      console.log('Title:', $('title').text());
      
      // Check if it's the form page
      const form = $('form');
      if (form.length > 0) {
        console.log('⚠️  Got form page instead of results');
      }
    }
    
  } catch (error) {
    console.error('❌ POST request failed:', error.message);
  }
}

testSimpleBOESearch().catch(console.error);