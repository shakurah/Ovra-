const boeSearchService = require('./src/services/boeSearchService');

async function testBOESearch() {
  console.log('🔍 Testing BOE Search Service...\n');
  
  // Test search terms
  const testQueries = [
    'Plurinacional Sumar y Mixto del',
    'cultural freelancer',
    'freelancer cultural'
  ];

  for (const query of testQueries) {
    console.log(`\n📝 Testing search: "${query}"`);
    console.log('=' + '='.repeat(50));
    
    try {
      // Test single search
      console.log('🔍 Performing single search...');
      const singleResult = await boeSearchService.performSearch(query);
      console.log(`✅ Single search completed. Found ${singleResult.length} results`);
      
      if (singleResult.length > 0) {
        console.log('📄 First result preview:');
        console.log(singleResult[0].text.substring(0, 200) + '...');
      }
      
      // Test multiple searches
      console.log('\n🔍 Performing multiple searches...');
      const multipleResults = await boeSearchService.performMultipleSearches(query);
      console.log(`✅ Multiple searches completed. Found ${multipleResults.length} total results`);
      
      // Show formatted results
      const formattedResults = boeSearchService.formatResultsForAI(multipleResults);
      console.log('\n📋 Formatted results preview:');
      console.log(formattedResults.substring(0, 300) + '...');
      
    } catch (error) {
      console.error(`❌ Error testing "${query}":`, error.message);
      console.error('Stack:', error.stack);
    }
    
    console.log('\n' + '-'.repeat(60));
  }
}

// Test HTML parsing separately
async function testHTMLParsing() {
  console.log('\n🔬 Testing HTML Parsing...\n');
  
  const testHTML = `
    <html>
      <body>
        <div id="listadoResult">
          <div class="resultado">
            <h3>Result 1</h3>
            <p>This is the first result content.</p>
          </div>
          <div class="resultado">
            <h3>Result 2</h3>
            <p>This is the second result content.</p>
          </div>
        </div>
      </body>
    </html>
  `;
  
  try {
    const results = boeSearchService.parseSearchResults(testHTML);
    console.log(`✅ HTML parsing test completed. Found ${results.length} results`);
    console.log('📄 Parsed results:');
    results.forEach((result, index) => {
      console.log(`${index + 1}. ${result.text.substring(0, 100)}...`);
    });
  } catch (error) {
    console.error('❌ HTML parsing error:', error.message);
  }
}

// Test search variations
function testSearchVariations() {
  console.log('\n🔀 Testing Search Variations...\n');
  
  const testQueries = [
    'How should I invoice as a cultural freelancer?',
    'tax rates 2025',
    'Plurinacional Sumar y Mixto del'
  ];
  
  testQueries.forEach(query => {
    console.log(`Query: "${query}"`);
    const variations = boeSearchService.generateSearchVariations(query);
    console.log('Variations:', variations);
    console.log('---');
  });
}

// Run all tests
async function runAllTests() {
  console.log('🚀 Starting BOE Scraper Tests...');
  console.log('=' + '='.repeat(60));
  
  try {
    // Test search variations first (no network calls)
    testSearchVariations();
    
    // Test HTML parsing (no network calls)
    await testHTMLParsing();
    
    // Test actual BOE searches (network calls)
    await testBOESearch();
    
    console.log('\n✅ All tests completed!');
  } catch (error) {
    console.error('\n❌ Test suite failed:', error.message);
  }
}

// Run the tests
runAllTests().catch(console.error);