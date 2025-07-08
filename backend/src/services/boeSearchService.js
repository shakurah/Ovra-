const axios = require('axios');
const cheerio = require('cheerio');

class BOESearchService {
  constructor() {
    this.baseUrl = 'https://www.boe.es/buscar/boe.php';
    this.headers = {
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
  }

  createSearchData(searchTerm) {
    return {
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
      'dato[3]': searchTerm,
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
  }

  async performSearch(searchTerm) {
    try {
      // Convert data to URL-encoded format like jQuery does
      const data = this.createSearchData(searchTerm);
      const urlEncodedData = new URLSearchParams(data).toString();
      
      const response = await axios.post(this.baseUrl, urlEncodedData, {
        headers: {
          ...this.headers,
          'Content-Type': 'application/x-www-form-urlencoded'
        },
        timeout: 30000
      });

      return this.parseSearchResults(response.data);
    } catch (error) {
      console.error(`Error performing BOE search for "${searchTerm}":`, error.message);
      throw error;
    }
  }

  parseSearchResults(html) {
    const $ = cheerio.load(html);
    const results = [];

    // Find the listadoResult element (class, not ID)
    const listadoResult = $('.listadoResult');
    
    if (listadoResult.length === 0) {
      console.log('No listadoResult element found');
      return results;
    }

    console.log(`Found ${listadoResult.length} listadoResult elements`);

    // Extract structured data from each search result
    listadoResult.find('li.resultado-busqueda').each((_, element) => {
      const $element = $(element);
      
      // Extract structured information
      const title = $element.find('h3').text().trim();
      const subtitle = $element.find('h4').text().trim();
      const description = $element.find('p').text().trim();
      const link = $element.find('a.resultado-busqueda-link-defecto').attr('href');
      const reference = $element.find('a').attr('title');
      
      // Combine all text content
      const fullText = `${title}\n${subtitle}\n${description}`.trim();
      
      if (fullText && fullText.length > 20) {
        results.push({
          text: fullText,
          html: $element.html(),
          structured: {
            title: title,
            subtitle: subtitle,
            description: description,
            link: link,
            reference: reference
          }
        });
      }
    });

    // If no structured results found, try to get any text content from the element
    if (results.length === 0) {
      const textContent = listadoResult.text().trim();
      if (textContent) {
        results.push({
          text: textContent,
          html: listadoResult.html()
        });
      }
    }

    console.log(`Parsed ${results.length} results from BOE search`);
    return results;
  }

  generateSearchVariations(userQuery) {
    // Generate different search variations based on user query
    const variations = [];
    
    // Original query
    variations.push(userQuery);
    
    // Split into words and create variations
    const words = userQuery.split(/\s+/).filter(word => word.length > 2);
    
    if (words.length > 1) {
      // First few words
      variations.push(words.slice(0, Math.min(3, words.length)).join(' '));
      
      // Last few words
      if (words.length > 3) {
        variations.push(words.slice(-3).join(' '));
      }
    }
    
    // Ensure we have at least 3 variations
    while (variations.length < 3) {
      variations.push(userQuery);
    }
    
    return variations.slice(0, 3);
  }

  async performMultipleSearches(userQuery, enhancedTerms = null) {
    // Use enhanced terms if provided, otherwise generate variations
    const searchTerms = enhancedTerms && enhancedTerms.length > 0 
      ? enhancedTerms 
      : this.generateSearchVariations(userQuery);
    
    console.log(`Performing BOE searches with terms:`, searchTerms);
    
    try {
      // Perform all searches simultaneously
      const searchPromises = searchTerms.map(term => 
        this.performSearch(term).catch(error => {
          console.error(`Search failed for term "${term}":`, error.message);
          return []; // Return empty array on error
        })
      );

      const results = await Promise.all(searchPromises);
      
      // Combine and deduplicate results
      const combinedResults = [];
      const seenTexts = new Set();
      
      results.forEach((searchResult, index) => {
        searchResult.forEach(result => {
          if (!seenTexts.has(result.text)) {
            seenTexts.add(result.text);
            combinedResults.push({
              ...result,
              searchTerm: searchTerms[index],
              originalQuery: userQuery
            });
          }
        });
      });

      console.log(`Combined ${combinedResults.length} unique results from ${searchTerms.length} search terms`);
      return combinedResults;
    } catch (error) {
      console.error('Error performing multiple BOE searches:', error);
      throw error;
    }
  }

  formatResultsForAI(results) {
    if (!results || results.length === 0) {
      return 'No results found in BOE search.';
    }

    let formattedResults = `BOE Search Results (${results.length} results found):\n\n`;
    
    results.forEach((result, index) => {
      formattedResults += `Result ${index + 1} (Search term: "${result.searchTerm}"):\n`;
      if (result.structured) {
        formattedResults += `Title: ${result.structured.title}\n`;
        formattedResults += `Subtitle: ${result.structured.subtitle}\n`;
        formattedResults += `Description: ${result.structured.description}\n`;
        if (result.structured.link) {
          formattedResults += `Link: ${result.structured.link}\n`;
        }
      } else {
        formattedResults += `${result.text}\n`;
      }
      formattedResults += '---\n\n';
    });

    return formattedResults;
  }

  async search(userQuery) {
    try {
      console.log(`BOE Search requested for: "${userQuery}"`);
      
      // Perform multiple searches with variations
      const results = await this.performMultipleSearches(userQuery);
      
      // Format results for compatibility with widget service
      const formattedResults = results.map(result => ({
        title: result.structured?.title || result.text.split('\n')[0] || 'BOE Document',
        content: result.structured?.description || result.text,
        source: 'BOE',
        url: result.structured?.link || '',
        metadata: {
          subtitle: result.structured?.subtitle || '',
          searchTerm: result.searchTerm,
          reference: result.structured?.reference || ''
        }
      }));

      console.log(`BOE Search completed. Found ${formattedResults.length} results.`);
      return formattedResults;
    } catch (error) {
      console.error('Error in BOE search:', error);
      return [];
    }
  }
}

module.exports = new BOESearchService();